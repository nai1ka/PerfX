import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class MetricDto(

    @SerialName("ts")
    val ts: String,

    @SerialName("metricId")
    val metricId: String,

    @SerialName("metricType")
    val metricType: String,

    @SerialName("screenName")
    val screenName: String,

    @SerialName("value")
    val value: Double
)

@Serializable
data class AppInfo(
    @SerialName("project_id")
    val projectId: String,

    @SerialName("package_name")
    val packageName: String,

    @SerialName("app_version")
    val appVersion: String,

    @SerialName("os_version")
    val osVersion: String,

    @SerialName("device_model")
    val deviceModel: String,

    @SerialName("total_ram_gb")
    val totalRamGb: Double,

    @SerialName("cpu_cores")
    val cpuCores: Int,

    @SerialName("screen_refresh_rate")
    val screenRefreshRate: Double,

    @SerialName("is_power_save_mode")
    val isPowerSaveMode: Boolean,

)
// TODO add removal of old metrics

@Serializable
data class IngestBatchRequest(
    @SerialName("app_info")
    val appInfo: AppInfo,

    @SerialName("metrics")
    val metrics: List<MetricDto>
)

@Serializable
data class IngestResponse(
    val accepted: Int,
    val status: String
)