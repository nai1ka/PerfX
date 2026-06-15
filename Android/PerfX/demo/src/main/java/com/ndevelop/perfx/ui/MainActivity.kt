package com.ndevelop.perfx.ui

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.ndevelop.perfx.ExperimentConfig
import com.ndevelop.perfx.RegressionType
import com.ndevelop.perfx.ui.screens.AnimationTestScreen
import com.ndevelop.perfx.ui.screens.CpuLoadScreen
import com.ndevelop.perfx.ui.screens.MemoryLeakTestScreen
import com.ndevelop.perfx.ui.theme.PerfXTheme
import com.ndevelop.sdk.PerfX

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val experiment = ExperimentConfig.fromIntent(intent)
        if (experiment != null) {
            Log.i("PerfXExperiment", "Experiment mode: $experiment")
        }
        // navigate_to overrides both experiment-based nav and BuildConfig.TARGET_SCREEN.
        val navigateTo = intent.getStringExtra("navigate_to")
        setContent {
            PerfXTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { paddingValues ->
                    Box(modifier = Modifier.padding(paddingValues)) {
                        NavHostApp(experiment, navigateTo)
                    }
                }
            }
        }
    }
}

@Composable
fun NavHostApp(experiment: ExperimentConfig? = null, navigateTo: String? = null) {
    val navController = rememberNavController()

    LaunchedEffect(navController) {
        PerfX.attachNavController(navController)
    }

    val startDestination = navigateTo ?: when (experiment?.type) {
        RegressionType.CPU, RegressionType.CONTROL -> "cpu_load"
        RegressionType.MEMORY -> "ram_load"
        RegressionType.UI -> "ui_responsiveness"
        null -> com.ndevelop.perfx.BuildConfig.TARGET_SCREEN
    }

    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable("home") { HomeScreen(navController) }
        composable("ui_responsiveness") {
            AnimationTestScreen(experiment?.takeIf { it.type == RegressionType.UI })
        }
        composable("cpu_load") {
            CpuLoadScreen(
                experiment?.takeIf {
                    it.type == RegressionType.CPU || it.type == RegressionType.CONTROL
                }
            )
        }
        composable("ram_load") {
            MemoryLeakTestScreen(experiment?.takeIf { it.type == RegressionType.MEMORY })
        }
    }
}

@Composable
fun HomeScreen(navController: NavController, modifier: Modifier = Modifier) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        contentAlignment = Alignment.Center

    ) {
        Column {
            Button(onClick = {
                navController.navigate("ui_responsiveness")
            }, modifier = Modifier.width(200.dp)) {
                Text(text = "UI responsiveness")
            }
            Button(onClick = {
                navController.navigate("cpu_load")
            }, modifier = Modifier.width(200.dp)) {
                Text(text = "CPU")
            }
            Button(onClick = {
                navController.navigate("ram_load")
            }, modifier = Modifier.width(200.dp)) {
                Text(text = "RAM")
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun MainPagePreview() {
    PerfXTheme {
        HomeScreen(rememberNavController())
    }
}