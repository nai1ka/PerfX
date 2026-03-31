package com.ndevelop.sdk.trackers

import android.os.Handler
import android.os.Looper
import android.view.Choreographer
import com.ndevelop.sdk.models.Metric
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.launch
import kotlin.math.max

internal class FrameTimeCollector : PerformanceCollector() {

    private val mainHandler = Handler(Looper.getMainLooper())

    @Volatile
    private var isRunning = false

    @Volatile
    private var lastFrameTimeNs: Long = 0L

    private var frameCallback: Choreographer.FrameCallback? = null
    private var flushJob: Job? = null

    private var frameCount = 0
    private var totalFrameTimeMs = 0.0
    private var maxFrameTimeMs = 0.0

    override fun collect(intervalMs: Long): Flow<Metric> = callbackFlow {
        isRunning = true
        resetWindow()

        val callback = Choreographer.FrameCallback { frameTimeNs ->
            if (!isRunning) return@FrameCallback

            if (lastFrameTimeNs != 0L) {
                val deltaMs = (frameTimeNs - lastFrameTimeNs) / 1_000_000.0

                if (deltaMs >= 0.0) {
                    frameCount++
                    totalFrameTimeMs += deltaMs
                    maxFrameTimeMs = max(maxFrameTimeMs, deltaMs)
                }
            }

            lastFrameTimeNs = frameTimeNs

            if (isRunning) {
                Choreographer.getInstance().postFrameCallback(frameCallback)
            }
        }

        frameCallback = callback

        mainHandler.post {
            if (isRunning) {
                Choreographer.getInstance().postFrameCallback(callback)
            }
        }

        flushJob = launch {
            while (isRunning) {
                delay(intervalMs)

                val count = frameCount
                val avgFrameTime = if (count > 0) totalFrameTimeMs / count else 0.0
                val timestamp = System.currentTimeMillis()

                if (isDebug) {
                    android.util.Log.d(
                        "FrameTimeCollector",
                        "frames=$count avg=${"%.2f".format(avgFrameTime)}ms max=${"%.2f".format(maxFrameTimeMs)}ms"
                    )
                }

                trySend(
                    Metric.FrameTime(
                        timestamp = timestamp,
                        value = avgFrameTime
                    )
                )

                resetWindow()
            }
        }

        awaitClose { stop() }
    }

    override fun stop() {
        isRunning = false

        flushJob?.cancel()
        flushJob = null

        frameCallback?.let { callback ->
            mainHandler.post {
                runCatching {
                    Choreographer.getInstance().removeFrameCallback(callback)
                }
            }
        }

        frameCallback = null
        lastFrameTimeNs = 0L

        resetWindow()
    }

    private fun resetWindow() {
        frameCount = 0
        totalFrameTimeMs = 0.0
        maxFrameTimeMs = 0.0
    }
}