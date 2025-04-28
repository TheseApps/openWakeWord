#!/usr/bin/env python3
import os
import numpy as np
from openwakeword.model import Model
import librosa
import soundfile as sf
import logging
import glob
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_audio_file(model, file_path):
    """Process an audio file and check for wake word activations."""
    try:
        logger.info(f"Processing file: {file_path}")
        
        # Load audio with librosa (handles MP3, WAV, etc.)
        audio, sr = librosa.load(file_path, sr=16000, mono=True)
        
        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Process in chunks to simulate streaming
        chunk_size = 4096
        total_chunks = len(audio_int16) // chunk_size
        
        logger.info(f"Audio length: {len(audio_int16) / 16000:.2f} seconds, {total_chunks} chunks")
        
        # Dictionary to store maximum activation values
        max_activations = {model_name: 0.0 for model_name in model.models.keys()}
        
        # Process audio in chunks
        for i in range(total_chunks):
            chunk = audio_int16[i * chunk_size:(i + 1) * chunk_size]
            
            # Get predictions
            predictions = model.predict(chunk)
            
            # Check for wake word activations
            activations = []
            for key, value in predictions.items():
                # Update maximum activation value
                max_activations[key] = max(max_activations[key], value)
                
                # Check for activation
                if value >= 0.4:  # Using lower threshold
                    activations.append(f"{key}: {value:.4f}")
            
            # Log activations
            if activations:
                logger.info(f"[{i}/{total_chunks}] Activations detected: {', '.join(activations)}")
        
        # Print maximum activations for each model
        logger.info("Maximum activation values:")
        for model_name, max_value in max_activations.items():
            logger.info(f"  {model_name}: {max_value:.4f}")
        
        return max_activations
            
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return {}

def main():
    # Set up model
    model_paths = [
        "models/alexa_v0.1.onnx",
        "models/hey_mycroft_v0.1.onnx",
        "models/hey_jarvis_v0.1.onnx",
        "models/hey_rhasspy_v0.1.onnx",
    ]
    
    logger.info("Loading wake word models...")
    model = Model(
        wakeword_models=model_paths,
        inference_framework='onnx',
        vad_threshold=0.2,
        enable_speex_noise_suppression=False
    )
    
    # Create list of directories to check
    directories = [
        "recordings/angie",
        "recordings/applejack",
        "recordings/daniel",
        "recordings/various"
    ]
    
    # Process each directory
    for directory in directories:
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            continue
            
        logger.info(f"Processing directory: {directory}")
        
        # Find audio files
        audio_files = []
        for ext in ["*.wav", "*.mp3", "*.ogg", "*.flac"]:
            audio_files.extend(glob.glob(os.path.join(directory, ext)))
        
        logger.info(f"Found {len(audio_files)} audio files")
        
        # Process each file
        for file_path in audio_files[:5]:  # Process first 5 files in each directory
            process_audio_file(model, file_path)
            time.sleep(0.5)  # Short delay between files

if __name__ == "__main__":
    logger.info("Starting wake word detection test on recorded audio")
    main()
    logger.info("Test complete") 