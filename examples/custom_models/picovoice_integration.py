"""
Integration script for using Picovoice Porcupine models alongside openWakeWord
This allows you to use both systems together for maximum flexibility
"""

import pvporcupine
import pyaudio
import struct
import numpy as np
from openwakeword.model import Model
import argparse

class DualWakeWordDetector:
    """Combines Picovoice and openWakeWord detection"""
    
    def __init__(self, picovoice_key, picovoice_model_path=None, oww_model_paths=None):
        # Initialize Picovoice Porcupine
        if picovoice_model_path:
            self.porcupine = pvporcupine.create(
                access_key=picovoice_key,
                keyword_paths=[picovoice_model_path]  # Your OK Frank .ppn file
            )
        else:
            self.porcupine = None
            
        # Initialize openWakeWord
        if oww_model_paths:
            self.oww_model = Model(
                wakeword_models=oww_model_paths,
                inference_framework='onnx'
            )
        else:
            self.oww_model = None
            
        # Audio settings
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=16000,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=512
        )
        
    def detect(self):
        """Run detection loop for both systems"""
        print("Listening for wake words...")
        print("Say 'OK Frank' (Picovoice) or other loaded wake words (openWakeWord)")
        
        oww_audio_buffer = []
        
        try:
            while True:
                # Read audio frame
                pcm = self.audio_stream.read(512, exception_on_overflow=False)
                pcm_array = struct.unpack_from("h" * 512, pcm)
                
                # Check Picovoice detection
                if self.porcupine:
                    keyword_index = self.porcupine.process(pcm_array)
                    if keyword_index >= 0:
                        print("🎯 Picovoice: 'OK Frank' detected!")
                        
                # Check openWakeWord detection
                if self.oww_model:
                    # Convert to numpy array for openWakeWord
                    audio_data = np.array(pcm_array, dtype=np.int16)
                    oww_audio_buffer.extend(audio_data)
                    
                    # Process in 1280-sample chunks (80ms at 16kHz)
                    if len(oww_audio_buffer) >= 1280:
                        chunk = np.array(oww_audio_buffer[:1280])
                        oww_audio_buffer = oww_audio_buffer[1280:]
                        
                        predictions = self.oww_model.predict(chunk)
                        for model, score in predictions.items():
                            if score > 0.5:
                                print(f"🎤 openWakeWord: '{model}' detected (score: {score:.2f})")
                                
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        if self.porcupine:
            self.porcupine.delete()
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.pa.terminate()


def standalone_picovoice(access_key, model_path):
    """Run Picovoice Porcupine standalone"""
    
    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[model_path]
    )
    
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )
    
    print(f"Listening for wake word (Picovoice Porcupine)...")
    print(f"Model: {model_path}")
    
    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print(f"Wake word detected!")
                
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        audio_stream.stop_stream()
        audio_stream.close()
        pa.terminate()
        porcupine.delete()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--picovoice_key",
        help="Your Picovoice access key",
        required=True
    )
    parser.add_argument(
        "--picovoice_model",
        help="Path to .ppn model file from Picovoice",
        default=None
    )
    parser.add_argument(
        "--oww_models",
        help="Paths to openWakeWord models",
        nargs="+",
        default=None
    )
    parser.add_argument(
        "--mode",
        help="Run mode: 'dual', 'picovoice', or 'oww'",
        default="dual"
    )
    
    args = parser.parse_args()
    
    if args.mode == "picovoice":
        # Run Picovoice only
        standalone_picovoice(args.picovoice_key, args.picovoice_model)
    elif args.mode == "dual":
        # Run both systems
        detector = DualWakeWordDetector(
            picovoice_key=args.picovoice_key,
            picovoice_model_path=args.picovoice_model,
            oww_model_paths=args.oww_models
        )
        detector.detect()
    else:
        print("Invalid mode. Choose 'dual' or 'picovoice'")
