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

# This example script runs openWakeWord in a web server that:
# 1. Detects wake words from streaming audio
# 2. Records speech after wake word until ENGAGE, pause, or timeout
# 3. Saves the recording for processing

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
import wave
import datetime

# Define websocket handler
async def websocket_handler(request):
    print(f"New client connection from {request.remote}")
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print(f"WebSocket connection prepared for {request.remote}")

    # Send loaded models
    model_list = list(owwModel.models.keys())
    await ws.send_str(json.dumps({"loaded_models": model_list}))
    print(f"Sent model list: {model_list}")

    # Constants for recording behavior
    PAUSE_THRESHOLD = 2.5  # seconds
    MAX_RECORDING_TIME = 12  # seconds
    SILENCE_THRESHOLD = 500  # audio level below which is considered silence
    
    # Variables to track recording state
    is_recording = False
    recording_buffer = []
    last_audio_time = None
    recording_start_time = None
    detected_wake_word = None
    sample_rate = None  # Will be set by client
    
    # Start listening for websocket messages
    try:
        async for msg in ws:
            # Get the sample rate of the microphone from the browser
            if msg.type == aiohttp.WSMsgType.TEXT:
                print(f"Received text message: {msg.data[:50]}")
                sample_rate = int(msg.data)
                print(f"Client sample rate set to: {sample_rate}Hz")
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

                # Get openWakeWord predictions
                predictions = owwModel.predict(data)

                # Check for wake word activations
                activations = []
                for key in predictions:
                    if predictions[key] >= 0.5:
                        activations.append(key)
                        print(f"Detected: {key}")
                
                # Start recording if wake word detected and not already recording
                if activations and not is_recording:
                    detected_wake_word = activations[0]  # Use the first detected wake word
                    is_recording = True
                    recording_buffer = [data]  # Include the current audio chunk
                    recording_start_time = time.time()
                    last_audio_time = time.time()
                    print(f"Wake word '{detected_wake_word}' detected! Started recording.")
                    await ws.send_str(json.dumps({"status": "recording_started", 
                                               "wake_word": detected_wake_word}))
                
                # Process audio if recording is active
                elif is_recording:
                    current_time = time.time()
                    recording_buffer.append(data)
                    
                    # Check for "ENGAGE" in audio (processed through wake word models)
                    engage_detected = False
                    # This is a simple approach - in practice, you might need a dedicated model for "ENGAGE"
                    if "ENGAGE" in str(activations) or "engage" in str(activations):
                        engage_detected = True
                        print("ENGAGE command detected!")
                    
                    # Check for timeout
                    timeout_detected = current_time - recording_start_time > MAX_RECORDING_TIME
                    if timeout_detected:
                        print(f"Recording stopped: {MAX_RECORDING_TIME}s timeout")
                    
                    # Check for pause/silence
                    audio_level = np.abs(data).mean()
                    pause_detected = False
                    if audio_level < SILENCE_THRESHOLD:
                        if last_audio_time and current_time - last_audio_time > PAUSE_THRESHOLD:
                            pause_detected = True
                            print(f"Recording stopped: {PAUSE_THRESHOLD}s pause detected")
                    else:
                        # Reset the silence timer when audio is detected
                        last_audio_time = current_time
                    
                    # If any stop condition is met, save the recording and reset
                    if engage_detected or timeout_detected or pause_detected:
                        # Save the recording
                        filename = await save_recording(recording_buffer, detected_wake_word)
                        
                        # Reset recording state
                        is_recording = False
                        recording_buffer = []
                        detected_wake_word = None
                        
                        # Determine the trigger that ended recording
                        end_trigger = "engage" if engage_detected else "timeout" if timeout_detected else "pause"
                        
                        # Send status to client
                        await ws.send_str(json.dumps({
                            "status": "recording_stopped",
                            "trigger": end_trigger,
                            "filename": filename
                        }))
                
                # Send activations to client (whether recording or not)
                if activations:
                    await ws.send_str(json.dumps({"activations": activations}))
    except Exception as e:
        print(f"Error in websocket handler: {str(e)}")
    finally:
        # Clean up any resources, close connection gracefully
        print(f"WebSocket connection closed for {request.remote}")
    
    return ws

# Function to save recorded audio to a WAV file
async def save_recording(audio_chunks, wake_word):
    try:
        # Create saved_clips directory if it doesn't exist
        if not os.path.exists("saved_clips"):
            os.makedirs("saved_clips")
        
        # Generate unique filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saved_clips/{wake_word}_{timestamp}.wav"
        
        # Combine all audio chunks
        combined_audio = np.concatenate(audio_chunks)
        
        # Save as WAV file (16-bit, 16kHz, mono)
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(16000)  # 16kHz
            wf.writeframes(combined_audio.tobytes())
        
        print(f"Saved recording to {filename}")
        return filename
    except Exception as e:
        print(f"Error saving recording: {str(e)}")
        return f"error_{timestamp}.wav"  # Return a placeholder filename in case of error

# Define static file handler
async def static_file_handler(request):
    # Use the correct path relative to the project root
    return web.FileResponse('examples/web/wake_record_client.html')

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

    print("Starting openWakeWord recording server...")
    
    # Check if user provided a specific model path argument
    if args.model_path != "":
        print(f"Loading model from path: {args.model_path}")
        owwModel = Model(wakeword_models=[args.model_path],
                         inference_framework=args.inference_framework,
                         vad_threshold=0.3)
    else:
        print(f"Loading {len(local_onnx_model_paths)} models from local directory")
        owwModel = Model(wakeword_models=local_onnx_model_paths,
                         inference_framework=args.inference_framework,
                         vad_threshold=0.3)

    print(f"Loaded models: {list(owwModel.models.keys())}")
    print("Server will automatically record after wake word detection")
    print("Recording will end with ENGAGE, a 2.5s pause, or after 12 seconds")
    
    # Start webapp
    web.run_app(app, host='localhost', port=9000) 