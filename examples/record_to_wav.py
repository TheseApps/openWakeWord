#!/usr/bin/env python3
import argparse
import datetime
import os
import wave
import sys

import numpy as np
import pyaudio


def record_fixed_length(duration_sec: int, out_path: str, rate: int = 16000, channels: int = 1, chunk: int = 1024):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)

    frames = []
    samples_needed = duration_sec * rate
    samples_collected = 0

    try:
        while samples_collected < samples_needed:
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
            samples_collected += len(data) // 2  # 16-bit
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))


def record_until_silence(out_path: str, rate: int = 16000, channels: int = 1, chunk: int = 1024, silence_ms: int = 1200, rms_thresh: float = 300.0, max_sec: int = 30):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)

    frames = []
    silence_target_chunks = max(1, (silence_ms * rate) // (1000 * chunk))
    silent_chunks = 0
    total_chunks_limit = max_sec * rate // chunk

    try:
        while True:
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
            audio = np.frombuffer(data, dtype=np.int16)
            rms = float(np.sqrt(np.mean(np.square(audio.astype(np.float32)))))
            if rms < rms_thresh:
                silent_chunks += 1
            else:
                silent_chunks = 0

            if silent_chunks >= silence_target_chunks or len(frames) >= total_chunks_limit:
                break
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))


def main():
    parser = argparse.ArgumentParser(description="Record microphone to WAV file.")
    parser.add_argument("--out", type=str, default=None, help="Output WAV file path. Default under ./recordings/")
    parser.add_argument("--mode", type=str, choices=["fixed", "silence"], default="fixed", help="Recording mode")
    parser.add_argument("--seconds", type=int, default=15, help="Duration for fixed mode")
    parser.add_argument("--silence_ms", type=int, default=1200, help="Trailing silence to stop (silence mode)")
    parser.add_argument("--rms_thresh", type=float, default=300.0, help="Silence RMS threshold")
    args = parser.parse_args()

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join("recordings")
    default_name = f"rec_{args.mode}_{ts}.wav"
    out_path = args.out or os.path.join(out_dir, default_name)

    if args.mode == "fixed":
        record_fixed_length(args.seconds, out_path)
        print(f"Saved fixed-length recording to {out_path}")
    else:
        record_until_silence(out_path, silence_ms=args.silence_ms, rms_thresh=args.rms_thresh)
        print(f"Saved silence-terminated recording to {out_path}")


if __name__ == "__main__":
    main()


