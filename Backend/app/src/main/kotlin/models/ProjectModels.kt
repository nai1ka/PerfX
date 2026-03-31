package com.perfx.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ProjectDto(
    @SerialName("id")
    val id: String,

    @SerialName("name")
    val name: String,

    @SerialName("package_name")
    val packageName: String,
)

@Serializable
data class CreateProjectRequest(
    @SerialName("name")
    val name: String,

    @SerialName("package_name")
    val packageName: String,
)