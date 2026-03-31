@file:OptIn(ExperimentalUuidApi::class)

package db

import org.jetbrains.exposed.v1.core.ReferenceOption
import org.jetbrains.exposed.v1.core.dao.id.java.UUIDTable
import kotlin.uuid.ExperimentalUuidApi

object UsersTable : UUIDTable("users") {

    val email = text("email").uniqueIndex()

    val passwordHash = text("password_hash")
}

object ProjectsTable : UUIDTable("projects") {

    val userId = reference("user_id", UsersTable, onDelete = ReferenceOption.CASCADE)

    val name = text("name").uniqueIndex()

    val packageName = text("package_name").uniqueIndex()
}

object ThresholdsTable : UUIDTable("thresholds") {

    val projectId = reference("project_id", ProjectsTable, onDelete = ReferenceOption.CASCADE)

    val metricId = text("metric_id")

    val screenName = text("screen_name").nullable()

    val thresholdValue = double("threshold_value")
}