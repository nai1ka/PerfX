package com.ndevelop.sdk

import android.app.Activity
import android.app.Application
import android.content.Context
import android.os.Bundle
import androidx.navigation.NavController
import com.ndevelop.sdk.data.AppInfoProvider
import com.ndevelop.sdk.data.MetricDatabase
import com.ndevelop.sdk.data.MetricsRepository
import com.ndevelop.sdk.data.NetworkClient
import com.ndevelop.sdk.data.SyncManager
import com.ndevelop.sdk.models.AppInfo
import com.ndevelop.sdk.trackers.CpuCollector
import com.ndevelop.sdk.trackers.FrameTimeCollector
import com.ndevelop.sdk.trackers.InputLatencyCollector
import com.ndevelop.sdk.trackers.PerformanceCollector
import com.ndevelop.sdk.trackers.RamCollector
import com.ndevelop.sdk.trackers.StartupTimeCollector
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.merge

object PerfX {

    val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private lateinit var db: MetricDatabase
    private val metricsRepository: MetricsRepository = MetricsRepository()

    @Volatile
    private var isRunning = false

    private var currentActivityName: String? = null

    private var resumedCount = 0

    private var collectors: List<PerformanceCollector> = emptyList()
    private var inputLatencyCollector: InputLatencyCollector? = null

    private var activityLifecycleCallbacks: Application.ActivityLifecycleCallbacks? = null

    private var composeScreenTracker: ComposeScreenTracker? = null
    lateinit var appInfo: AppInfo

    fun initialize(
        application: Application,
        projectId: String,
        endpointUrl: String = "https://api.perfx.ru",
    ) {
        if (isRunning) return

        NetworkClient.initialize(endpointUrl)
        appInfo = AppInfoProvider().get(application, projectId)
        db = MetricDatabase.getInstance(application)

        val cpuCollector = CpuCollector().apply { isDebug = false }
        val frameCollector = FrameTimeCollector().apply { isDebug = false }
        val ramCollector = RamCollector().apply { isDebug = false }

        collectors = listOf(cpuCollector, frameCollector, ramCollector)

        // Startup is one-shot — observe independently, not part of pause/resume cycle.
        val startupCollector = StartupTimeCollector(application)
        metricsRepository.observeOneShot(startupCollector.collect(0), db, application)

        registerActivityCallback(application)
        isRunning = true
    }

    private fun startCollectors(activity: Activity) {
        inputLatencyCollector = InputLatencyCollector(activity.window)
        val allMetrics = (collectors.map { it.collect(500) } +
                listOf(inputLatencyCollector!!.collect(0))).merge()
        metricsRepository.observeCollector(flow = allMetrics, db = db, context = activity)
        SyncManager.startPeriodicSync(activity)
    }

    private fun stopCollectors() {
        collectors.forEach { it.stop() }
        inputLatencyCollector?.stop()
        inputLatencyCollector = null
        metricsRepository.stopObserving()
        SyncManager.stopPeriodicSync()
    }

    fun stop(application: Application) {
        if (!isRunning) return

        SyncManager.stopPeriodicSync()
        stopCollectors()
        collectors = emptyList()

        composeScreenTracker?.stop()
        unregisterActivityCallback(application)


        currentActivityName = null
        isRunning = false
    }

    internal fun currentScreenName(): String {
        val composeScreen = composeScreenTracker?.currentScreenName()
        val composeScreenString = composeScreen?.let { "compose/$it" }
        // TODO add fragment name
        return composeScreenString
            ?: currentActivityName
            ?: "unknown"
    }

    private fun registerActivityCallback(application: Application) {
        if (activityLifecycleCallbacks != null) return

        val callbacks = object : Application.ActivityLifecycleCallbacks {
            override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) = Unit

            override fun onActivityDestroyed(activity: Activity) {
                if (currentActivityName == activity.javaClass.simpleName) {
                    currentActivityName = null
                }
            }

            override fun onActivityPaused(activity: Activity) {
                if (currentActivityName == activity.javaClass.simpleName) {
                    currentActivityName = null
                    resumedCount--
                    if (resumedCount <= 0) {
                        resumedCount = 0
                        stopCollectors()
                    }
                }
            }

            override fun onActivityResumed(activity: Activity) {
                currentActivityName = activity.javaClass.simpleName

                resumedCount++
                if (resumedCount == 1) {
                    startCollectors(activity)
                }
            }

            override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) = Unit

            override fun onActivityStarted(activity: Activity) = Unit

            override fun onActivityStopped(activity: Activity) = Unit
        }

        application.registerActivityLifecycleCallbacks(callbacks)
        activityLifecycleCallbacks = callbacks
    }

    fun attachNavController(navController: NavController) {
        composeScreenTracker?.stop()
        composeScreenTracker = ComposeScreenTracker(scope)
        composeScreenTracker?.start(navController)
    }

    private fun unregisterActivityCallback(application: Application) {
        activityLifecycleCallbacks?.let {
            application.unregisterActivityLifecycleCallbacks(it)
        }
        activityLifecycleCallbacks = null
    }
}