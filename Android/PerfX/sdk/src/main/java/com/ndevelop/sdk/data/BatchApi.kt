package com.ndevelop.sdk.data

import com.ndevelop.sdk.models.AppInfo
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable


@Serializable
data class BatchApi(
    @SerialName("app_info")
    val appInfo: AppInfo,

    @SerialName("metrics")
    val metrics: List<MetricApi>
)