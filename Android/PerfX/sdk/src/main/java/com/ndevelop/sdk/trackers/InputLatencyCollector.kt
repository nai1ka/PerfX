package com.ndevelop.sdk.trackers

import android.view.Choreographer
import android.view.MotionEvent
import android.view.Window
import com.ndevelop.sdk.models.Metric
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

internal class InputLatencyCollector(private val window: Window) : PerformanceCollector() {

    private var originalCallback: Window.Callback? = null

    override fun collect(intervalMs: Long): Flow<Metric> = callbackFlow {
        originalCallback = window.callback

        window.callback = object : Window.Callback by originalCallback!! {
            override fun dispatchTouchEvent(event: MotionEvent): Boolean {
                if (event.action == MotionEvent.ACTION_DOWN) {
                    val touchTimeMs = event.eventTime
                    Choreographer.getInstance().postFrameCallback { frameTimeNs ->
                        val latencyMs = frameTimeNs / 1_000_000L - touchTimeMs
                        if (latencyMs >= 0) {
                            trySend(
                                Metric.InputLatency(
                                    timestamp = System.currentTimeMillis(),
                                    value = latencyMs.toDouble(),
                                )
                            )
                        }
                    }
                }
                return originalCallback?.dispatchTouchEvent(event) ?: false
            }
        }

        awaitClose { stop() }
    }

    override fun stop() {
        originalCallback?.let { window.callback = it }
        originalCallback = null
    }
}
