# Copyright 2023 David Scripka. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#######################################################################################

# This modified server implements continuous listening until "ENGAGE!" or a pause
# is detected, with a 12-second maximum timeout.

#######################################################################################

# Imports
import aiohttp
from aiohttp import web
import numpy as np
from openwakeword.model import Model
import resampy
import argparse
import json
import asyncio
import websockets
import logging
import time
import os
import datetime

# Define websocket handler
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Send loaded models
    await ws.send_str(json.dumps({"loaded_models": list(owwModel.models.keys())}))
    
    # Define constants for our recording behavior
    PAUSE_THRESHOLD = 2.5  # seconds
    MAX_LISTEN_TIME = 12   # seconds
    ENGAGE_KEYWORD = "ENGAGE!"
    SILENCE_THRESHOLD = 500  # audio level below which is considered silence
    
    # Variables to track recording state
    is_recording = False
    recording_buffer = []
    last_audio_time = None
    recording_start_time = None
    
    # Start listening for websocket messages
    async for msg in ws:
        # Get the sample rate of the microphone from the browser
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data.startswith('{"command":'):
                # Process command from client
                try:
                    command_data = json.loads(msg.data)
                    if command_data.get("command") == "start_listening":
                        print("Command received: start_listening")
                        is_recording = True
                        recording_buffer = []
                        recording_start_time = time.time()
                        await ws.send_str(json.dumps({"status": "listening", "message": "I'm listening..."}))
                        print("I'm listening...")
                except json.JSONDecodeError:
                    print(f"Invalid JSON: {msg.data}")
            else:
                # Assume it's the sample rate
                sample_rate = int(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print(f"WebSocket error: {ws.exception()}")
        else:
            # Get audio data from websocket
            audio_bytes = msg.data

            # Add extra bytes of silence if needed
            if len(msg.data) % 2 == 1:
                audio_bytes += (b'\x00')

            # Convert audio to correct format and sample rate
            data = np.frombuffer(audio_bytes, dtype=np.int16)
            if sample_rate != 16000:
                data = resampy.resample(data, sample_rate, 16000)
                
            # Process audio for continuous recording if we're in recording mode
            if is_recording:
                current_time = time.time()
                
                # Check for timeout
                if current_time - recording_start_time > MAX_LISTEN_TIME:
                    is_recording = False
                    print(f"Stopped recording: reached maximum time of {MAX_LISTEN_TIME} seconds")
                    await ws.send_str(json.dumps({
                        "status": "timeout", 
                        "message": f"Listening timeout after {MAX_LISTEN_TIME} seconds"
                    }))
                    continue
                
                # Check for silence/pause
                audio_level = np.abs(data).mean()
                if audio_level < SILENCE_THRESHOLD:
                    if last_audio_time and current_time - last_audio_time > PAUSE_THRESHOLD:
                        is_recording = False
                        print(f"Stopped recording: detected {PAUSE_THRESHOLD}s pause")
                        await ws.send_str(json.dumps({
                            "status": "pause_detected", 
                            "message": f"Detected pause of {PAUSE_THRESHOLD} seconds"
                        }))
                        continue
                else:
                    # Reset the last audio time when we hear something
                    last_audio_time = current_time
                
                # Add to recording buffer
                recording_buffer.append(data)
                
            # Get openWakeWord predictions and set to browser client
            predictions = owwModel.predict(data)

            activations = []
            for key in predictions:
                if predictions[key] >= 0.5:
                    activations.append(key)
                    print(f"Detected: {key}")

            if activations != []:
                # Check if "ENGAGE!" was detected
                if "ENGAGE!" in str(activations):
                    if is_recording:
                        is_recording = False
                        print("Stopped recording: ENGAGE detected")
                        await ws.send_str(json.dumps({
                            "status": "engage_detected", 
                            "message": "ENGAGE command detected!"
                        }))
                
                # Send the activations to client
                await ws.send_str(json.dumps({"activations": activations}))

    return ws

# Define static file handler
async def static_file_handler(request):
    # Use the correct path relative to the project root
    return web.FileResponse('examples/web/listening_client.html')

app = web.Application()
app.add_routes([web.get('/ws', websocket_handler), web.get('/', static_file_handler)])

if __name__ == '__main__':
    # Parse CLI arguments
    parser=argparse.ArgumentParser()
    parser.add_argument(
        "--chunk_size",
        help="How much audio (in number of samples) to predict on at once",
        type=int,
        default=1280,
        required=False
    )
    parser.add_argument(
        "--model_path",
        help="The path of a specific model to load",
        type=str,
        default="",
        required=False
    )
    parser.add_argument(
        "--inference_framework",
        help="The inference framework to use (either 'onnx' or 'tflite'",
        type=str,
        default='onnx',
        required=False
    )
    args=parser.parse_args()

    # --- Load specific pre-trained models from the local ./models directory ---
    # Define the list of relative paths to the desired ONNX models
    local_onnx_model_paths = [
        "models/alexa_v0.1.onnx",
        "models/hey_mycroft_v0.1.onnx",
        "models/hey_jarvis_v0.1.onnx",
        "models/hey_rhasspy_v0.1.onnx",
        "models/timer_v0.1.onnx",
        "models/weather_v0.1.onnx"
    ]
    
    print("Starting openWakeWord listening server...")
    
    # Check if user provided a specific model path argument
    if args.model_path != "":
        # If user provided a path, use that one
        print(f"Loading model from path: {args.model_path}")
        # Also explicitly pass vad_threshold=0.3 to detect speech
        owwModel = Model(wakeword_models=[args.model_path],
                         inference_framework=args.inference_framework,
                         vad_threshold=0.3)
    else:
        # Otherwise, load the specific models from our local list
        print(f"Loading {len(local_onnx_model_paths)} models from local directory")
        # Also explicitly pass vad_threshold=0.3 to detect speech
        owwModel = Model(wakeword_models=local_onnx_model_paths,
                         inference_framework=args.inference_framework,
                         vad_threshold=0.3)
    
    print(f"Loaded models: {list(owwModel.models.keys())}")
    print("To use: Open http://localhost:9000 in your browser")
    print("The server will listen continuously until it detects 'ENGAGE!' or a 2.5s pause")
    
    # Start webapp
    web.run_app(app, host='localhost', port=9000) 