package com.perfx.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ProjectDto(
    @SerialName("id")
    val id: String,

    @SerialName("name")
    val name: String,

    @SerialName("package_name")
    val packageName: String,
)

@Serializable
data class CreateProjectRequest(
    @SerialName("name")
    val name: String,

    @SerialName("package_name")
    val packageName: String,
)

@Serializable
data class RegressionDto(
    val id: String,
    @SerialName("project_name") val projectName: String,
    @SerialName("metric_id") val metricId: String,
    @SerialName("screen_name") val screenName: String,
    @SerialName("device_cohort") val deviceCohort: String,
    @SerialName("baseline_p95") val baselineP95: Double?,
    @SerialName("current_p95") val currentP95: Double?,
    @SerialName("degradation_percent") val degradationPercent: Double?,
    @SerialName("p_value") val pValue: Double?,
    @SerialName("detected_at") val detectedAt: String?,
)

@Serializable
data class ProjectStatusDto(
    @SerialName("total_rows") val totalRows: Long,
    @SerialName("last_ingested") val lastIngested: String?,
    @SerialName("unique_metrics") val uniqueMetrics: Long,
    @SerialName("unique_screens") val uniqueScreens: Long,
)

@Serializable
data class MetricDimensionDto(
    @SerialName("metric_id") val metricId: String,
    @SerialName("screen_name") val screenName: String,
    @SerialName("device_cohort") val deviceCohort: String,
)

@Serializable
data class CustomPlotRequest(
    @SerialName("metric_id") val metricId: String,
    @SerialName("screen_name") val screenName: String,
    @SerialName("device_cohort") val deviceCohort: String,
    val aggregation: String,
    @SerialName("minutes_back") val minutesBack: Int,
    @SerialName("bucket_minutes") val bucketMinutes: Int,
)

@Serializable
data class PlotPointDto(
    val bucket: String,
    @SerialName("metric_value") val metricValue: Double,
)