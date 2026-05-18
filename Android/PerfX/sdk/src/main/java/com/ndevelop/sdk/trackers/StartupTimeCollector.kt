package com.ndevelop.sdk.trackers

import android.app.Activity
import android.app.Application
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.view.ViewTreeObserver
import com.ndevelop.sdk.models.Metric
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

internal class StartupTimeCollector(
    private val application: Application,
) : PerformanceCollector() {

    override fun collect(intervalMs: Long): Flow<Metric> = flow {
        val processStartTime = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            android.os.Process.getStartUptimeMillis()
        } else {
            SystemClock.uptimeMillis()
        }

        val firstFrameTime = suspendCancellableCoroutine { continuation ->
            val callbacks = object : Application.ActivityLifecycleCallbacks {
                override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {
                    application.unregisterActivityLifecycleCallbacks(this)
                    val decorView = activity.window.decorView
                    decorView.viewTreeObserver.addOnPreDrawListener(
                        object : ViewTreeObserver.OnPreDrawListener {
                            override fun onPreDraw(): Boolean {
                                decorView.viewTreeObserver.removeOnPreDrawListener(this)
                                if (continuation.isActive) {
                                    continuation.resume(SystemClock.uptimeMillis())
                                }
                                return true
                            }
                        }
                    )
                }

                override fun onActivityStarted(activity: Activity) = Unit
                override fun onActivityResumed(activity: Activity) = Unit
                override fun onActivityPaused(activity: Activity) = Unit
                override fun onActivityStopped(activity: Activity) = Unit
                override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) = Unit
                override fun onActivityDestroyed(activity: Activity) = Unit
            }

            continuation.invokeOnCancellation {
                application.unregisterActivityLifecycleCallbacks(callbacks)
            }

            application.registerActivityLifecycleCallbacks(callbacks)
        }

        val startupMs = firstFrameTime - processStartTime
        emit(
            Metric.AppStartup(
                timestamp = System.currentTimeMillis(),
                value = startupMs.toDouble(),
            )
        )
    }

    override fun stop() = Unit
}
