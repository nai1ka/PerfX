package com.ndevelop.perfx.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ndevelop.perfx.ExperimentConfig
import com.ndevelop.perfx.RegressionType
import com.ndevelop.perfx.memoryMbPerTick
import kotlinx.coroutines.delay

@Composable
fun MemoryLeakTestScreen(experiment: ExperimentConfig? = null) {

    val allocations = remember { mutableStateListOf<ByteArray>() }

    var running by remember { mutableStateOf(false) }
    var allocatedMb by remember { mutableStateOf(0) }
    val mbPerTick = remember(experiment) { memoryMbPerTick(experiment?.intensity ?: 1) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {

        Text("Memory Usage Test", style = MaterialTheme.typography.headlineSmall)

        Spacer(Modifier.height(16.dp))

        if (experiment == null) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {

                Button(
                    onClick = { running = true }
                ) {
                    Text("Start allocating")
                }

                Button(
                    onClick = {
                        running = false
                        allocations.clear()
                        allocatedMb = 0
                    }
                ) {
                    Text("Clear memory")
                }
            }
        } else {
            Text("Experiment: ${experiment.type} ($mbPerTick MB / 100 ms)")
        }

        Spacer(Modifier.height(16.dp))

        Text("Allocated memory: $allocatedMb MB")

        Spacer(Modifier.height(24.dp))

        Text("Objects stored: ${allocations.size}")
    }

    // Experiment mode: idle for the baseline window, then start leaking memory.
    if (experiment != null && experiment.type == RegressionType.MEMORY) {
        LaunchedEffect(Unit) {
            delay(experiment.baselineSecs * 1000L)
            running = true
        }
    }

    LaunchedEffect(running) {

        while (running) {

            repeat(mbPerTick) {
                allocations.add(ByteArray(256 * 1024))
                allocatedMb += 1
            }

            delay(200)
        }
    }
}
