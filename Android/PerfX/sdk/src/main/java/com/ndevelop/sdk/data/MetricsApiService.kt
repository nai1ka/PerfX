package com.ndevelop.sdk.data

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface MetricsApiService {
    @POST("ingest")
    suspend fun uploadBatch(
        @Body batchApi: BatchApi,
    ): Response<Unit>
}