package com.ndevelop.perfx

import android.content.Context
import android.view.Choreographer
import android.os.Handler
import android.os.Looper

/**
 * Activates a synthetic performance regression that is baked into the APK at build time
 * via BuildConfig.BAKED_REGRESSION_TYPE / BAKED_REGRESSION_INTENSITY.
 *
 * Called once from DemoApp.onCreate(); subsequent calls for the same type are additive
 * (more workers, more allocations), so avoid calling more than once per process.
 */
object RegressionInjector {

    /** Added delay (ms) for click handlers when interaction injection is active. */
    @Volatile var interactionDelayMs: Long = 0L

    // Direct (off-heap) buffers — GC cannot see or reclaim them.
    // Each buffer's pages are touched on allocation so the OS physically commits the RAM.
    private val leakedBuffers = mutableListOf<java.nio.ByteBuffer>()

    fun activate(context: Context, type: String, intensity: Int) {
        when (type.lowercase()) {
            "cpu"         -> startCpuWorkers(intensity)
            "memory"      -> startMemoryLeak(intensity)
            "ui"          -> startUiJank(intensity)
            "startup"     -> Thread.sleep(intensity * 200L)
            "interaction" -> interactionDelayMs = intensity * 200L
            // "none", "control" → no-op
        }
    }

    private enum class CpuPhase { IDLE, LIGHT, SPIKE }

    private fun nextCpuPhase(rng: java.util.Random, intensity: Int): CpuPhase {
        val r = rng.nextDouble()
        return when (intensity) {
            1    -> when {
                r < 0.55 -> CpuPhase.IDLE
                r < 0.85 -> CpuPhase.LIGHT
                else     -> CpuPhase.SPIKE
            }
            2    -> when {
                r < 0.30 -> CpuPhase.IDLE
                r < 0.60 -> CpuPhase.LIGHT
                else     -> CpuPhase.SPIKE
            }
            else -> when {
                r < 0.10 -> CpuPhase.IDLE
                r < 0.35 -> CpuPhase.LIGHT
                else     -> CpuPhase.SPIKE
            }
        }
    }

    // Completely quiet — 0.5 to 5 seconds of sleep.
    private fun doIdle(rng: java.util.Random) {
        Thread.sleep(500L + rng.nextInt(4500))
    }

    // Gentle throttled burn — yields every 20 ms so it doesn't peg a core.
    private fun doLight(rng: java.util.Random) {
        val end = System.currentTimeMillis() + 300L + rng.nextInt(1200)
        while (System.currentTimeMillis() < end) {
            var x = 0.0
            repeat(1_000) { x += Math.sqrt(Math.random()) }
            Thread.sleep(20)
        }
    }

    // Full-throttle burst — duration scales with intensity.
    private fun doSpike(rng: java.util.Random, intensity: Int) {
        val maxExtraMs = when (intensity) { 1 -> 200; 2 -> 450; else -> 750 }
        val end = System.currentTimeMillis() + 80L + rng.nextInt(maxExtraMs)
        while (System.currentTimeMillis() < end) {
            var x = 0.0
            repeat(5_000) { x += Math.sqrt(Math.random()) }
        }
    }

    private fun startCpuWorkers(intensity: Int) {
        repeat(cpuWorkers(intensity)) { workerIndex ->
            Thread {
                val rng = java.util.Random()
                // Stagger starts — workers drift out of phase naturally over time.
                Thread.sleep(workerIndex * 200L + rng.nextInt(600).toLong())
                while (true) {
                    when (nextCpuPhase(rng, intensity)) {
                        CpuPhase.IDLE  -> doIdle(rng)
                        CpuPhase.LIGHT -> doLight(rng)
                        CpuPhase.SPIKE -> doSpike(rng, intensity)
                    }
                }
            }.apply { isDaemon = true; start() }
        }
    }

    private fun startMemoryLeak(intensity: Int) {
        // ByteArray (Java heap) triggers GC, which compacts the heap and can
        // paradoxically LOWER measured PSS.  ByteBuffer.allocateDirect() goes to
        // native memory — GC-invisible, shows up reliably in totalPss.
        //
        // Pages are touched on allocation so the OS physically commits the RAM
        // immediately rather than lazy-mapping it.
        val targetMb = when (intensity) { 1 -> 15; 2 -> 80; else -> 130 }
        val mbPerTick = memoryMbPerTick(intensity)
        Thread {
            var allocatedMb = 0
            while (allocatedMb < targetMb) {
                val chunkMb = minOf(mbPerTick, targetMb - allocatedMb)
                try {
                    val buf = java.nio.ByteBuffer.allocateDirect(chunkMb * 1024 * 1024)
                    // Write one byte per page to force physical allocation.
                    var i = 0
                    while (i < buf.capacity()) { buf.put(i, 0x42); i += 4096 }
                    synchronized(leakedBuffers) { leakedBuffers.add(buf) }
                    allocatedMb += chunkMb
                } catch (_: OutOfMemoryError) {
                    break  // near native heap limit — stop gracefully
                }
                Thread.sleep(500)
            }
            // leakedBuffers holds all direct buffers; RAM stays elevated for the run.
        }.apply { isDaemon = true; start() }
    }

    private fun startUiJank(intensity: Int) {
        val blockMs = uiBlockMs(intensity)
        Handler(Looper.getMainLooper()).post {
            Choreographer.getInstance().postFrameCallback(object : Choreographer.FrameCallback {
                override fun doFrame(frameTimeNanos: Long) {
                    Thread.sleep(blockMs)
                    Choreographer.getInstance().postFrameCallback(this)
                }
            })
        }
    }
}
