package com.ndevelop.perfx.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameMillis
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.animateLottieCompositionAsState
import com.airbnb.lottie.compose.rememberLottieComposition
import com.ndevelop.perfx.ExperimentConfig
import com.ndevelop.perfx.R
import com.ndevelop.perfx.RegressionType
import com.ndevelop.perfx.uiBlockMs
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive

@Composable
fun AnimationTestScreen(experiment: ExperimentConfig? = null) {
    var enabled by remember { mutableStateOf(false) }
    var blockMs by remember {
        mutableLongStateOf(experiment?.let { uiBlockMs(it.intensity) } ?: 40L)
    }

    val composition by rememberLottieComposition(
        LottieCompositionSpec.RawRes(R.raw.rocket)
    )

    val progress by animateLottieCompositionAsState(
        composition = composition,
        iterations = LottieConstants.IterateForever
    )

    // Experiment mode: idle for the baseline window, then block the UI thread.
    if (experiment != null && experiment.type == RegressionType.UI) {
        LaunchedEffect(Unit) {
            delay(experiment.baselineSecs * 1000L)
            enabled = true
        }
    }

    LaunchedEffect(enabled, blockMs) {
        if (enabled) {
            while (isActive) {
                withFrameMillis {
                    Thread.sleep(blockMs)
                }
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Lagging Animation Test", style = MaterialTheme.typography.headlineSmall)

        Spacer(Modifier.height(16.dp))

        if (experiment == null) {
            Button(onClick = { enabled = !enabled }) {
                Text(if (enabled) "Stop" else "Start")
            }

            Spacer(Modifier.height(16.dp))

            Text("Block main thread: $blockMs ms per frame")
            Slider(
                value = blockMs.toFloat(),
                onValueChange = { blockMs = it.toLong() },
                valueRange = 0f..120f
            )
        } else {
            Text("Experiment: ${experiment.type} (block $blockMs ms / frame)")
        }

        Spacer(Modifier.height(32.dp))

        LottieAnimation(
            composition = composition,
            progress = { progress },
            modifier = Modifier.size(300.dp)
        )
    }
}
