#!/usr/bin/env python3
"""
Illustrative demo (synthetic, plausible data): why the release-pair P95 rule
reacts to a SUSTAINED regression but ignores short-term spikes.

Frame time is plotted over time. The detector flags a version when its P95 is
more than 15% above the baseline version's P95. A few rare spikes sit above the
95th percentile, so they do not move P95 -> ignored. A sustained regression
raises the whole trace, so P95 moves -> flagged.

NOT real measurement data; it only illustrates the mechanism on frame time.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
T = 600                 # frames shown over time
THRESHOLD = 0.15
YMAX = 60               # display cap; taller spikes are clipped and annotated


def baseline_frames(n):
    # ~93% smooth frames near the 16.7 ms vsync budget, ~7% mild jank.
    smooth = rng.normal(15.0, 1.2, n)
    jank = rng.normal(22.0, 3.5, n)
    is_jank = rng.random(n) < 0.07
    return np.clip(np.where(is_jank, jank, smooth), 8.0, None)


def p95(x):
    return float(np.percentile(x, 95))


base = baseline_frames(T)

# Transient spikes: baseline, but ~1% of frames spike hard (rare, well < 5%).
spike = baseline_frames(T)
sp = rng.random(T) < 0.01
spike[sp] = rng.normal(220.0, 30.0, sp.sum())

# Sustained regression: every frame a few ms slower (extra per-frame work).
reg = baseline_frames(T) + rng.normal(8.0, 1.5, T)

base_p95 = p95(base)
thr_ms = base_p95 * (1 + THRESHOLD)     # flag if a version's P95 exceeds this

panels = [
    ("Baseline", base),
    ("Transient spikes (1% of frames)", spike),
    ("Sustained regression", reg),
]

x = np.arange(T)
fig, axes = plt.subplots(3, 1, figsize=(10, 7.2), sharex=True)
for ax, (name, d) in zip(axes, panels):
    ax.plot(x, np.clip(d, 0, YMAX), lw=0.7, color="#3a6ea5", alpha=0.9)
    pv = p95(d)
    shift = (pv - base_p95) / base_p95 * 100
    decision = "FLAGGED" if pv > thr_ms else "ignored"
    ax.axhline(thr_ms, color="black", ls="--", lw=1.2,
               label=f"flag threshold ({thr_ms:.0f} ms)")
    ax.axhline(pv, color="crimson", lw=1.8, label=f"this version P95 ({pv:.0f} ms)")
    ax.set_ylim(0, YMAX)
    ax.set_ylabel("Frame time (ms)")
    ax.set_title(f"{name}    P95 shift {shift:+.0f}%  →  {decision}",
                 loc="left", fontsize=10,
                 color=("crimson" if decision == "FLAGGED" else "black"))
    ax.legend(loc="upper left", fontsize=7, ncol=2)
    clipped = d > YMAX
    if clipped.any():
        for xi in x[clipped]:
            ax.annotate("", xy=(xi, YMAX - 1), xytext=(xi, YMAX - 12),
                        arrowprops=dict(arrowstyle="-|>", color="#c44", lw=1.0))
        ax.text(0.995, 0.62, f"↑ {clipped.sum()} rare spikes to ~{int(d.max())} ms",
                transform=ax.transAxes, ha="right", fontsize=8, color="#c44")

axes[-1].set_xlabel("Frame  (time →)")
fig.suptitle("Frame time over time: P95 ignores rare spikes, reacts to sustained shift",
             fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.97])
out = "figs/spike_separation_demo.png"
fig.savefig(out, dpi=140)

print(f"baseline P95 = {base_p95:.1f} ms   flag threshold = {thr_ms:.1f} ms\n")
print(f"{'scenario':32s} {'P95(ms)':>8} {'shift%':>8}  decision")
for name, d in panels:
    pv = p95(d)
    sh = (pv - base_p95) / base_p95 * 100
    print(f"{name:32s} {pv:8.1f} {sh:8.1f}  {'FLAGGED' if pv > thr_ms else 'ignored'}")
print("\nsaved", out)
