package com.perfx.plugins


import io.ktor.server.application.*
import org.jetbrains.exposed.v1.jdbc.Database

fun Application.configureDatabases() {
    val host = System.getenv("POSTGRES_HOST") ?: "localhost"
    val port = System.getenv("POSTGRES_PORT") ?: "5432"
    val db = System.getenv("POSTGRES_DB") ?: "perfx"
    val user = System.getenv("POSTGRES_USER") ?: "perfx_user"
    val password = System.getenv("POSTGRES_PASSWORD") ?: "perfx_pass"

    Database.connect(
        url = "jdbc:postgresql://$host:$port/$db",
        driver = "org.postgresql.Driver",
        user = user,
        password = password,
    )
}