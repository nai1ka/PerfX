package com.ndevelop.sdk.data

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

object NetworkClient {

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        })
        .connectTimeout(15, TimeUnit.SECONDS)
        .build()

    val json = Json {
        ignoreUnknownKeys = true
    }

    private var _api: MetricsApiService? = null

    val api: MetricsApiService
        get() = _api ?: error("NetworkClient is not initialized. Call PerfX.initialize() first.")

    internal fun initialize(endpointUrl: String) {
        _api = Retrofit.Builder()
            .baseUrl(endpointUrl)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(MetricsApiService::class.java)
    }
}