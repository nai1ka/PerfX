package com.ndevelop.sdk.data

import android.content.Context
import android.util.Log
import com.ndevelop.sdk.PerfX
import com.ndevelop.sdk.PerfX.scope
import com.ndevelop.sdk.models.Metric
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentLinkedQueue

internal class MetricsRepository() {
    private val memoryBuffer = ConcurrentLinkedQueue<Metric>()

    @Volatile
    private var memoryBufferSize = 0

    fun observeCollector(flow: Flow<Metric>, db: MetricDatabase, context: Context) {
        scope.launch {
            flow.collect { metric ->
                memoryBuffer.add(metric)
                memoryBufferSize += 1

                if (memoryBufferSize >= Constants.MEMORY_LIMIT) {
                    Log.d(
                        "PerfX",
                        "Number of metrics in memory($memoryBufferSize) exceeds the limit(${Constants.MEMORY_LIMIT}). Flushing..."
                    )
                    flushToDisk(db, context)
                    memoryBufferSize = 0
                    // TODO if disk fails, we dont need to make size 0
                }
            }
        }
    }


    private suspend fun flushToDisk(db: MetricDatabase, context: Context) {
        val snapshot = mutableListOf<Metric>()
        // TODO ???? memory buffer can be added in parallel
        while (memoryBuffer.isNotEmpty()) {
            memoryBuffer.poll()?.let { snapshot.add(it) }
        }

        val currentScreenName = PerfX.currentScreenName()
        db.metricDao().insertAll(snapshot.map { it.mapToDb(screenName = currentScreenName) })
        val numberOfMetricsOnDisk = db.metricDao().getCount()
        Log.d(
            "PerfX",
            "Flushed. Current number of metrics on disk: $numberOfMetricsOnDisk"
        )
        if (numberOfMetricsOnDisk >= Constants.DISK_LIMIT) {
            Log.d(
                "PerfX",
                "Number of metrics on disk($numberOfMetricsOnDisk) exceeds the limit(${Constants.DISK_LIMIT}). Syncing with the server..."
            )
            SyncManager.triggerImmediateSync(context)
        }
    }

}