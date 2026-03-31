package com.ndevelop.sdk.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable


@Serializable
data class MetricApi(
    /**
     * ISO-8601 timestamp in UTC, for example:
     * 2026-03-07T10:15:30.123Z
     */
    @SerialName("ts")
    val ts: String,

    /**
     * Examples:
     * cpu_usage
     * memory_usage
     * frame_time_mean
     * startup_time
     * crash
     * anr
     */
    @SerialName("metricId")
    val metricId: String,

    /**
     * "sample" or "event"
     */
    @SerialName("metricType")
    val metricType: MetricType,

    /**
     * Human-readable screen name.
     * If unknown, send "unknown".
     */
    @SerialName("screenName")
    val screenName: String,

    /**
     * Numeric metric value.
     */
    @SerialName("value")
    val value: Double
)