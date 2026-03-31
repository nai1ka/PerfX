package com.perfx.data

import IngestBatchRequest
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.CIO
import io.ktor.client.request.*
import io.ktor.http.*
import kotlinx.serialization.json.*

class ClickHouseClient(
    private val baseUrl: String,
    private val db: String,
    private val user: String,
    private val password: String
) {
    private val http = HttpClient(CIO)

    suspend fun insertBatch(batch: IngestBatchRequest) {
        val rows = buildJsonLines(batch)

        val query = """
            INSERT INTO $db.metric_records
            FORMAT JSONEachRow
        """.trimIndent()

        val url = "$baseUrl/?database=$db"

        val body = buildString {
            append(query)
            append("\n")
            append(rows)
        }

        val response = http.post(url) {
            basicAuth(user, password)
            contentType(ContentType.Text.Plain)
            setBody(body)
        }

        if (!response.status.isSuccess()) {
            val text: String = response.body()
            error("ClickHouse insert failed: ${response.status} $text")
        }
    }

    private fun buildJsonLines(batch: IngestBatchRequest): String {
        return buildString {
            for (m in batch.metrics) {
                val obj = buildJsonObject {
                    put("project_id", batch.appInfo.projectId)
                    put("package_name", batch.appInfo.packageName)
                    put("ts", m.ts)
                    put("metric_id", m.metricId)
                    put("metric_type", m.metricType)
                    put("screen_name", m.screenName)
                    put("value", m.value)
                    put("app_version", batch.appInfo.appVersion)
                    put("os_version", batch.appInfo.osVersion)
                    put("device_model", batch.appInfo.deviceModel)
                }
                append(obj.toString())
                append('\n')
            }
        }
    }
}

// TRUNCATE TABLE metrics.metric_records;