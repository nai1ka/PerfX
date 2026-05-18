package com.ndevelop.sdk.data

import android.content.Context
import android.util.Log
import com.ndevelop.sdk.PerfX
import com.ndevelop.sdk.PerfX.scope
import com.ndevelop.sdk.models.Metric
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentLinkedQueue

internal class MetricsRepository() {
    private val memoryBuffer = ConcurrentLinkedQueue<Metric>()

    @Volatile
    private var memoryBufferSize = 0

    private var collectionJob: Job? = null

    fun observeCollector(flow: Flow<Metric>, db: MetricDatabase, context: Context) {
        collectionJob?.cancel()
        collectionJob = scope.launch {
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

    fun stopObserving() {
        collectionJob?.cancel()
        collectionJob = null
    }

    fun observeOneShot(flow: Flow<Metric>, db: MetricDatabase, context: Context) {
        scope.launch {
            flow.collect { metric ->
                val dao = db.metricDao()
                val overflow = dao.getCount() + 1 - Constants.DISK_HARD_LIMIT
                if (overflow > 0) dao.deleteOldest(overflow)
                dao.insertAll(listOf(metric).map {
                    it.mapToDb(screenName = PerfX.currentScreenName())
                })
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
        val dao = db.metricDao()
        val countBefore = dao.getCount()
        val overflow = countBefore + snapshot.size - Constants.DISK_HARD_LIMIT
        if (overflow > 0) {
            dao.deleteOldest(overflow)
            Log.d("PerfX", "Hard disk limit reached. Evicted $overflow oldest entries.")
        }

        dao.insertAll(snapshot.map { it.mapToDb(screenName = currentScreenName) })
        val numberOfMetricsOnDisk = dao.getCount()
        Log.d("PerfX", "Flushed. Current number of metrics on disk: $numberOfMetricsOnDisk")
        if (numberOfMetricsOnDisk >= Constants.DISK_SYNC_THRESHOLD) {
            Log.d(
                "PerfX",
                "Sync threshold reached ($numberOfMetricsOnDisk). Triggering upload..."
            )
            SyncManager.triggerImmediateSync(context)
        }
    }

}