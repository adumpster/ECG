#!/usr/bin/env python3
"""
generate_ecg.py
Generates a synthetic ECG signal sampled at 360 Hz and writes it to a plain-
text file compatible with the Pan-Tompkins QRS detector.

Each line contains one integer sample value (the detector's default dataType
is 'int').  The signal includes:
  - A realistic PQRST morphology constructed from Gaussian pulses
  - Configurable heart rate (BPM) and duration (seconds)
  - Mild Gaussian noise to simulate a real sensor environment

Usage:
    python3 generate_ecg.py [output_file] [bpm] [duration_sec]

Defaults: output_file=ecg_samples.txt, bpm=75, duration_sec=10
"""

import math
import random
import sys

# ── Configuration ────────────────────────────────────────────────────────────
FS          = 360          # sampling frequency (must match #define FS in panTompkins.c)
OUTPUT_FILE = "ecg_samples.txt"
BPM         = 75           # heart rate
DURATION    = 10           # seconds of signal
AMPLITUDE   = 1000         # R-peak amplitude (integer units)
NOISE_STD   = 20           # standard-deviation of additive Gaussian noise

# Override via command-line args
if len(sys.argv) > 1: OUTPUT_FILE = sys.argv[1]
if len(sys.argv) > 2: BPM         = int(sys.argv[2])
if len(sys.argv) > 3: DURATION    = int(sys.argv[3])
# ─────────────────────────────────────────────────────────────────────────────


def gaussian(t, center, sigma, amplitude):
    """Single Gaussian pulse centred at `center`."""
    return amplitude * math.exp(-0.5 * ((t - center) / sigma) ** 2)


def pqrst(t, beat_center):
    """
    Synthetic PQRST complex centred at beat_center (seconds).
    Offsets and widths are expressed in seconds and approximate real ECG ratios.
    """
    sample = 0.0
    # P wave  (+80 ms before R, width ≈ 40 ms, amp = 10 % of R)
    sample += gaussian(t, beat_center - 0.080,  0.020, AMPLITUDE * 0.10)
    # Q wave  (−25 ms before R, narrow negative dip, amp = −5 % of R)
    sample += gaussian(t, beat_center - 0.025,  0.008, AMPLITUDE * -0.05)
    # R wave  (the QRS peak itself)
    sample += gaussian(t, beat_center,           0.010, AMPLITUDE)
    # S wave  (+25 ms after R, narrow negative dip, amp = −8 % of R)
    sample += gaussian(t, beat_center + 0.025,   0.008, AMPLITUDE * -0.08)
    # T wave  (+200 ms after R, width ≈ 60 ms, amp = 20 % of R)
    sample += gaussian(t, beat_center + 0.200,   0.030, AMPLITUDE * 0.20)
    return sample


def generate_ecg(fs, bpm, duration):
    """Return a list of integer ECG samples."""
    n_samples    = int(fs * duration)
    rr_interval  = 60.0 / bpm          # seconds between beats
    beat_times   = []
    t = rr_interval                    # first beat at 1 RR-interval in
    while t < duration:
        beat_times.append(t)
        t += rr_interval

    samples = []
    for idx in range(n_samples):
        t = idx / fs
        value = 0.0
        for beat in beat_times:
            # Only evaluate beats whose influence reaches this sample
            if abs(t - beat) < 0.5:
                value += pqrst(t, beat)
        # Add Gaussian noise
        value += random.gauss(0, NOISE_STD)
        samples.append(int(round(value)))

    return samples


def main():
    random.seed(42)   # reproducible output
    print(f"Generating synthetic ECG: {BPM} BPM, {DURATION}s @ {FS} Hz -> {OUTPUT_FILE}")
    samples = generate_ecg(FS, BPM, DURATION)
    with open(OUTPUT_FILE, "w") as f:
        for s in samples:
            f.write(f"{s}\n")
    print(f"  Written {len(samples)} samples.")


if __name__ == "__main__":
    main()
