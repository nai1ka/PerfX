package com.ndevelop.sdk.models

internal sealed interface Metric {

    val id: String

    // TODO move timestamp to other model
    val timestamp: Long

    val value: Double


    data class FrameTime(
        override val id: String = "frameTime",
        override val timestamp: Long,
        override val value: Double,
    ) : Metric

    data class MemoryUsage(
        override val id: String = "memoryUsage",
        override val timestamp: Long,
        override val value: Double,
    ) : Metric

    data class CpuUsage(
        override val id: String = "cpuUsage",
        override val timestamp: Long,
        override val value: Double,
    ): Metric
}