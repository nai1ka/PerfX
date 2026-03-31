package com.ndevelop.sdk.trackers

import android.util.Log
import com.ndevelop.sdk.models.Metric
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.isActive
import android.os.Process

internal class CpuCollector : PerformanceCollector() {

    override fun collect(intervalMs: Long): Flow<Metric> = flow {

        var prevCpu = Process.getElapsedCpuTime()
        var prevTime = System.currentTimeMillis()

        while (currentCoroutineContext().isActive) {

            // todo
            delay(intervalMs)

            val nowCpu = Process.getElapsedCpuTime()
            val nowTime = System.currentTimeMillis()

            val cpuDelta = nowCpu - prevCpu
            val timeDelta = nowTime - prevTime

            val cpuUsage = if (timeDelta > 0) {
                (cpuDelta.toDouble() / timeDelta.toDouble()) * 100
            } else {
                0.0
            }

            if (isDebug) {
                Log.d("CpuUsage", "CpuUsage: $cpuUsage")
            }
            emit(
                Metric.CpuUsage(
                    timestamp = nowTime,
                    value = cpuUsage
                )
            )

            prevCpu = nowCpu
            prevTime = nowTime
        }
    }.flowOn(Dispatchers.Default)

    override fun stop() { // TODO
     }
}