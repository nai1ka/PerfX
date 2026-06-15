@file:OptIn(ExperimentalUuidApi::class)

package data.repository

import com.perfx.db.suspendTransaction
import com.perfx.models.PatchRegressionRequest
import com.perfx.models.ProjectDto
import com.perfx.models.RegressionDto
import com.perfx.models.VersionReleaseDto
import db.ProjectsTable
import db.RegressionsTable
import db.UsersTable
import db.VersionReleasesTable
import models.UserDto
import org.jetbrains.exposed.v1.core.ResultRow
import org.jetbrains.exposed.v1.core.SortOrder
import org.jetbrains.exposed.v1.core.and
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.eq
import org.jetbrains.exposed.v1.jdbc.insert
import org.jetbrains.exposed.v1.jdbc.selectAll
import org.jetbrains.exposed.v1.jdbc.update
import java.time.Instant
import java.util.UUID
import kotlin.uuid.ExperimentalUuidApi

class PostgresAuthRepository : AuthRepository {

    // ── Auth ─────────────────────────────────────────────────────────────────

    override suspend fun findUserByEmail(email: String): InternalUser? = suspendTransaction {
        UsersTable
            .selectAll()
            .where { UsersTable.email eq email }
            .limit(1)
            .map(::rowToInternalUser)
            .firstOrNull()
    }

    override suspend fun findUserById(userId: String): InternalUser? = suspendTransaction {
        UsersTable
            .selectAll()
            .where { UsersTable.id eq UUID.fromString(userId) }
            .limit(1)
            .map(::rowToInternalUser)
            .firstOrNull()
    }

    override suspend fun createUser(email: String, passwordHash: String): UserDto = suspendTransaction {
        val inserted = UsersTable.insert {
            it[UsersTable.email]        = email
            it[UsersTable.passwordHash] = passwordHash
        }
        UserDto(
            id    = inserted[UsersTable.id].value.toString(),
            email = inserted[UsersTable.email],
        )
    }

    // ── Projects ─────────────────────────────────────────────────────────────

    override suspend fun getProjectsForUser(userId: String): List<ProjectDto> = suspendTransaction {
        ProjectsTable
            .selectAll()
            .where { ProjectsTable.userId eq UUID.fromString(userId) }
            .map(::rowToProjectDto)
    }

    override suspend fun existsProjectByName(name: String): Boolean = suspendTransaction {
        ProjectsTable
            .selectAll()
            .where { ProjectsTable.name eq name }
            .limit(1)
            .count() > 0
    }

    override suspend fun existsProjectByPackageName(packageName: String): Boolean = suspendTransaction {
        ProjectsTable
            .selectAll()
            .where { ProjectsTable.packageName eq packageName }
            .limit(1)
            .count() > 0
    }

    override suspend fun createProjectForUser(
        userId: String,
        name: String,
        packageName: String,
    ): ProjectDto = suspendTransaction {
        val inserted = ProjectsTable.insert {
            it[ProjectsTable.userId]      = EntityID(UUID.fromString(userId), UsersTable)
            it[ProjectsTable.name]        = name
            it[ProjectsTable.packageName] = packageName
        }
        ProjectDto(
            id          = inserted[ProjectsTable.id].value.toString(),
            name        = inserted[ProjectsTable.name],
            packageName = inserted[ProjectsTable.packageName],
        )
    }

    override suspend fun isProjectOwnedByUser(projectId: String, userId: String): Boolean = suspendTransaction {
        ProjectsTable
            .selectAll()
            .where {
                (ProjectsTable.id     eq UUID.fromString(projectId)) and
                (ProjectsTable.userId eq UUID.fromString(userId))
            }
            .limit(1)
            .count() > 0
    }

    // ── Version releases ─────────────────────────────────────────────────────

    override suspend fun getVersionReleasesForProject(projectId: String): List<VersionReleaseDto> =
        suspendTransaction {
            VersionReleasesTable
                .selectAll()
                .where { VersionReleasesTable.projectId eq UUID.fromString(projectId) }
                .orderBy(VersionReleasesTable.versionCode, SortOrder.DESC)
                .map(::rowToVersionReleaseDto)
        }

    override suspend fun upsertVersionRelease(
        projectId: String,
        versionCode: Int,
        versionName: String,
        firstSeenAt: Instant,
        sampleCount: Long,
    ) {
        suspendTransaction {
        val projectUuid = UUID.fromString(projectId)

        val existing = VersionReleasesTable
            .selectAll()
            .where {
                (VersionReleasesTable.projectId   eq projectUuid) and
                (VersionReleasesTable.versionCode eq versionCode)
            }
            .firstOrNull()

        if (existing != null) {
            VersionReleasesTable.update({
                (VersionReleasesTable.projectId   eq projectUuid) and
                (VersionReleasesTable.versionCode eq versionCode)
            }) {
                it[VersionReleasesTable.sampleCount] = sampleCount
                it[VersionReleasesTable.versionName] = versionName
            }
        } else {
            VersionReleasesTable.insert {
                it[VersionReleasesTable.projectId]   = EntityID(projectUuid, ProjectsTable)
                it[VersionReleasesTable.versionCode] = versionCode
                it[VersionReleasesTable.versionName] = versionName
                it[VersionReleasesTable.firstSeenAt] = firstSeenAt
                it[VersionReleasesTable.sampleCount] = sampleCount
            }
        }
        }
    }

