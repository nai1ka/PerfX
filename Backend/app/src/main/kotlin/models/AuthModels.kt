package com.perfx.models

import kotlinx.serialization.Serializable
import models.UserDto

@Serializable
data class LoginRequest(
    val email: String,
    val password: String
)

@Serializable
data class LoginResponse(
    val token: String,
    val user: UserDto
)
