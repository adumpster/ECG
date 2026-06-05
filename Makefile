## Makefile for Pan-Tompkins QRS Detector

CC      = gcc
CFLAGS  = -Wall -O2 -std=c99
TARGET  = qrs_detector
SRCS    = main.c panTompkins.c
OBJS    = $(SRCS:.c=.o)

.PHONY: all clean run generate

## Default build
all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

## Generate a synthetic ECG test signal (requires Python 3)
generate:
	python3 generate_ecg.py ecg_samples.txt

## Run the detector on the generated sample file
run: $(TARGET) generate
	./$(TARGET) ecg_samples.txt detections.txt
	@echo ""
	@echo "--- Detection summary ---"
	@python3 -c "\
samples = open('ecg_samples.txt').readlines(); \
detections = open('detections.txt').readlines(); \
peaks = [i for i,v in enumerate(detections) if v.strip()=='1']; \
print(f'  Total samples   : {len(samples)}'); \
print(f'  R-peaks detected: {len(peaks)}'); \
intervals = [peaks[i+1]-peaks[i] for i in range(len(peaks)-1)]; \
avg_rr = sum(intervals)/len(intervals) if intervals else 0; \
bpm = 60*360/avg_rr if avg_rr else 0; \
print(f'  Avg RR interval : {avg_rr:.1f} samples ({avg_rr/360*1000:.1f} ms)'); \
print(f'  Estimated HR    : {bpm:.1f} BPM'); \
"

clean:
	rm -f $(OBJS) $(TARGET) ecg_samples.txt detections.txt
