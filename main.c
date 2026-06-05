/**
 * main.c
 * Entry point for the Pan-Tompkins QRS detector.
 *
 * Usage:
 *   ./qrs_detector <input_file> <output_file>
 *
 * The input file must contain one integer ECG sample per line (ASCII).
 * The output file will contain one integer per line: 1 if a QRS (R-peak)
 * was detected at that sample, 0 otherwise.
 *
 * Example:
 *   ./qrs_detector ecg_samples.txt detections.txt
 */

#include <stdio.h>
#include <stdlib.h>
#include "panTompkins.h"

/* Declared in panTompkins.c */
void init(char file_in[], char file_out[]);

int main(int argc, char *argv[])
{
    if (argc != 3)
    {
        fprintf(stderr, "Usage: %s <input_file> <output_file>\n", argv[0]);
        fprintf(stderr, "  input_file  : plain-text file, one integer ECG sample per line\n");
        fprintf(stderr, "  output_file : results file (1 = R-peak detected, 0 = no peak)\n");
        return EXIT_FAILURE;
    }

    printf("Pan-Tompkins QRS Detector\n");
    printf("  Input  : %s\n", argv[1]);
    printf("  Output : %s\n", argv[2]);
    printf("  Sampling frequency : %d Hz\n", 360);
    printf("  Integration window : %d samples (%.0f ms)\n\n", 20, 20 * 1000.0 / 360.0);

    /* Open files and perform any hardware/serial setup */
    init(argv[1], argv[2]);

    /* Run the detector until all samples are consumed */
    panTompkins();

    printf("Detection complete. Results written to: %s\n", argv[2]);
    return EXIT_SUCCESS;
}
