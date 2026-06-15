@file:OptIn(ExperimentalUuidApi::class)

package db

import org.jetbrains.exposed.v1.core.ReferenceOption
import org.jetbrains.exposed.v1.core.dao.id.java.UUIDTable
import org.jetbrains.exposed.v1.javatime.timestamp
import kotlin.uuid.ExperimentalUuidApi

object UsersTable : UUIDTable("users") {
    val email        = text("email").uniqueIndex()
    val passwordHash = text("password_hash")
}

object ProjectsTable : UUIDTable("projects") {
    val userId      = reference("user_id", UsersTable, onDelete = ReferenceOption.CASCADE)
    val name        = text("name")
    val packageName = text("package_name")

    init {
        uniqueIndex(userId, name)
        uniqueIndex(userId, packageName)
    }
}

object VersionReleasesTable : UUIDTable("version_releases") {
    val projectId   = reference("project_id", ProjectsTable, onDelete = ReferenceOption.CASCADE)
    val versionCode = integer("version_code")
    val versionName = text("version_name")
    val firstSeenAt = timestamp("first_seen_at").nullable()
    val sampleCount = long("sample_count").default(0)

    init {
        uniqueIndex(projectId, versionCode)
    }
}

object RegressionsTable : UUIDTable("regressions") {
    val projectId   = reference("project_id", ProjectsTable, onDelete = ReferenceOption.CASCADE)

    val metricId     = text("metric_id")
    val screenName   = text("screen_name")
    val deviceCohort = text("device_cohort")

    // Version pair
    val baselineVersionCode = integer("baseline_version_code")
    val baselineVersionName = text("baseline_version_name")
    val currentVersionCode  = integer("current_version_code")
    val currentVersionName  = text("current_version_name")

    // Statistics (filled by detector; nullable until then)
    val baselineP95        = double("baseline_p95").nullable()
    val currentP95         = double("current_p95").nullable()
    val degradationPercent = double("degradation_percent").nullable()

    val baselineCiLower = double("baseline_ci_lower").nullable()
    val baselineCiUpper = double("baseline_ci_upper").nullable()
    val currentCiLower  = double("current_ci_lower").nullable()
    val currentCiUpper  = double("current_ci_upper").nullable()

    val sampleCountBaseline = integer("sample_count_baseline").nullable()
    val sampleCountCurrent  = integer("sample_count_current").nullable()

    // Lifecycle
    val status    = text("status").default("open")

    val closedAt  = timestamp("closed_at").nullable()
    val detectedAt = timestamp("detected_at").nullable()

    init {
        uniqueIndex(
            projectId, metricId, screenName, deviceCohort,
            baselineVersionCode, currentVersionCode
        )
    }
}
