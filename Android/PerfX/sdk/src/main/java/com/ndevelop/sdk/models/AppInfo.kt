package com.ndevelop.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

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
)