    // ── Regressions ──────────────────────────────────────────────────────────

    override suspend fun getRegressionsForProject(
        projectId: String,
        status: String?,
        limit: Int,
    ): List<RegressionDto> = suspendTransaction {
        RegressionsTable
            .innerJoin(ProjectsTable)
            .selectAll()
            .where {
                val base = RegressionsTable.projectId eq UUID.fromString(projectId)
                if (status != null) base and (RegressionsTable.status eq status) else base
            }
            .orderBy(RegressionsTable.detectedAt, SortOrder.DESC)
            .limit(limit)
            .map(::rowToRegressionDto)
    }

    override suspend fun patchRegression(
        regressionId: String,
        projectId: String,
        request: PatchRegressionRequest,
    ): RegressionDto? = suspendTransaction {
        val regressionUuid = UUID.fromString(regressionId)
        val projectUuid    = UUID.fromString(projectId)

        val existing = RegressionsTable
            .innerJoin(ProjectsTable)
            .selectAll()
            .where {
                (RegressionsTable.id        eq regressionUuid) and
                (RegressionsTable.projectId eq projectUuid)
            }
            .firstOrNull() ?: return@suspendTransaction null

        val newStatus = request.status ?: existing[RegressionsTable.status]

        val newClosedAt = when {
            newStatus == "closed" && existing[RegressionsTable.closedAt] == null -> Instant.now()
            newStatus == "open" -> null
            else -> existing[RegressionsTable.closedAt]
        }

        RegressionsTable.update({
            (RegressionsTable.id        eq regressionUuid) and
            (RegressionsTable.projectId eq projectUuid)
        }) {
            it[RegressionsTable.status]   = newStatus
            it[RegressionsTable.closedAt] = newClosedAt
        }

        // Re-fetch to return the updated row
        RegressionsTable
            .innerJoin(ProjectsTable)
            .selectAll()
            .where { RegressionsTable.id eq regressionUuid }
            .firstOrNull()
            ?.let(::rowToRegressionDto)
    }

    // ── Mappers ───────────────────────────────────────────────────────────────

    private fun rowToInternalUser(row: ResultRow) = InternalUser(
        id           = row[UsersTable.id].value.toString(),
        email        = row[UsersTable.email],
        passwordHash = row[UsersTable.passwordHash],
    )

    private fun rowToProjectDto(row: ResultRow) = ProjectDto(
        id          = row[ProjectsTable.id].value.toString(),
        name        = row[ProjectsTable.name],
        packageName = row[ProjectsTable.packageName],
    )

    private fun rowToVersionReleaseDto(row: ResultRow) = VersionReleaseDto(
        id          = row[VersionReleasesTable.id].value.toString(),
        projectId   = row[VersionReleasesTable.projectId].value.toString(),
        versionCode = row[VersionReleasesTable.versionCode],
        versionName = row[VersionReleasesTable.versionName],
        firstSeenAt = row[VersionReleasesTable.firstSeenAt]?.toString(),
        sampleCount = row[VersionReleasesTable.sampleCount],
    )

    private fun rowToRegressionDto(row: ResultRow) = RegressionDto(
        id                  = row[RegressionsTable.id].value.toString(),
        projectName         = row[ProjectsTable.name],
        metricId            = row[RegressionsTable.metricId],
        screenName          = row[RegressionsTable.screenName],
        deviceCohort        = row[RegressionsTable.deviceCohort],
        baselineVersionCode = row[RegressionsTable.baselineVersionCode],
        baselineVersionName = row[RegressionsTable.baselineVersionName],
        currentVersionCode  = row[RegressionsTable.currentVersionCode],
        currentVersionName  = row[RegressionsTable.currentVersionName],
        baselineP95         = row[RegressionsTable.baselineP95],
        currentP95          = row[RegressionsTable.currentP95],
        degradationPercent  = row[RegressionsTable.degradationPercent],
        baselineCiLower     = row[RegressionsTable.baselineCiLower],
        baselineCiUpper     = row[RegressionsTable.baselineCiUpper],
        currentCiLower      = row[RegressionsTable.currentCiLower],
        currentCiUpper      = row[RegressionsTable.currentCiUpper],
        sampleCountBaseline = row[RegressionsTable.sampleCountBaseline],
        sampleCountCurrent  = row[RegressionsTable.sampleCountCurrent],
        status     = row[RegressionsTable.status],
        closedAt   = row[RegressionsTable.closedAt]?.toString(),
        detectedAt = row[RegressionsTable.detectedAt]?.toString(),
    )
}
