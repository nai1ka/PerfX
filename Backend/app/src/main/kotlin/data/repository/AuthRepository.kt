package data.repository

import com.perfx.models.ProjectDto
import com.perfx.models.RegressionDto
import com.perfx.models.PatchRegressionRequest
import com.perfx.models.VersionReleaseDto
import models.UserDto
import java.time.Instant

data class InternalUser(
    val id: String,
    val email: String,
    val passwordHash: String
)

interface AuthRepository {
    // ── Auth ─────────────────────────────────────────────────────────────────
    suspend fun findUserByEmail(email: String): InternalUser?
    suspend fun findUserById(userId: String): InternalUser?
    suspend fun createUser(email: String, passwordHash: String): UserDto

    // ── Projects ─────────────────────────────────────────────────────────────
    suspend fun getProjectsForUser(userId: String): List<ProjectDto>
    suspend fun existsProjectByName(name: String): Boolean
    suspend fun existsProjectByPackageName(packageName: String): Boolean
    suspend fun createProjectForUser(userId: String, name: String, packageName: String): ProjectDto
    suspend fun isProjectOwnedByUser(projectId: String, userId: String): Boolean

    // ── Version releases ─────────────────────────────────────────────────────
    suspend fun getVersionReleasesForProject(projectId: String): List<VersionReleaseDto>
    suspend fun upsertVersionRelease(
        projectId: String,
        versionCode: Int,
        versionName: String,
        firstSeenAt: Instant,
        sampleCount: Long,
    )

    // ── Regressions ──────────────────────────────────────────────────────────
    suspend fun getRegressionsForProject(
        projectId: String,
        status: String? = null,
        limit: Int = 200,
    ): List<RegressionDto>

    suspend fun patchRegression(
        regressionId: String,
        projectId: String,
        request: PatchRegressionRequest,
    ): RegressionDto?
}
