package com.ndevelop.sdk.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class MetricType {
    @SerialName("sample")
    SAMPLE,

    @SerialName("event")
    EVENT
}