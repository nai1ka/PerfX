package com.ndevelop.perfx

import android.content.Intent

/**
 * Scriptable experiment mode for the thesis regression-detection evaluation.
 *
 * The demo app is launched by the driver script with intent extras, e.g.:
 *   adb shell am start -n com.ndevelop.perfx/.ui.MainActivity \
 *     --es regression_type cpu --ei intensity 2 \
 *     --ei baseline_secs 120 --ei current_secs 120
 *
 * In experiment mode the target screen runs idle for `baselineSecs`, then enables
 * the synthetic regression at the given intensity and keeps it on. The driver
 * force-stops the process after the windows elapse.
 */
enum class RegressionType { CPU, MEMORY, UI, CONTROL }

data class ExperimentConfig(
    val type: RegressionType,
    val intensity: Int,      // 1 = low, 2 = medium, 3 = high
    val baselineSecs: Int,
    val currentSecs: Int,
) {
    companion object {
        fun fromIntent(intent: Intent?): ExperimentConfig? {
            val raw = intent?.getStringExtra("regression_type") ?: return null
            val type = when (raw.lowercase()) {
                "cpu" -> RegressionType.CPU
                "memory" -> RegressionType.MEMORY
                "ui" -> RegressionType.UI
                "control" -> RegressionType.CONTROL
                else -> return null
            }
            return ExperimentConfig(
                type = type,
                intensity = intent.getIntExtra("intensity", 2).coerceIn(1, 3),
                baselineSecs = intent.getIntExtra("baseline_secs", 120),
                currentSecs = intent.getIntExtra("current_secs", 120),
            )
        }
    }
}

/** Number of parallel CPU-burning workers for the CPU regression. */
fun cpuWorkers(intensity: Int): Int = when (intensity) {
    1 -> 1
    2 -> 2
    else -> 4
}

/** Megabytes allocated per 500 ms tick for the memory regression (capped at 15/80/130 MB). */
fun memoryMbPerTick(intensity: Int): Int = when (intensity) {
    1 -> 1
    2 -> 2
    else -> 3
}

/** Main-thread block time per frame (ms) for the UI-thread regression. */
fun uiBlockMs(intensity: Int): Long = when (intensity) {
    1 -> 15L
    2 -> 40L
    else -> 90L
}
