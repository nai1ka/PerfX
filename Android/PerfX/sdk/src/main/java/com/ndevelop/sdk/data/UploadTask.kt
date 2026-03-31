package com.ndevelop.sdk.data

import android.content.Context
import android.util.Log
import com.ndevelop.sdk.PerfX

internal object UploadTask {

    suspend fun uploadOnce(context: Context): Boolean {
        val db = MetricDatabase.getInstance(context)
        val batch = db.metricDao().getBatch(Constants.DISK_LIMIT)

        if (batch.isEmpty()) {
            Log.d("PerfX", "No metrics to upload")
            return true
        }

        return try {
            val batchApi = BatchApi(
                appInfo = PerfX.appInfo,
                metrics = batch.map { it.mapToApi() }
            )

            val response = NetworkClient.api.uploadBatch(batchApi)

            if (response.isSuccessful) {
                Log.d("PerfX", "Successfully uploaded ${batch.size} metrics to the server")
                db.metricDao().deleteMetrics(batch.map { it.id })
                Log.d("PerfX", "Deleted ${batch.size} metrics from disk")
                true
            } else {
                Log.e("PerfX", "Server error: ${response.code()}")
                false
            }
        } catch (e: Exception) {
            Log.e("PerfX", "Network failure during upload: ${e.message}", e)
            false
        }
    }
}