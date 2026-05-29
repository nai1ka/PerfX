package com.perfx.jobs

import com.perfx.data.ClickHouseClient
import data.repository.AuthRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import kotlin.time.Duration.Companion.minutes

/**
 * Periodically reads version statistics from ClickHouse and upserts them
 * into the Postgres [version_releases] catalogue.
 *
 * Runs every [intervalMinutes] minutes in the provided [CoroutineScope].
 */
class VersionSyncJob(
    private val clickHouseClient: ClickHouseClient,
    private val authRepository: AuthRepository,
    private val scope: CoroutineScope,
    private val intervalMinutes: Long = 5,
) {
    private val chDateFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss[.SSS][.SS][.S]")

    fun start() {
        scope.launch {
            while (true) {
                try {
                    sync()
                } catch (e: Exception) {
                    System.err.println("[VersionSyncJob] sync failed: ${e.message}")
                }
                delay(intervalMinutes.minutes)
            }
        }
    }

    private suspend fun sync() {
        val sql = """
            SELECT
                project_id,
                version_code,
                version_name,
                min(ts)    AS first_seen,
                count()    AS sample_count
            FROM metric_records
            GROUP BY project_id, version_code, version_name
        """.trimIndent()

        val rows = clickHouseClient.query(sql)

        for (row in rows) {
            try {
                val projectId   = row["project_id"]?.jsonPrimitive?.content   ?: continue
                val versionCode = row["version_code"]?.jsonPrimitive?.content?.toIntOrNull() ?: continue
                val versionName = row["version_name"]?.jsonPrimitive?.content  ?: continue
                val sampleCount = row["sample_count"]?.jsonPrimitive?.longOrNull ?: 0L
                val firstSeen   = row["first_seen"]?.jsonPrimitive?.content?.let(::parseChTimestamp)
                    ?: Instant.now()

                authRepository.upsertVersionRelease(
                    projectId   = projectId,
                    versionCode = versionCode,
                    versionName = versionName,
                    firstSeenAt = firstSeen,
                    sampleCount = sampleCount,
                )
            } catch (e: Exception) {
                System.err.println("[VersionSyncJob] skipping row: ${e.message}")
            }
        }
    }

    private fun parseChTimestamp(raw: String): Instant =
        LocalDateTime.parse(raw.trim(), chDateFormatter).toInstant(ZoneOffset.UTC)
}
