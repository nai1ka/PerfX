package com.perfx

import IngestBatchRequest
import IngestResponse
import auth.JwtConfig
import com.perfx.data.ClickHouseClient
import com.perfx.models.CreateProjectRequest
import com.perfx.models.LoginRequest
import com.perfx.models.LoginResponse
import data.repository.AuthRepository

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.auth.authenticate
import io.ktor.server.auth.jwt.JWTPrincipal
import io.ktor.server.auth.principal
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import models.UserDto
import org.mindrot.jbcrypt.BCrypt

fun Application.configureRouting(authRepository: AuthRepository) {
    val clickHouseClient = ClickHouseClient(
        baseUrl = System.getenv("CLICKHOUSE_URL") ?: "http://185.71.196.185:8123",
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
        }

        post("/ingest") {
            val request = call.receive<IngestBatchRequest>()

            if (request.metrics.isEmpty()) {
                call.respond(HttpStatusCode.BadRequest, IngestResponse(0, "empty batch"))
                return@post
            }

// TODO check that such project exists
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