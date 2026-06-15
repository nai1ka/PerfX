package com.perfx.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ProjectDto(
    val id: String,
    val name: String,
    @SerialName("package_name") val packageName: String,
)

@Serializable
data class CreateProjectRequest(
    val name: String,
    @SerialName("package_name") val packageName: String,
)

// ── Version releases ──────────────────────────────────────────────────────────

@Serializable
data class VersionReleaseDto(
    val id: String,
    @SerialName("project_id")   val projectId: String,
    @SerialName("version_code") val versionCode: Int,
    @SerialName("version_name") val versionName: String,
    @SerialName("first_seen_at") val firstSeenAt: String?,
    @SerialName("sample_count") val sampleCount: Long,
)

// ── Regressions ───────────────────────────────────────────────────────────────

@Serializable
data class RegressionDto(
    val id: String,
    @SerialName("project_name") val projectName: String,
    @SerialName("metric_id")    val metricId: String,
    @SerialName("screen_name")  val screenName: String,
    @SerialName("device_cohort") val deviceCohort: String,

    @SerialName("baseline_version_code") val baselineVersionCode: Int,
    @SerialName("baseline_version_name") val baselineVersionName: String,
    @SerialName("current_version_code")  val currentVersionCode: Int,
    @SerialName("current_version_name")  val currentVersionName: String,

    @SerialName("baseline_p95")        val baselineP95: Double?,
    @SerialName("current_p95")         val currentP95: Double?,
    @SerialName("degradation_percent") val degradationPercent: Double?,

    @SerialName("baseline_ci_lower") val baselineCiLower: Double?,
    @SerialName("baseline_ci_upper") val baselineCiUpper: Double?,
    @SerialName("current_ci_lower")  val currentCiLower: Double?,
    @SerialName("current_ci_upper")  val currentCiUpper: Double?,

    @SerialName("sample_count_baseline") val sampleCountBaseline: Int?,
    @SerialName("sample_count_current")  val sampleCountCurrent: Int?,

    val status: String,
    @SerialName("closed_at")   val closedAt: String?,
    @SerialName("detected_at") val detectedAt: String?,
)

@Serializable
data class PatchRegressionRequest(
    val status: String? = null,
)

// ── Metrics / plots ───────────────────────────────────────────────────────────

@Serializable
data class ProjectStatusDto(
    @SerialName("total_rows")      val totalRows: Long,
    @SerialName("last_ingested")   val lastIngested: String?,
    @SerialName("unique_metrics")  val uniqueMetrics: Long,
    @SerialName("unique_screens")  val uniqueScreens: Long,
)

@Serializable
data class MetricDimensionDto(
    @SerialName("metric_id")    val metricId: String,
    @SerialName("screen_name")  val screenName: String,
    @SerialName("device_cohort") val deviceCohort: String,
)

@Serializable
data class CustomPlotRequest(
    @SerialName("metric_id")    val metricId: String,
    @SerialName("screen_name")  val screenName: String,
    @SerialName("device_cohort") val deviceCohort: String,
    val aggregation: String,
    @SerialName("minutes_back")   val minutesBack: Int,
    @SerialName("bucket_minutes") val bucketMinutes: Int,
)

@Serializable
data class PlotPointDto(
    val bucket: String,
    @SerialName("metric_value") val metricValue: Double,
)

@Serializable
data class DailyMetricPoint(
    val date: String,
    val p95: Double,
    val count: Long,
)

@Serializable
data class VersionCompareResponse(
    val baseline: List<DailyMetricPoint>,
    val current: List<DailyMetricPoint>,
)
