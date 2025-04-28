#!/usr/bin/env python3
import os
import numpy as np
from openwakeword.model import Model
import wave
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_wav_file(file_path):
    """Load a WAV file and return the audio data."""
    with wave.open(file_path, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        data = np.frombuffer(frames, dtype=np.int16)
        return data, wf.getframerate()

def test_models():
    # Define model paths
    model_paths = [
        "models/alexa_v0.1.onnx",
        "models/hey_mycroft_v0.1.onnx",
        "models/hey_jarvis_v0.1.onnx",
        "models/hey_rhasspy_v0.1.onnx",
    ]
    
    # Print working directory to verify file paths
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Check if model files exist
    for model_path in model_paths:
        if os.path.exists(model_path):
            logger.info(f"Model file exists: {model_path}")
        else:
            logger.error(f"Model file not found: {model_path}")
    
    # Load models with various parameters
    logger.info("Loading models with default parameters")
    try:
        model = Model(wakeword_models=model_paths, 
                      inference_framework='onnx',
                      vad_threshold=0.2,
                      enable_speex_noise_suppression=False)
        
        logger.info(f"Successfully loaded models: {list(model.models.keys())}")
        
        # Test with basic audio
        test_audio = np.random.randint(-32768, 32767, 16000, dtype=np.int16)  # 1 second of random audio
        logger.info("Testing with random audio")
        results = model.predict(test_audio)
        logger.info(f"Prediction results: {results}")
        
        # Test models with all possible parameters
        logger.info("Testing with different parameters")
        test_models = [
            Model(inference_framework='onnx', vad_threshold=0.1),
            Model(inference_framework='onnx', vad_threshold=0.3),
            Model(inference_framework='onnx', vad_threshold=0.5),
        ]
        
        # Log the model settings
        logger.info(f"Default chunk length: {model._chunk_length}")
        logger.info(f"Default sampling rate: {model._sampling_rate}")
        
    except Exception as e:
        logger.error(f"Error loading models: {e}")

if __name__ == "__main__":
    logger.info("Starting model test")
    test_models()
    logger.info("Model test complete") 