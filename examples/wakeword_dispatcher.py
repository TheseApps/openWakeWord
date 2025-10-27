#!/usr/bin/env python3
import argparse
import datetime
import json
import logging
import os
import subprocess
import sys
import time

import numpy as np
import pyaudio

from openwakeword.model import Model


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("wakeword-dispatcher")


def spawn(cmd: list[str], env: dict | None = None, cwd: str | None = None) -> subprocess.Popen:
    return subprocess.Popen(cmd, env=env, cwd=cwd)


def create_default_routes(models_dir: str):
    return {
        # Second-stage listener: e.g., say "Alexa" then spawn another listener
        "alexa_v0.1": {
            "type": "second_stage",
            "command": [sys.executable, "-m", "examples.direct_wakeword_test_simple", "--inference_framework", "onnx", "--model_path", os.path.join(models_dir, "alexa_v0.1.onnx")]
        },
        # Fixed-length recorder examples: say "Hey Jarvis" / "Hey Mycroft" to capture 15s
        "hey_jarvis_v0.1": {
            "type": "fixed_record",
            "seconds": 15,
            "out_pattern": os.path.join("recordings", "note_{ts}.wav")
        },
        "hey_mycroft_v0.1": {
            "type": "fixed_record",
            "seconds": 15,
            "out_pattern": os.path.join("recordings", "note_{ts}.wav")
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Dispatch subprocesses/log on wakeword activations")
    parser.add_argument("--chunk_size", type=int, default=1280)
    parser.add_argument("--inference_framework", type=str, default="onnx", choices=["onnx", "tflite"])
    parser.add_argument("--model_path", type=str, default="", help="Single model to load; otherwise defaults")
    parser.add_argument("--routes", type=str, default="", help="Path to JSON mapping model->action")
    parser.add_argument("--log_dir", type=str, default="logs", help="Where to write activation logs")
    parser.add_argument("--threshold", type=float, default=0.35, help="Activation threshold")
    parser.add_argument("--debounce", type=float, default=1.0, help="Seconds to suppress repeats per model")
    parser.add_argument("--vad_threshold", type=float, default=0.0, help="Voice activity gate; 0 disables VAD")
    args = parser.parse_args()

    os.makedirs(args.log_dir, exist_ok=True)
    log_path = os.path.join(args.log_dir, f"dispatcher_{datetime.datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(file_handler)
    logger.info("starting wakeword dispatcher")

    # Load model(s)
    if args.model_path:
        oww = Model(wakeword_models=[args.model_path], inference_framework=args.inference_framework, vad_threshold=args.vad_threshold)
    else:
        oww = Model(inference_framework=args.inference_framework, vad_threshold=args.vad_threshold)

    # Audio input
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=args.chunk_size)

    # Routing configuration
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    routes = create_default_routes(models_dir)
    if args.routes and os.path.exists(args.routes):
        with open(args.routes, "r", encoding="utf-8") as f:
            routes.update(json.load(f))

    last_activation: dict[str, float] = {}

    logger.info("loaded models: %s", list(oww.models.keys()))
    logger.info("routes for: %s", list(routes.keys()))

    try:
        while True:
            audio = np.frombuffer(stream.read(args.chunk_size, exception_on_overflow=False), dtype=np.int16)
            preds = oww.predict(audio)

            now = time.time()
            for key, score in preds.items():
                if score >= args.threshold:
                    last = last_activation.get(key, 0.0)
                    if now - last < args.debounce:
                        continue
                    last_activation[key] = now

                    logger.info("activation: %s score=%.3f", key, float(score))

                    route = None
                    # match by exact model key or by parent model name
                    if key in routes:
                        route = routes[key]
                    else:
                        # sometimes keys are class labels, map back to parent
                        parent = oww.get_parent_model_from_label(key)
                        if parent and parent in routes:
                            route = routes[parent]

                    if not route:
                        continue

                    rtype = route.get("type")
                    if rtype == "second_stage":
                        cmd = route.get("command", [])
                        if cmd:
                            spawn(cmd)
                            logger.info("spawned second_stage: %s", cmd)
                    elif rtype == "fixed_record":
                        seconds = int(route.get("seconds", 15))
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        out_pattern = route.get("out_pattern", os.path.join("recordings", "clip_{ts}.wav"))
                        out_path = out_pattern.replace("{ts}", ts)
                        cmd = [sys.executable, "-m", "examples.record_to_wav", "--mode", "fixed", "--seconds", str(seconds), "--out", out_path]
                        spawn(cmd)
                        logger.info("spawned fixed_record: %s", out_path)
                    elif rtype == "command":
                        cmd = route.get("command", [])
                        if cmd:
                            spawn(cmd)
                            logger.info("spawned command: %s", cmd)

    except KeyboardInterrupt:
        logger.info("stopping dispatcher")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()


