package com.ndevelop.perfx.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.ndevelop.perfx.ExperimentConfig
import com.ndevelop.perfx.RegressionType
import com.ndevelop.perfx.cpuWorkers
import com.ndevelop.perfx.ui.theme.PerfXTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext

@Composable
fun CpuLoadScreen(experiment: ExperimentConfig? = null) {
    var isRunning by remember { mutableStateOf(false) }
    var counter by remember { mutableStateOf(0L) }
    val workers = remember(experiment) { cpuWorkers(experiment?.intensity ?: 1) }

    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text("CPU Load Demo", style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))
        if (experiment == null) {
            Button(onClick = { isRunning = !isRunning }) {
                Text(if (isRunning) "Stop Load" else "Start Load")
            }
        } else {
            Text("Experiment: ${experiment.type} (intensity ${experiment.intensity})")
        }
        Spacer(modifier = Modifier.height(16.dp))
        Text("Counter: $counter")
    }

    // Experiment mode: idle for the baseline window, then enable the CPU regression.
    // CONTROL runs stay idle for the whole session.
    if (experiment != null && experiment.type == RegressionType.CPU) {
        LaunchedEffect(Unit) {
            delay(experiment.baselineSecs * 1000L)
            isRunning = true
        }
    }

    // High CPU loop, spread across `workers` background coroutines.
    LaunchedEffect(isRunning, workers) {
        if (isRunning) {
            withContext(Dispatchers.Default) {
                coroutineScope {
                    repeat(workers) {
                        launch {
                            while (isActive && isRunning) {
                                var localCounter = 0L
                                for (i in 2..10_000) {
                                    if (isPrime(i)) localCounter++
                                }
                                counter += localCounter
                                delay(10) // yield so SDK upload coroutines can run
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun isPrime(n: Int): Boolean {
    if (n < 2) return false
    for (i in 2..kotlin.math.sqrt(n.toDouble()).toInt()) {
        if (n % i == 0) return false
    }
    return true
}


@Composable
@Preview(showBackground = true)
fun CpuScreenPreview() {
    PerfXTheme {
        CpuLoadScreen()
    }
}
