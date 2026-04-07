package com.ndevelop.sdk.data

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import android.os.PowerManager
import android.view.WindowManager
import com.ndevelop.sdk.models.AppInfo

internal class AppInfoProvider {

    fun get(context: Context, projectId: String): AppInfo {

        val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)

        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)
        val ramGb = memoryInfo.totalMem.toDouble() / (1024 * 1024 * 1024)

        val cores = Runtime.getRuntime().availableProcessors()

        val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        val screenRefreshRate = windowManager.defaultDisplay.refreshRate.toDouble() // e.g., 60.0 or 120.0

        val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        val isPowerSaveMode = powerManager.isPowerSaveMode

        return AppInfo(
            projectId = projectId,
            packageName = context.packageName,
            appVersion = packageInfo.versionName ?: "unknown",
            osVersion = Build.VERSION.RELEASE ?: "unknown",
            deviceModel = "${Build.MANUFACTURER} ${Build.MODEL}",
            totalRamGb = ramGb,
            cpuCores = cores,
            screenRefreshRate = screenRefreshRate,
            isPowerSaveMode = isPowerSaveMode,
        )
    }
}