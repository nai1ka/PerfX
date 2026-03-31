package com.ndevelop.sdk.data


import android.content.Context
import android.util.Log
import com.ndevelop.sdk.PerfX
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

internal object SyncManager {

    private var periodicJob: Job? = null

    /**
     * Upload once immediately.
     */
    fun triggerImmediateSync(context: Context) {
        PerfX.scope.launch {
            UploadTask.uploadOnce(context.applicationContext)
        }
    }

    /**
     * Starts periodic in-process sync.
     * This DOES NOT survive app/process death.
     */
    fun startPeriodicSync(
        context: Context,
        intervalMs: Long = 15 * 60 * 1000L
    ) {
        if (periodicJob != null) return

        val appContext = context.applicationContext

        periodicJob = PerfX.scope.launch {
            Log.d("PerfX", "Starting periodic sync")

            while (isActive) {
                UploadTask.uploadOnce(appContext)
                delay(intervalMs)
            }
        }
    }

    /**
     * Stops periodic sync immediately.
     */
    fun stopPeriodicSync() {
        if (periodicJob == null) return

        Log.d("PerfX", "Stopping periodic sync")
        periodicJob?.cancel()
        periodicJob = null
    }
}