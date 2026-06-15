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
        val bakedType = BuildConfig.BAKED_REGRESSION_TYPE
        val bakedIntensity = BuildConfig.BAKED_REGRESSION_INTENSITY
        if (bakedType != "none" && bakedIntensity > 0) {
            RegressionInjector.activate(this, bakedType, bakedIntensity)
        }
    }
}