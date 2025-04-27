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

# This example script runs openWakeWord in a simple web server that:
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
import logging
import time
import os
import wave
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define websocket handler
async def websocket_handler(request):
    logger.info(f"New client connection from {request.remote}")
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    logger.info(f"WebSocket connection prepared for {request.remote}")

    # Send loaded models
    model_list = list(owwModel.models.keys())
    await ws.send_str(json.dumps({"loaded_models": model_list}))
    logger.info(f"Sent model list: {', '.join(model_list)}")

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
    
    try:
        # Start listening for websocket messages
        async for msg in ws:
            # Get the sample rate of the microphone from the browser
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    sample_rate = int(msg.data)
                    logger.info(f"Client sample rate set to: {sample_rate}Hz")
                except ValueError:
                    logger.warning(f"Received invalid sample rate: {msg.data}")
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
                break
            elif msg.type == aiohttp.WSMsgType.CLOSE:
                logger.info("WebSocket closed by client")
                break
            else:
                # Get audio data from websocket
                try:
                    audio_bytes = msg.data

                    # Add extra bytes of silence if needed
                    if len(msg.data) % 2 == 1:
                        audio_bytes += (b'\x00')

                    # Convert audio to correct format and sample rate
                    data = np.frombuffer(audio_bytes, dtype=np.int16)
                    if sample_rate and sample_rate != 16000:
                        data = resampy.resample(data, sample_rate, 16000)

                    # Get openWakeWord predictions
                    predictions = owwModel.predict(data)

                    # Check for wake word activations
                    activations = []
                    for key in predictions:
                        if predictions[key] >= 0.5:
                            activations.append(key)
                    
                    # If we have activations, send them to the client
                    if activations:
                        logger.info(f"Detected: {', '.join(activations)}")
                        await ws.send_str(json.dumps({"activations": activations}))
                    
                    # Start recording if wake word detected and not already recording
                    if activations and not is_recording:
                        detected_wake_word = activations[0]  # Use the first detected wake word
                        is_recording = True
                        recording_buffer = [data]  # Include the current audio chunk
                        recording_start_time = time.time()
                        last_audio_time = time.time()
                        logger.info(f"Wake word '{detected_wake_word}' detected! Started recording.")
                        await ws.send_str(json.dumps({"status": "recording_started", 
                                                    "wake_word": detected_wake_word}))
                    
                    # Process audio if recording is active
                    elif is_recording:
                        current_time = time.time()
                        recording_buffer.append(data)
                        
                        # Check for "ENGAGE" in audio
                        engage_detected = False
                        if any("ENGAGE" in str(key) or "engage" in str(key) for key in activations):
                            engage_detected = True
                            logger.info("ENGAGE command detected!")
                        
                        # Check for timeout
                        timeout_detected = current_time - recording_start_time > MAX_RECORDING_TIME
                        if timeout_detected:
                            logger.info(f"Recording stopped: {MAX_RECORDING_TIME}s timeout")
                        
                        # Check for pause/silence
                        audio_level = np.abs(data).mean()
                        pause_detected = False
                        if audio_level < SILENCE_THRESHOLD:
                            if last_audio_time and current_time - last_audio_time > PAUSE_THRESHOLD:
                                pause_detected = True
                                logger.info(f"Recording stopped: {PAUSE_THRESHOLD}s pause detected")
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
                            
                            # Determine the trigger that ended recording
                            end_trigger = "engage" if engage_detected else "timeout" if timeout_detected else "pause"
                            
                            # Send status to client
                            await ws.send_str(json.dumps({
                                "status": "recording_stopped",
                                "trigger": end_trigger,
                                "filename": filename
                            }))
                            logger.info(f"Recording saved to {filename} (trigger: {end_trigger})")
                except Exception as e:
                    logger.error(f"Error processing audio: {str(e)}")
    except Exception as e:
        logger.error(f"WebSocket handler error: {str(e)}")
    finally:
        if not ws.closed:
            await ws.close()
        logger.info(f"WebSocket connection closed for {request.remote}")
    
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
        
        logger.info(f"Saved recording to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving recording: {str(e)}")
        return f"error_{timestamp}.wav"  # Return a placeholder filename in case of error

