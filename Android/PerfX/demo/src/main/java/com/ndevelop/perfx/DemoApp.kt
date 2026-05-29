package com.ndevelop.perfx

import android.app.Application
import com.ndevelop.sdk.PerfX

class DemoApp : Application() {
    override fun onCreate() {
        super.onCreate()
        if (BuildConfig.SDK_ENABLED) {
            PerfX.initialize(
                this,
                BuildConfig.PROJECT_ID,
                endpointUrl = BuildConfig.ENDPOINT_URL,
            )
        }
    }
}