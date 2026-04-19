package data.repository

import com.perfx.models.ProjectDto
import com.perfx.models.RegressionDto
import models.UserDto

data class InternalUser(
    val id: String,
    val email: String,
    val passwordHash: String
)

interface AuthRepository {
    suspend fun findUserByEmail(email: String): InternalUser?
    suspend fun createUser(email: String, passwordHash: String): UserDto
    suspend fun getProjectsForUser(userId: String): List<ProjectDto>
    suspend fun existsProjectByName(name: String): Boolean
    suspend fun existsProjectByPackageName(appId: String): Boolean
    suspend fun createProjectForUser(userId: String, name: String, appId: String): ProjectDto
    suspend fun isProjectOwnedByUser(projectId: String, userId: String): Boolean
    suspend fun getRegressionsForProject(projectId: String, limit: Int = 200): List<RegressionDto>
    suspend fun deleteRegression(regressionId: String, projectId: String): Boolean
}