# Simple HTML page that streams audio continuously
SIMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>openWakeWord Simple Listener</title>
  <style>
    body {
      text-align: center;
      font-family: Arial, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    button {
      padding: 15px 30px;
      font-size: 18px;
      background-color: #03A9F4;
      border: none;
      border-radius: 4px;
      color: white;
      cursor: pointer;
      outline: none;
      transition: background-color 0.3s;
    }
    button.active {
      background-color: #F44336;
    }
    .status {
      margin: 20px 0;
      padding: 10px;
      background-color: #f0f0f0;
      border-radius: 4px;
    }
    .wake-word {
      padding: 5px 10px;
      background-color: #4CAF50;
      color: white;
      border-radius: 4px;
      margin: 2px;
      display: inline-block;
      animation: flash 1s ease-out;
    }
    @keyframes flash {
      0% { opacity: 0.5; }
      50% { opacity: 1; }
      100% { opacity: 0.5; }
    }
    #wakeWordContainer {
      margin-top: 20px;
    }
    #logArea {
      height: 200px;
      overflow-y: auto;
      border: 1px solid #ddd;
      padding: 10px;
      margin-top: 20px;
      text-align: left;
      font-family: monospace;
      background-color: #f9f9f9;
    }
  </style>
</head>
<body>
  <h1>openWakeWord Simple Listener</h1>
  <p>This page continuously listens for wake words and records until:</p>
  <ul style="text-align: left;">
    <li>You say "ENGAGE" to stop recording</li>
    <li>After a 2.5 second pause in speech</li>
    <li>After 12 seconds of total recording time</li>
  </ul>
  
  <button id="startButton">Start Listening</button>
  <div class="status" id="statusText">Not connected</div>
  
  <div id="wakeWordContainer">
    <h2>Wake Words</h2>
    <div id="modelsList"></div>
  </div>
  
  <h2>Activity Log</h2>
  <div id="logArea"></div>
  
  <script>
    // Elements
    const startButton = document.getElementById('startButton');
    const statusText = document.getElementById('statusText');
    const modelsList = document.getElementById('modelsList');
    const logArea = document.getElementById('logArea');
    
    // Variables
    let ws = null;
    let audioContext = null;
    let audioStream = null;
    let sampleRate = null;
    let isListening = false;
    let processorNode = null;
    
    // Add log message
    function log(message) {
      const time = new Date().toLocaleTimeString();
      const logEntry = document.createElement('div');
      logEntry.textContent = `${time}: ${message}`;
      logArea.appendChild(logEntry);
      logArea.scrollTop = logArea.scrollHeight;
    }
    
    // Show wake word detection
    function showWakeWord(word) {
      const element = document.createElement('div');
      element.className = 'wake-word';
      element.textContent = word;
      
      // Add to the UI
      modelsList.appendChild(element);
      
      // Remove after animation
      setTimeout(() => {
        element.style.opacity = '0';
        element.style.transition = 'opacity 0.5s';
        setTimeout(() => element.remove(), 500);
      }, 2000);
    }
    
    // Start or stop listening
    async function toggleListening() {
      if (!isListening) {
        try {
          // Start WebSocket connection
          ws = new WebSocket('ws://localhost:9000/ws');
          
          ws.onopen = function() {
            log('WebSocket connection established');
            statusText.textContent = 'Connected';
            
            // Start audio after WebSocket is connected
            startAudio();
          };
          
          ws.onclose = function() {
            log('WebSocket connection closed');
            statusText.textContent = 'Disconnected';
            stopAudio();
            isListening = false;
            startButton.textContent = 'Start Listening';
            startButton.classList.remove('active');
          };
          
          ws.onerror = function(error) {
            log('WebSocket error occurred');
            console.error('WebSocket error:', error);
          };
          
          ws.onmessage = function(event) {
            try {
              const data = JSON.parse(event.data);
              
              // Handle model list
              if (data.loaded_models) {
                log(`Loaded ${data.loaded_models.length} models`);
                modelsList.innerHTML = '';
              }
              
              // Handle wake word activations
              if (data.activations && data.activations.length > 0) {
                data.activations.forEach(word => {
                  log(`Detected: ${word}`);
                  showWakeWord(word);
                });
              }
              
              // Handle recording status
              if (data.status === 'recording_started') {
                log(`Started recording after wake word: ${data.wake_word}`);
                statusText.textContent = `Recording after: ${data.wake_word}`;
              } else if (data.status === 'recording_stopped') {
                log(`Recording stopped (${data.trigger}): ${data.filename}`);
                statusText.textContent = 'Listening for wake words';
              }
            } catch (e) {
              console.error('Error parsing message:', e);
            }
          };
        } catch (error) {
          log(`Error starting: ${error.message}`);
          console.error('Error starting:', error);
        }
      } else {
        // Stop listening
        stopAudio();
        
        if (ws) {
          ws.close();
        }
        
        isListening = false;
        startButton.textContent = 'Start Listening';
        startButton.classList.remove('active');
        statusText.textContent = 'Not connected';
      }
    }
    
    // Start audio capture
    async function startAudio() {
      try {
        // Get microphone access
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Create audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        sampleRate = audioContext.sampleRate;
        
        // Send sample rate to server
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(sampleRate.toString());
          log(`Microphone initialized at ${sampleRate}Hz`);
        }
        
        // Set up audio processing
        const source = audioContext.createMediaStreamSource(audioStream);
        
        // Use ScriptProcessor (compatible with more browsers)
        processorNode = audioContext.createScriptProcessor(4096, 1, 1);
        
        processorNode.onaudioprocess = function(e) {
          if (ws && ws.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0);
            const samples = new Int16Array(inputData.length);
            
            // Convert float32 (-1.0 to 1.0) to int16 (-32768 to 32767)
            for (let i = 0; i < inputData.length; i++) {
              samples[i] = Math.max(-32768, Math.min(32767, Math.round(inputData[i] * 32767)));
            }
            
            ws.send(samples.buffer);
          }
        };
        
        // Connect the nodes
        source.connect(processorNode);
        processorNode.connect(audioContext.destination);
        
        // Update UI
        isListening = true;
        startButton.textContent = 'Stop Listening';
        startButton.classList.add('active');
        statusText.textContent = 'Listening for wake words';
        log('Started listening');
      } catch (error) {
        log(`Microphone error: ${error.message}`);
        console.error('Error accessing microphone:', error);
      }
    }
    
    // Stop audio capture
    function stopAudio() {
      if (processorNode) {
        processorNode.disconnect();
        processorNode = null;
      }
      
      if (audioContext) {
        audioContext.close().catch(console.error);
        audioContext = null;
      }
      
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
      }
      
      log('Stopped listening');
    }
    
    // Add event listener to button
    startButton.addEventListener('click', toggleListening);
    
    // Log startup
    log('Page loaded. Click "Start Listening" to begin.');
  </script>
</body>
</html>
"""

# Define static file handler
async def static_file_handler(request):
    return web.Response(text=SIMPLE_HTML, content_type='text/html')

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

    logger.info("Starting openWakeWord simple server...")
    
    # Check if user provided a specific model path argument
    if args.model_path != "":
        logger.info(f"Loading model from path: {args.model_path}")
        owwModel = Model(wakeword_models=[args.model_path],
                         inference_framework=args.inference_framework,
                         vad_threshold=0.3)
    else:
        logger.info(f"Loading {len(local_onnx_model_paths)} models from local directory")
        owwModel = Model(wakeword_models=local_onnx_model_paths,
                         inference_framework=args.inference_framework,
                         vad_threshold=0.3)

    logger.info(f"Loaded models: {list(owwModel.models.keys())}")
    logger.info("Server will automatically record after wake word detection")
    logger.info("Recording will end with ENGAGE, a 2.5s pause, or after 12 seconds")
    
    # Start webapp
    web.run_app(app, host='localhost', port=9000) 