package com.ndevelop.sdk.trackers

import android.os.Debug
import android.util.Log
import com.ndevelop.sdk.models.Metric
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.isActive

internal class RamCollector : PerformanceCollector() {

    @Volatile
    private var isRunning = false

    override fun collect(intervalMs: Long): Flow<Metric> = flow {
        isRunning = true

        while (currentCoroutineContext().isActive && isRunning) {
            val timestamp = System.currentTimeMillis()

            val memoryInfo = Debug.MemoryInfo()
            Debug.getMemoryInfo(memoryInfo)

            val runtime = Runtime.getRuntime()
            val javaHeapUsedMb =
                (runtime.totalMemory() - runtime.freeMemory()) / (1024.0 * 1024.0)

            val javaHeapTotalMb =
                runtime.totalMemory() / (1024.0 * 1024.0)

            val nativeHeapUsedMb =
                Debug.getNativeHeapAllocatedSize() / (1024.0 * 1024.0)

            val pssMb = memoryInfo.totalPss / 1024.0
            val dalvikPssMb = memoryInfo.dalvikPss / 1024.0
            val nativePssMb = memoryInfo.nativePss / 1024.0
            val otherPssMb = memoryInfo.otherPss / 1024.0

            if (isDebug) {
                Log.d(
                    TAG,
                    "javaUsed=${"%.2f".format(javaHeapUsedMb)}MB, " +
                            "javaTotal=${"%.2f".format(javaHeapTotalMb)}MB, " +
                            "nativeUsed=${"%.2f".format(nativeHeapUsedMb)}MB, " +
                            "pss=${"%.2f".format(pssMb)}MB, " +
                            "dalvikPss=${"%.2f".format(dalvikPssMb)}MB, " +
                            "nativePss=${"%.2f".format(nativePssMb)}MB, " +
                            "otherPss=${"%.2f".format(otherPssMb)}MB"
                )
            }

            emit(
                Metric.MemoryUsage(
                    timestamp = timestamp,
                    value = javaHeapUsedMb
                )
            )

            delay(intervalMs)
        }
    }.flowOn(Dispatchers.Default)

    override fun stop() {
        isRunning = false
    }

    private companion object {
        const val TAG = "RamCollector"
    }
}