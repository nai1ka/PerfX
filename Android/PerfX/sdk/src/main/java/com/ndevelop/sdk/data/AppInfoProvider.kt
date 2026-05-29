package com.ndevelop.sdk.data

import android.app.ActivityManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.PowerManager
import android.view.WindowManager
import com.ndevelop.sdk.models.AppInfo

internal class AppInfoProvider {

    fun get(context: Context, projectId: String): AppInfo {

        val packageInfo = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.packageManager.getPackageInfo(context.packageName, PackageManager.PackageInfoFlags.of(0))
        } else {
            @Suppress("DEPRECATION")
            context.packageManager.getPackageInfo(context.packageName, 0)
        }

        @Suppress("DEPRECATION")
        val versionCode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            packageInfo.longVersionCode.toInt()
        } else {
            packageInfo.versionCode
        }

        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)
        val ramGb = memoryInfo.totalMem.toDouble() / (1024 * 1024 * 1024)

        val cores = Runtime.getRuntime().availableProcessors()

        val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        @Suppress("DEPRECATION")
        val screenRefreshRate = windowManager.defaultDisplay.refreshRate.toDouble()

        val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        val isPowerSaveMode = powerManager.isPowerSaveMode

        return AppInfo(
            projectId = projectId,
            packageName = context.packageName,
            versionName = packageInfo.versionName ?: "unknown",
            versionCode = versionCode,
            osVersion = Build.VERSION.RELEASE,
            deviceModel = "${Build.MANUFACTURER} ${Build.MODEL}",
            totalRamGb = ramGb,
            cpuCores = cores,
            screenRefreshRate = screenRefreshRate,
            isPowerSaveMode = isPowerSaveMode,
        )
    }
}