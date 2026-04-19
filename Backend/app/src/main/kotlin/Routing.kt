package com.perfx

import IngestBatchRequest
import IngestResponse
import auth.JwtConfig
import com.perfx.data.ClickHouseClient
import com.perfx.models.*
import data.repository.AuthRepository

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.auth.authenticate
import io.ktor.server.auth.jwt.JWTPrincipal
import io.ktor.server.auth.principal
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import models.UserDto
import org.mindrot.jbcrypt.BCrypt

fun Application.configureRouting(authRepository: AuthRepository) {
    val clickHouseClient = ClickHouseClient(
        baseUrl = System.getenv("CLICKHOUSE_URL") ?: "http://localhost:8123",
        db = System.getenv("CLICKHOUSE_DB") ?: "metrics",
        user = System.getenv("CLICKHOUSE_USER") ?: "metrics_user",
        password = System.getenv("CLICKHOUSE_PASSWORD") ?: "metrics_pass"
    )

    routing {
        get("/health") {
            call.respondText("ok")
        }

        post("/auth/login") {
            val request = call.receive<LoginRequest>()
            val user = authRepository.findUserByEmail(request.email)

            if (user == null || !BCrypt.checkpw(request.password, user.passwordHash)) {
                call.respond(HttpStatusCode.Unauthorized, mapOf("message" to "Invalid credentials"))
                return@post
            }

            val token = JwtConfig.makeToken(user.id, user.email)
            call.respond(LoginResponse(token, UserDto(user.id, user.email)))
        }

        post("/auth/signup") {
            val request = call.receive<LoginRequest>()

            if (authRepository.findUserByEmail(request.email) != null) {
                call.respond(HttpStatusCode.Conflict, mapOf("message" to "User already exists"))
                return@post
            }

            val hash = BCrypt.hashpw(request.password, BCrypt.gensalt())
            val created = authRepository.createUser(request.email, hash)
            val token = JwtConfig.makeToken(created.id, created.email)

            call.respond(HttpStatusCode.Created, LoginResponse(token, created))
        }

        authenticate("auth-jwt") {
            get("/auth/me") {
                val principal = call.principal<JWTPrincipal>()!!
                val userId = principal.payload.subject
                val email = principal.payload.getClaim("email").asString()

                call.respond(
                    HttpStatusCode.OK,
                    mapOf(
                        "id" to userId,
                        "email" to email
                    )
                )
            }

            get("/projects") {
                val principal = call.principal<JWTPrincipal>()!!
                val userId = principal.payload.subject

                val projects = authRepository.getProjectsForUser(userId)
                call.respond(HttpStatusCode.OK, projects)
            }

            post("/projects") {
                val principal = call.principal<JWTPrincipal>()!!
                val userId = principal.payload.subject

                val request = call.receive<CreateProjectRequest>()

                if (request.name.isBlank()) {
                    call.respond(HttpStatusCode.BadRequest, "Project name is required")
                    return@post
                }

                if (request.packageName.isBlank()) {
                    call.respond(HttpStatusCode.BadRequest, "Android App ID is required")
                    return@post
                }

                if (authRepository.existsProjectByName(request.name)) {
                    call.respond(HttpStatusCode.Conflict, "Project with this name already exists")
                    return@post
                }

                if (authRepository.existsProjectByPackageName(request.packageName)) {
                    call.respond(HttpStatusCode.Conflict, "Project with this Android App ID already exists")
                    return@post
                }

                val project = authRepository.createProjectForUser(
                    userId = userId,
                    name = request.name,
                    appId = request.packageName
                )

                call.respond(HttpStatusCode.Created, project)
            }

            // ── Regressions ─────────────────────────────────────────────

            get("/regressions") {
                val userId = call.principal<JWTPrincipal>()!!.payload.subject
                val projectId = call.parameters["project_id"]
                    ?: return@get call.respond(HttpStatusCode.BadRequest, "project_id is required")

                if (!authRepository.isProjectOwnedByUser(projectId, userId)) {
                    return@get call.respond(HttpStatusCode.Forbidden, "Access denied")
                }

                val regressions = authRepository.getRegressionsForProject(projectId)
                call.respond(HttpStatusCode.OK, regressions)
            }

            delete("/regressions/{id}") {
                val userId = call.principal<JWTPrincipal>()!!.payload.subject
                val regressionId = call.parameters["id"]
                    ?: return@delete call.respond(HttpStatusCode.BadRequest, "id is required")
                val projectId = call.parameters["project_id"]
                    ?: return@delete call.respond(HttpStatusCode.BadRequest, "project_id is required")

                if (!authRepository.isProjectOwnedByUser(projectId, userId)) {
                    return@delete call.respond(HttpStatusCode.Forbidden, "Access denied")
                }

                val deleted = authRepository.deleteRegression(regressionId, projectId)
                if (deleted) {
                    call.respond(HttpStatusCode.OK, mapOf("status" to "deleted"))
                } else {
                    call.respond(HttpStatusCode.NotFound, "Regression not found")
                }
            }

            // ── ClickHouse metric queries ───────────────────────────────

            get("/metrics/screens") {
                val userId = call.principal<JWTPrincipal>()!!.payload.subject
                val projectId = call.parameters["project_id"]
                    ?: return@get call.respond(HttpStatusCode.BadRequest, "project_id is required")

                if (!authRepository.isProjectOwnedByUser(projectId, userId)) {
                    return@get call.respond(HttpStatusCode.Forbidden, "Access denied")
                }

                val sql = """
                    SELECT DISTINCT screen_name
                    FROM metric_records
                    WHERE project_id = '$projectId'
                    ORDER BY screen_name ASC
                """.trimIndent()

                val rows = clickHouseClient.query(sql)
                val screens = rows.map { it["screen_name"]!!.jsonPrimitive.content }
                call.respond(HttpStatusCode.OK, screens)
            }

            get("/metrics/metric-ids") {
                val userId = call.principal<JWTPrincipal>()!!.payload.subject
                val projectId = call.parameters["project_id"]
                    ?: return@get call.respond(HttpStatusCode.BadRequest, "project_id is required")

                if (!authRepository.isProjectOwnedByUser(projectId, userId)) {
                    return@get call.respond(HttpStatusCode.Forbidden, "Access denied")
                }

                val sql = """
                    SELECT DISTINCT metric_id
                    FROM metric_records
                    WHERE project_id = '$projectId'
                    ORDER BY metric_id ASC
                """.trimIndent()

                val rows = clickHouseClient.query(sql)
                val metricIds = rows.map { it["metric_id"]!!.jsonPrimitive.content }
                call.respond(HttpStatusCode.OK, metricIds)
            }

            get("/metrics") {
                val userId = call.principal<JWTPrincipal>()!!.payload.subject
                val projectId = call.parameters["project_id"]
                    ?: return@get call.respond(HttpStatusCode.BadRequest, "project_id is required")
                val metricId = call.parameters["metric_id"] ?: ""
                val screenName = call.parameters["screen_name"] ?: ""
                val minutesBack = call.parameters["minutes_back"]?.toIntOrNull() ?: 60

                if (!authRepository.isProjectOwnedByUser(projectId, userId)) {
                    return@get call.respond(HttpStatusCode.Forbidden, "Access denied")
                }

                val filters = mutableListOf("project_id = '$projectId'")
                if (metricId.isNotBlank()) filters.add("metric_id = '$metricId'")
                if (screenName.isNotBlank()) filters.add("screen_name = '$screenName'")
                filters.add("ts >= now() - INTERVAL $minutesBack MINUTE")

                val sql = """
                    SELECT ts, project_id, package_name, app_version, metric_id, screen_name, device_cohort, value
                    FROM metric_records
                    WHERE ${filters.joinToString(" AND ")}
                    ORDER BY ts DESC
                """.trimIndent()

                val rows = clickHouseClient.query(sql)
                call.respond(HttpStatusCode.OK, rows)
            }

            get("/projects/{id}/status") {
                val userId = call.principal<JWTPrincipal>()!!.payload.subject
                val projectId = call.parameters["id"]
                    ?: return@get call.respond(HttpStatusCode.BadRequest, "id is required")

                if (!authRepository.isProjectOwnedByUser(projectId, userId)) {
                    return@get call.respond(HttpStatusCode.Forbidden, "Access denied")
                }

                val sql = """
                    SELECT
                        count() AS total_rows,
                        max(ts) AS last_ingested,
                        uniq(metric_id) AS unique_metrics,
                        uniq(screen_name) AS unique_screens
                    FROM metric_records
                    WHERE project_id = '$projectId'
                """.trimIndent()

                val rows = clickHouseClient.query(sql)
                if (rows.isEmpty()) {
                    call.respond(HttpStatusCode.OK, ProjectStatusDto(0, null, 0, 0))
                } else {
                    val row = rows.first()
                    call.respond(HttpStatusCode.OK, ProjectStatusDto(
                        totalRows = row["total_rows"]?.jsonPrimitive?.longOrNull ?: 0,
                        lastIngested = row["last_ingested"]?.jsonPrimitive?.content?.takeIf { it != "1970-01-01 00:00:00.000" },
                        uniqueMetrics = row["unique_metrics"]?.jsonPrimitive?.longOrNull ?: 0,
                        uniqueScreens = row["unique_screens"]?.jsonPrimitive?.longOrNull ?: 0,
                    ))
                }
            }

            get("/projects/{id}/dimensions") {
                val userId = call.principal<JWTPrincipal>()!!.payload.subject
                val projectId = call.parameters["id"]
                    ?: return@get call.respond(HttpStatusCode.BadRequest, "id is required")

                if (!authRepository.isProjectOwnedByUser(projectId, userId)) {
                    return@get call.respond(HttpStatusCode.Forbidden, "Access denied")
                }

                val sql = """
                    SELECT DISTINCT metric_id, screen_name, device_cohort
                    FROM metric_records
                    WHERE project_id = '$projectId'
                    ORDER BY metric_id, screen_name, device_cohort
                """.trimIndent()

                val rows = clickHouseClient.query(sql)
                val dimensions = rows.map {
                    MetricDimensionDto(
                        metricId = it["metric_id"]!!.jsonPrimitive.content,
                        screenName = it["screen_name"]!!.jsonPrimitive.content,
                        deviceCohort = it["device_cohort"]!!.jsonPrimitive.content,
                    )
                }
                call.respond(HttpStatusCode.OK, dimensions)
            }

            post("/projects/{id}/plots") {
                val userId = call.principal<JWTPrincipal>()!!.payload.subject
                val projectId = call.parameters["id"]
                    ?: return@post call.respond(HttpStatusCode.BadRequest, "id is required")

                if (!authRepository.isProjectOwnedByUser(projectId, userId)) {
                    return@post call.respond(HttpStatusCode.Forbidden, "Access denied")
                }

                val request = call.receive<CustomPlotRequest>()

                val aggFn = when (request.aggregation) {
                    "P50" -> "quantile(0.50)(value)"
                    "P95" -> "quantile(0.95)(value)"
                    "Avg" -> "avg(value)"
                    "Max" -> "max(value)"
                    else -> "quantile(0.95)(value)"
                }

                val cohortFilter = if (request.deviceCohort != "All") {
                    "AND device_cohort = '${request.deviceCohort}'"
                } else ""

                val sql = """
                    SELECT
                        toStartOfInterval(ts, INTERVAL ${request.bucketMinutes} MINUTE) AS bucket,
                        $aggFn AS metric_value
                    FROM metric_records
                    WHERE
                        project_id = '$projectId'
                        AND metric_id = '${request.metricId}'
                        AND screen_name = '${request.screenName}'
                        $cohortFilter
                        AND ts >= now() - INTERVAL ${request.minutesBack} MINUTE
                    GROUP BY bucket
                    ORDER BY bucket
                """.trimIndent()

                val rows = clickHouseClient.query(sql)
                val points = rows.map {
                    PlotPointDto(
                        bucket = it["bucket"]!!.jsonPrimitive.content,
                        metricValue = it["metric_value"]!!.jsonPrimitive.doubleOrNull ?: 0.0,
                    )
                }
                call.respond(HttpStatusCode.OK, points)
            }
        }

        post("/ingest") {
            val request = call.receive<IngestBatchRequest>()

            if (request.metrics.isEmpty()) {
                call.respond(HttpStatusCode.BadRequest, IngestResponse(0, "empty batch"))
                return@post
            }

            clickHouseClient.insertBatch(request)

            call.respond(
                HttpStatusCode.Accepted,
                IngestResponse(
                    accepted = request.metrics.size,
                    status = "accepted"
                )
            )
        }
    }
}