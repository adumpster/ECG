# Pan-Tompkins QRS Detector

A portable, real-time **QRS complex / R-peak detector** for ECG signals, based on the classic 1985 paper by Jiapu Pan and Willis J. Tompkins.

> *"A Real-Time QRS Detection Algorithm"* — IEEE Transactions on Biomedical Engineering, Vol. BME-32, No. 3, March 1985.

This repository contains an ANSI-C implementation by **Rafael de Moura Moreira**, a command-line driver, a GNU Makefile, and a Python script to generate synthetic test signals.

---

## Table of Contents

- [Algorithm Overview](#algorithm-overview)
- [Repository Structure](#repository-structure)
- [Requirements](#requirements)
- [Building](#building)
- [Usage](#usage)
- [Testing with Synthetic Data](#testing-with-synthetic-data)
- [Porting to Embedded / Other Platforms](#porting-to-embedded--other-platforms)
- [Key Configuration Parameters](#key-configuration-parameters)
- [License](#license)

---

## Algorithm Overview

The Pan-Tompkins algorithm detects QRS complexes (the sharp spike in an ECG waveform corresponding to ventricular depolarisation — the R-peak) in real time using a pipeline of digital filters followed by adaptive thresholding.

```
Raw ECG
   │
   ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────────┐    ┌──────────────────┐
│ DC Block │───▶│ Low-pass │───▶│High-pass │───▶│ Derivative │───▶│ Square + Integr. │
│          │    │  15 Hz   │    │   5 Hz   │    │            │    │  (moving window) │
└──────────┘    └──────────┘    └──────────┘    └────────────┘    └──────────────────┘
                                                                            │
                                                                            ▼
                                                               Adaptive Thresholding
                                                               + T-wave discrimination
                                                               + RR-interval averaging
                                                                            │
                                                                            ▼
                                                                   QRS Detection (0/1)
```

**Key stages:**

| Stage | Purpose |
|---|---|
| DC Block | Removes baseline wander (not in the original paper; can be disabled) |
| Low-pass (15 Hz) | Reduces high-frequency noise |
| High-pass (5 Hz) | Removes low-frequency drift |
| Derivative | Highlights the steep slope of the QRS complex |
| Squaring | Makes all values positive; amplifies larger slopes non-linearly |
| Moving-window integrator | Smooths the signal to produce a clean envelope |
| Adaptive thresholds | Two thresholds (signal & integrator) self-update to track amplitude changes |
| T-wave discrimination | Hard 200 ms and soft 360 ms refractory periods prevent T-wave false positives |
| RR averaging | Two 8-sample RR buffers detect irregular heart rate and relax thresholds accordingly |
| Back search | If no QRS is found for too long, a secondary threshold re-examines recent candidates |

---

## Repository Structure

```
.
├── panTompkins.h      # Header: dataType typedef, function declarations
├── panTompkins.c      # Core algorithm: init(), input(), output(), panTompkins()
├── main.c             # CLI driver: parses arguments, calls init() + panTompkins()
├── generate_ecg.py    # Synthetic ECG generator (Python 3, no dependencies)
├── Makefile           # Build, run, and clean targets
└── README.md          # This file
```

---

## Requirements

**To build the C program:**
- GCC (or any C99-compliant compiler)
- GNU Make

**To generate synthetic test data:**
- Python 3.6+ (standard library only — no pip packages needed)

---

## Building

```bash
make
```

This compiles `main.c` and `panTompkins.c` into the `qrs_detector` binary with `-Wall -Wextra -O2`.

---

## Usage

```
./qrs_detector <input_file> <output_file>
```

| Argument | Description |
|---|---|
| `input_file` | Plain-text file containing **one integer ECG sample per line** |
| `output_file` | Output file — one integer per line: `1` = R-peak detected, `0` = no peak |

**Example:**

```bash
./qrs_detector ecg_samples.txt detections.txt
```

**Sample output lines in `detections.txt`:**

```
0
0
0
1    ← R-peak detected at this sample
0
0
...
```

---

## Testing with Synthetic Data

The included Python script generates a realistic PQRST waveform at 360 Hz with configurable heart rate and duration:

```bash
# Generate a 10-second ECG at 75 BPM (default)
python3 generate_ecg.py ecg_samples.txt

# Or specify BPM and duration
python3 generate_ecg.py ecg_samples.txt 60 20   # 60 BPM, 20 seconds

# Build, generate, run and print a summary all in one step
make run
```

The `make run` target prints a summary like:

```
Pan-Tompkins QRS Detector
  Input  : ecg_samples.txt
  Output : detections.txt
  Sampling frequency : 360 Hz
  Integration window : 20 samples (56 ms)

Detection complete. Results written to: detections.txt

--- Detection summary ---
  Total samples   : 3600
  R-peaks detected: 12
  Avg RR interval : 288.0 samples (800.0 ms)
  Estimated HR    : 75.0 BPM
```

---

## Porting to Embedded / Other Platforms

The algorithm itself is pure ANSI C. Only three functions need to be adapted:

### `init()` — `panTompkins.c` + `panTompkins.h`
Replace file-open logic with hardware initialisation (UART, SPI, ADC setup, etc.).
Update the function signature in both files to match the parameters your platform needs.

```c
// Example for a bare-metal system — no parameters needed:
void init(void)
{
    adc_init();
    uart_init(115200);
}
```

### `input()` — `panTompkins.c`
Replace `fscanf` with a call to your ADC, serial port, or DMA buffer.
Return `NOSAMPLE` when no data is available (online mode) or at end-of-stream (offline mode).

```c
dataType input(void)
{
    return adc_read_blocking();   // blocks until a sample arrives
}
```

### `output()` — `panTompkins.c`
Replace `fprintf` with whatever action fits your application:
- Toggle a GPIO / blink an LED
- Transmit an RR-interval over UART
- Increment a beat counter
- Call a feature-extraction function

```c
void output(int qrs_detected)
{
    if (qrs_detected)
        led_toggle();
}
```

### Remove `<stdio.h>` and `fclose()`
Delete the `#include <stdio.h>` and the two `fclose()` calls at the end of `panTompkins()` if your platform has no file system.

---

## Key Configuration Parameters

All in `panTompkins.c`:

| `#define` | Default | Description |
|---|---|---|
| `FS` | `360` | Sampling frequency in Hz. **Must match your ADC rate.** |
| `WINDOWSIZE` | `20` | Integration window in samples (`FS × 0.15` ≈ 150 ms recommended) |
| `BUFFSIZE` | `600` | Circular buffer size. Must hold > 1.66 × longest expected RR interval. |
| `NOSAMPLE` | `-32000` | Sentinel value signalling end of data. Must be outside the valid ADC range. |
| `DELAY` | `22` | Filter group delay in samples. Set to `0` to preserve output length. |

In `panTompkins.h`:

| `typedef` | Default | Description |
|---|---|---|
| `dataType` | `int` | Change to `float`, `int16_t`, `uint16_t`, etc. to match your ADC output. |

---

## License

MIT License — Copyright (c) 2018 Rafael de Moura Moreira.
See source files for full license text.
