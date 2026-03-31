package com.ndevelop.sdk.data

import com.ndevelop.sdk.models.Metric


internal fun Metric.mapToDb(
    screenName: String,
): MetricDb {
    return MetricDb(
        metricId = id,
        metricType = "TODO",
        value = value,
        screenName = screenName,
        timestamp = timestamp
    )
}

internal fun MetricDb.mapToApi(): MetricApi {
    return MetricApi(
        ts = timestamp.toString(),
        metricId = metricId,
        metricType = MetricType.SAMPLE, //TODO
        screenName = screenName,
        value = value
    )
}
