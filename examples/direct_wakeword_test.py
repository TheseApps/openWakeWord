#!/usr/bin/env python3
import pyaudio
import numpy as np
import time
import os
from openwakeword.model import Model
import logging
import keyboard

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_wake_word_detection():
    """Test wake word detection directly with microphone input"""
    logger.info("Starting direct wake word test")
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Set audio parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000  # 16kHz sampling rate required by model
    
    # Load wake word models with very low detection threshold
    model_paths = [
        "models/alexa_v0.1.onnx",
        "models/hey_mycroft_v0.1.onnx",
        "models/hey_jarvis_v0.1.onnx"
    ]
    
    # Check if models exist
    for model_path in model_paths:
        if not os.path.exists(model_path):
            logger.warning(f"Model file not found: {model_path}")
    
    # Load model with various different configurations
    oww_model = Model(
        wakeword_models=model_paths,
        inference_framework='onnx',
        vad_threshold=0.1,  # Very low threshold to detect any speech
        enable_speex_noise_suppression=False
    )
    
    logger.info(f"Loaded models: {list(oww_model.models.keys())}")
    
    # Open audio stream
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    logger.info("Listening for wake words. Press 'q' to quit.")
    logger.info("Try saying: 'Hey Jarvis', 'Hey Mycroft', or 'Alexa'")
    
    # Main loop
    running = True
    while running:
        try:
            # Read audio chunk
            audio_bytes = stream.read(CHUNK, exception_on_overflow=False)
            
            # Convert to numpy array
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Get predictions
            predictions = oww_model.predict(audio_data)
            
            # Check for wake word activations at various thresholds
            any_predictions = False
            thresholds = {0.1: "Very weak", 0.2: "Weak", 0.3: "Moderate", 0.4: "Strong", 0.5: "Very strong"}
            
            for threshold_value, strength in thresholds.items():
                detected = []
                for key, value in predictions.items():
                    if value >= threshold_value:
                        detected.append(f"{key}: {value:.4f}")
                        any_predictions = True
                
                if detected:
                    logger.info(f"{strength} activations (≥{threshold_value}): {', '.join(detected)}")
            
            # If there's any prediction above 0.1, print the audio level
            if any_predictions:
                audio_level = np.abs(audio_data).mean()
                logger.info(f"Audio level: {audio_level:.2f}")
            
            # Check if 'q' was pressed to quit
            if keyboard.is_pressed('q'):
                running = False
                
            # Small delay to prevent CPU overload
            time.sleep(0.01)
            
        except Exception as e:
            logger.error(f"Error: {e}")
    
    # Clean up
    stream.stop_stream()
    stream.close()
    p.terminate()
    logger.info("Test ended.")

if __name__ == "__main__":
    test_wake_word_detection() 