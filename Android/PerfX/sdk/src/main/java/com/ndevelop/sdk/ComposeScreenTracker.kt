package com.ndevelop.sdk

import androidx.navigation.NavController
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

internal class ComposeScreenTracker(
    private val scope: CoroutineScope
) {

    @Volatile
    private var currentScreenName: String? = null

    private var job: Job? = null

    fun start(navController: NavController) {
        job?.cancel()
        job = scope.launch {
            navController.currentBackStackEntryFlow.collect { entry ->
                currentScreenName = entry.destination.route ?: "unknown"
            }
        }
    }

    fun stop() {
        job?.cancel()
        job = null
        currentScreenName = null
    }

    fun currentScreenName(): String = currentScreenName ?: "unknown"
}