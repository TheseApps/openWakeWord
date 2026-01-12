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

# This example scripts runs openWakeWord in a simple web server receiving audio
# from a web page using websockets.

#######################################################################################

# Imports
import aiohttp
from aiohttp import web
import numpy as np
from openwakeword import Model
import resampy
import argparse
import json
import os
import datetime
import wave
import io
from pathlib import Path

# Define websocket handler
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Send loaded models
    await ws.send_str(json.dumps({"loaded_models": list(owwModel.models.keys())}))

    # Start listening for websocket messages
    async for msg in ws:
        # Get the sample rate of the microphone from the browser
        if msg.type == aiohttp.WSMsgType.TEXT:
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

            # Get openWakeWord predictions and set to browser client
            predictions = owwModel.predict(data)

            activations = []
            activation_scores = {}
            for key in predictions:
                # Filter out numeric indices from timer model (0-9 as strings)
                if key.isdigit():
                    continue
                    
                if predictions[key] >= 0.5:  # Standard threshold for wake words
                    activations.append(key)
                    activation_scores[key] = float(predictions[key])

            if activations:
                await ws.send_str(json.dumps({
                    "activations": activations,
                    "scores": activation_scores
                }))

    return ws

# Define static file handler
async def static_file_handler(request):
    return web.FileResponse('examples/web/streaming_client.html')




# Handle saving recordings
async def save_recording_handler(request):
    try:
        # Create the saved_clips directory if it doesn't exist
        if not os.path.exists('saved_clips'):
            os.makedirs('saved_clips')
            
        reader = await request.multipart()
        
        # Get the audio data field from the multipart request
        field = await reader.next()

        if field and field.name == 'audio':
            # Sanitize and generate filename if not provided by the client
            filename = field.filename or f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            filename = os.path.basename(filename) # Clean up the filename to avoid path issues
            file_path = os.path.join('saved_clips', filename)
            
            print(f"Attempting to save to: {file_path}")

            # Buffer the audio data in memory first
            audio_buffer = io.BytesIO()
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break # End of stream
                audio_buffer.write(chunk)
            
            audio_bytes = audio_buffer.getvalue()

            # --- Check if audio data was actually received ---
            if not audio_bytes:
                print("Received empty audio data for saving.")
                return web.Response(text="No audio data received in the upload.", status=400)

            # The browser sends WebM/Opus format, not raw PCM
            # Save as WebM first, then convert
            
            webm_path = file_path.replace('.wav', '.webm')
            
            try:
                # Save the WebM data with proper binary mode
                with open(webm_path, 'wb') as f:
                    f.write(audio_bytes)
                    f.flush()  # Ensure all data is written
                    os.fsync(f.fileno())  # Force write to disk
                
                print(f"Saved WebM recording to {webm_path} ({len(audio_bytes)} bytes)")
                
                # Small delay to ensure file is ready
                import time
                time.sleep(0.1)
                
                # Try to convert to WAV if ffmpeg is available
                try:
                    import subprocess
                    
                    # First, probe the file to see if it's valid
                    probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                                 'format=duration', '-of', 'json', webm_path]
                    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                    
                    if probe_result.returncode != 0:
                        print(f"WebM file appears to be invalid: {probe_result.stderr}")
                        return web.Response(text=f"Recording saved as {webm_path} but appears corrupted", status=500)
                    
                    # Convert to WAV
                    cmd = [
                        'ffmpeg', '-i', webm_path,
                        '-acodec', 'pcm_s16le',  # 16-bit PCM
                        '-ar', '16000',          # 16kHz
                        '-ac', '1',              # Mono
                        '-y',                    # Overwrite
                        file_path
                    ]
                    
                    print(f"Converting: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        os.remove(webm_path)  # Remove WebM after conversion
                        print(f"Successfully converted to WAV: {file_path}")
                        return web.Response(text=f"File saved as {file_path}")
                    else:
                        print(f"FFmpeg conversion failed: {result.stderr}")
                        return web.Response(text=f"File saved as {webm_path} (conversion failed)", status=500)
                        
                except FileNotFoundError:
                    print("FFmpeg not installed. Please install ffmpeg for WAV conversion.")
                    print("Download from: https://ffmpeg.org/download.html")
                    return web.Response(text=f"File saved as {webm_path} (install ffmpeg for WAV)")
                except Exception as e:
                    print(f"Conversion error: {e}")
                    return web.Response(text=f"File saved as {webm_path} (error during conversion)")

            except wave.Error as we:
                # Catches errors specific to the wave module (e.g., invalid parameters)
                error_msg = f"Error processing WAV file: {we}"
                print(error_msg)
                return web.Response(text=error_msg, status=500)
            
        else:
            # This block handles cases where the 'audio' field isn't found
            print("No audio field found in the request or field was None.")
            return web.Response(text="No audio field found in the request.", status=400)
    
    except Exception as e:
        # Catch any other unexpected errors during the process
        error_msg = f"An unexpected error occurred while saving recording: {str(e)}"
        print(error_msg)
        return web.Response(text=error_msg, status=500)



app = web.Application()
app.add_routes([
    web.get('/ws', websocket_handler), 
    web.get('/', static_file_handler),
    web.post('/save-recording', save_recording_handler)
])

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
        default='tflite',
        required=False
    )
    args=parser.parse_args()

    # Load openWakeWord models
    if args.model_path != "":
        owwModel = Model(
            wakeword_models=[args.model_path], 
            inference_framework=args.inference_framework,
            vad_threshold=0.1,  # Lower VAD threshold for better sensitivity
            device="cpu"
        )
    else:
        # Load default models from the project's models directory
        # Exclude timer model as it outputs numeric indices that cause false positives
        models_dir = Path(__file__).resolve().parents[2] / "models"
        exclude_models = ["melspectrogram.onnx", "embedding_model.onnx", "silero_vad.onnx", "timer_v0.1.onnx"]
        model_files = [str(p) for p in models_dir.glob("*.onnx") if p.name not in exclude_models]
        
        print(f"Loading wake word models: {[Path(m).stem for m in model_files]}")
        
        owwModel = Model(
            wakeword_models=model_files,
            inference_framework="onnx",
            vad_threshold=0,  # Disable VAD for now to avoid missing model issue
            device="cpu"
        )

    # Start webapp
    web.run_app(app, host='localhost', port=9000)