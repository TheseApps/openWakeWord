# Copyright 2022 David Scripka. All rights reserved.
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

##################################

# This example scripts runs openWakeWord continuously on a microphone stream,
# and saves audio before and after the wake word activation as WAV clips
# in the specified output location.

##################################

# Imports
import os
import platform
import collections
import time
if platform.system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio
import numpy as np
from openwakeword.model import Model
import openwakeword
import scipy.io.wavfile
import datetime
import argparse
from utils.beep import playBeep

# Parse input arguments
parser=argparse.ArgumentParser()
parser.add_argument(
    "--output_dir",
    help="Where to save the audio that resulted in an activation",
    type=str,
    default="./",
    required=True
)
parser.add_argument(
    "--threshold",
    help="The score threshold for an activation",
    type=float,
    default=0.5,
    required=False
)
parser.add_argument(
    "--vad_threshold",
    help="""The threshold to use for voice activity detection (VAD) in the openWakeWord instance.
            The default (0.0), disables VAD.""",
    type=float,
    default=0.0,
    required=False
)
parser.add_argument(
    "--noise_suppression",
    help="Whether to enable speex noise suppression in the openWakeWord instance.",
    type=bool,
    default=False,
    required=False
)
parser.add_argument(
    "--chunk_size",
    help="How much audio (in number of 16khz samples) to predict on at once",
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
parser.add_argument(
    "--disable_activation_sound",
    help="Disables the activation sound, clips are silently captured",
    action='store_true',
    required=False
)
parser.add_argument(
    "--pre_activation_time",
    help="Seconds of audio to capture before the wake word (2-3 recommended)",
    type=float,
    default=3.0,
    required=False
)
parser.add_argument(
    "--post_activation_time",
    help="Seconds of audio to capture after the wake word (8-10 recommended)",
    type=float,
    default=8.0,
    required=False
)

args=parser.parse_args()

# Get microphone stream
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = args.chunk_size
audio = pyaudio.PyAudio()
mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

# Load pre-trained openwakeword models
if args.model_path:
    model_paths = openwakeword.get_pretrained_model_paths()
    for path in model_paths:
        if args.model_path in path:
            model_path = path
            
    if model_path:
        owwModel = Model(
            wakeword_models=[model_path],
            enable_speex_noise_suppression=args.noise_suppression,
            vad_threshold = args.vad_threshold,
            inference_framework=args.inference_framework
        )
    else: 
        print(f'Could not find model \"{args.model_path}\"')
        exit()
else:
    owwModel = Model(
        enable_speex_noise_suppression=args.noise_suppression,
        vad_threshold=args.vad_threshold
    )

# Set cooldown period before another activation can be processed
cooldown = 3  # seconds

# Create output directory if it does not already exist
if not os.path.exists(args.output_dir):
    os.mkdir(args.output_dir)

# Run capture loop, checking for hotwords
if __name__ == "__main__":
    # Predict continuously on audio stream
    last_save = time.time()
    recording_in_progress = False
    model_activated = None
    
    print("\n\nListening for wakewords...\n")
    print(f"Will capture {args.pre_activation_time}s before and {args.post_activation_time}s after wake word\n")
    
    while True:
        # Get audio
        mic_audio = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)

        # Feed to openWakeWord model
        prediction = owwModel.predict(mic_audio)

        # Check for model activations (score above threshold)
        for mdl in prediction.keys():
            if prediction[mdl] >= args.threshold and not recording_in_progress and (time.time() - last_save) >= cooldown:
                # Start recording process
                recording_in_progress = True
                model_activated = mdl
                activation_time = time.time()
                
                # Play activation sound if enabled
                if not args.disable_activation_sound:
                    playBeep(os.path.join(os.path.dirname(__file__), 'audio', 'activation.wav'), audio)
                
                detect_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                print(f'Detected activation from \"{mdl}\" at time {detect_time}! Recording...')
                
                # Get pre-activation audio from buffer (convert seconds to samples)
                pre_samples = int(args.pre_activation_time * RATE)
                pre_audio = np.array(list(owwModel.preprocessor.raw_data_buffer)[-pre_samples:]).astype(np.int16)
                
                # Start collecting post-activation audio
                post_audio = []
                
                # Calculate number of chunks needed for post-activation recording
                post_chunks = int((args.post_activation_time * RATE) / CHUNK)
                
                # Collect post-activation audio
                for _ in range(post_chunks):
                    chunk_audio = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)
                    post_audio.extend(chunk_audio)
                
                # Combine pre and post audio
                full_audio = np.concatenate([pre_audio, np.array(post_audio, dtype=np.int16)])
                
                # Save the full audio clip
                fname = detect_time + f"_{mdl}.wav"
                scipy.io.wavfile.write(os.path.join(os.path.abspath(args.output_dir), fname), RATE, full_audio)
                
                print(f"Saved {args.pre_activation_time + args.post_activation_time}s recording to {fname}")
                
                # Play end-of-recording sound if enabled
                if not args.disable_activation_sound:
                    playBeep(os.path.join(os.path.dirname(__file__), 'audio', 'activation.wav'), audio)
                
                # Reset recording state
                recording_in_progress = False
                last_save = time.time()
