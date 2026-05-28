package com.ndevelop.perfx

import android.app.Application
import com.ndevelop.sdk.PerfX

class DemoApp : Application() {
    override fun onCreate() {
        super.onCreate()
        if (BuildConfig.SDK_ENABLED) {
            PerfX.initialize(
                this,
                "ce96511b-500e-407e-ab9c-9d7a6c966dc5",
                endpointUrl = "http://10.0.2.2:8080/"
            )
        }
    }
}