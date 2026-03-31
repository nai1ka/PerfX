package com.ndevelop.sdk.trackers

import com.ndevelop.sdk.models.Metric
import kotlinx.coroutines.flow.Flow

internal abstract class PerformanceCollector {

    var isDebug = false

    abstract fun collect(intervalMs: Long): Flow<Metric>

    abstract fun stop()
}