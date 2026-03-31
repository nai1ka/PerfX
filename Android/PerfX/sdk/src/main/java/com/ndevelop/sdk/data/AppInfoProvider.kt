package com.ndevelop.sdk.data

import android.content.Context
import android.os.Build
import com.ndevelop.sdk.models.AppInfo

internal class AppInfoProvider {

    fun get(context: Context, projectId: String): AppInfo {

        val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)

        return AppInfo(
            projectId = projectId,
            packageName = context.packageName,
            appVersion = packageInfo.versionName ?: "unknown",
            osVersion = Build.VERSION.RELEASE ?: "unknown",
            deviceModel = "${Build.MANUFACTURER} ${Build.MODEL}"
        )
    }
}