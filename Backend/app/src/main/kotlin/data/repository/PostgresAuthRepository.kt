@file:OptIn(ExperimentalUuidApi::class)

package data.repository

import com.perfx.db.suspendTransaction
import com.perfx.models.ProjectDto
import com.perfx.models.RegressionDto
import db.ProjectsTable
import db.RegressionsTable
import db.UsersTable
import models.UserDto
import org.jetbrains.exposed.v1.core.ResultRow
import org.jetbrains.exposed.v1.core.SortOrder
import org.jetbrains.exposed.v1.core.and
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.eq
import org.jetbrains.exposed.v1.jdbc.deleteWhere
import org.jetbrains.exposed.v1.jdbc.insert
import org.jetbrains.exposed.v1.jdbc.selectAll
import java.util.UUID
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

class PostgresAuthRepository : AuthRepository {

    override suspend fun findUserByEmail(email: String): InternalUser? = suspendTransaction {
        UsersTable
            .selectAll()
            .where { UsersTable.email eq email }
            .limit(1)
            .map(::rowToInternalUser)
            .firstOrNull()
    }

    override suspend fun createUser(email: String, passwordHash: String): UserDto = suspendTransaction {
        val inserted = UsersTable.insert {
            it[UsersTable.email] = email
            it[UsersTable.passwordHash] = passwordHash
        }

        UserDto(
            id = inserted[UsersTable.id].value.toString(),
            email = inserted[UsersTable.email]
        )
    }

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

    override suspend fun createProjectForUser(userId: String, name: String, packageName: String): ProjectDto =
        suspendTransaction {
            val inserted = ProjectsTable.insert {
                it[ProjectsTable.userId] = EntityID(UUID.fromString(userId), UsersTable)
                it[ProjectsTable.name] = name
                it[ProjectsTable.packageName] = packageName
            }

            ProjectDto(
                id = inserted[ProjectsTable.id].value.toString(),
                name = inserted[ProjectsTable.name],
                packageName = inserted[ProjectsTable.packageName],
            )
        }

    private fun rowToInternalUser(row: ResultRow) = InternalUser(
        id = row[UsersTable.id].value.toString(),
        email = row[UsersTable.email],
        passwordHash = row[UsersTable.passwordHash]
    )

    override suspend fun isProjectOwnedByUser(projectId: String, userId: String): Boolean = suspendTransaction {
        ProjectsTable
            .selectAll()
            .where {
                (ProjectsTable.id eq UUID.fromString(projectId)) and
                        (ProjectsTable.userId eq UUID.fromString(userId))
            }
            .limit(1)
            .count() > 0
    }

    override suspend fun getRegressionsForProject(projectId: String, limit: Int): List<RegressionDto> =
        suspendTransaction {
            RegressionsTable
                .innerJoin(ProjectsTable)
                .selectAll()
                .where { RegressionsTable.projectId eq UUID.fromString(projectId) }
                .orderBy(RegressionsTable.detectedAt, SortOrder.DESC)
                .limit(limit)
                .map(::rowToRegressionDto)
        }

    override suspend fun deleteRegression(regressionId: String, projectId: String): Boolean = suspendTransaction {
        RegressionsTable.deleteWhere {
            (id eq UUID.fromString(regressionId)) and
                    (RegressionsTable.projectId eq UUID.fromString(projectId))
        } > 0
    }

    private fun rowToRegressionDto(row: ResultRow) = RegressionDto(
        id = row[RegressionsTable.id].value.toString(),
        projectName = row[ProjectsTable.name],
        metricId = row[RegressionsTable.metricId],
        screenName = row[RegressionsTable.screenName],
        deviceCohort = row[RegressionsTable.deviceCohort],
        baselineP95 = row[RegressionsTable.baselineP95],
        currentP95 = row[RegressionsTable.currentP95],
        degradationPercent = row[RegressionsTable.degradationPercent],
        pValue = row[RegressionsTable.pValue],
        detectedAt = row[RegressionsTable.detectedAt]?.toString(),
    )

    private fun rowToProjectDto(row: ResultRow) = ProjectDto(
        id = row[ProjectsTable.id].value.toString(),
        name = row[ProjectsTable.name],
        packageName = row[ProjectsTable.packageName],
    )
}