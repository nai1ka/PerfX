package com.ndevelop.sdk.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(
    tableName = "metrics",
//    indices = [
//        Index("timestamp"),
//        Index("metricId"),
//        Index("uploaded")
//    ]
)
data class MetricDb(

    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    val metricId: String,

    val metricType: String,

    val value: Double,

    val screenName: String,

    val timestamp: Long,
)