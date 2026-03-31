package com.perfx

import com.perfx.plugins.configureDatabases
import com.perfx.plugins.configureSecurity
import configureSerialization
import data.repository.PostgresAuthRepository
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.StatusPages
import io.ktor.server.response.respond

fun main(args: Array<String>) {
    io.ktor.server.netty.EngineMain.main(args)
}

fun Application.module() {
    val authRepository = PostgresAuthRepository()
    install(StatusPages) {
        exception<Throwable> { call, cause ->
            cause.printStackTrace()
            call.respond(HttpStatusCode.InternalServerError, "error")
        }
    }

    configureDatabases()
    configureSerialization()
    configureSecurity()
    configureRouting(authRepository)
}