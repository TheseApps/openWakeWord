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
                if predictions[key] >= 0.3:  # Lowered threshold for better detection
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
        
        # Get the audio data
        field = await reader.next()
        if field and field.name == 'audio':
            # Get and sanitize filename
            filename = field.filename
            if not filename:
                filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                
            # Clean up the filename to avoid path issues
            filename = os.path.basename(filename)
            
            # Create the full path
            file_path = os.path.join('saved_clips', filename)
            print(f"Saving to: {file_path}")
            
            # Write the file data in chunks
            with open(file_path, 'wb') as f:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    f.write(chunk)
            
            print(f"Successfully saved recording to {file_path}")
            return web.Response(text=f"File saved as {file_path}")
        else:
            print("No audio field found in request")
            return web.Response(text="No audio field found in request", status=400)
    
    except Exception as e:
        error_msg = f"Error saving recording: {str(e)}"
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
        # Load default models
        owwModel = Model(
            vad_threshold=0.1,  # Lower VAD threshold for better sensitivity
            device="cpu"
        )

    # Start webapp
    web.run_app(app, host='localhost', port=9000)