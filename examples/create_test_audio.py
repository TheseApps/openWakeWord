#!/usr/bin/env python3
import numpy as np
import soundfile as sf
import os
import argparse
import wave
from openwakeword.model import Model

def generate_test_audio():
    """Generate simple test audio with sine wave patterns for testing"""
    output_dir = "test_audio"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a simple 1-second sine wave (16kHz sample rate)
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Generate different frequencies for different "words"
    freqs = {
        "hey": 300,
        "jarvis": 400,
        "ok": 500,
        "mycroft": 600
    }
    
    # Generate individual word components
    word_components = {}
    for word, freq in freqs.items():
        sine_wave = np.sin(2 * np.pi * freq * t)
        word_components[word] = (sine_wave * 32767).astype(np.int16)
    
    # Create "Hey Jarvis" by concatenating components with a small pause
    hey_jarvis = np.concatenate([
        word_components["hey"], 
        np.zeros(int(0.1 * sample_rate), dtype=np.int16),
        word_components["jarvis"]
    ])
    
    # Create "OK Mycroft" by concatenating components
    ok_mycroft = np.concatenate([
        word_components["ok"], 
        np.zeros(int(0.1 * sample_rate), dtype=np.int16),
        word_components["mycroft"]
    ])
    
    # Save files
    sf.write(f"{output_dir}/hey_jarvis_test.wav", hey_jarvis, sample_rate, subtype='PCM_16')
    sf.write(f"{output_dir}/ok_mycroft_test.wav", ok_mycroft, sample_rate, subtype='PCM_16')
    
    print(f"Generated test audio files in {output_dir}/")
    return f"{output_dir}/hey_jarvis_test.wav", f"{output_dir}/ok_mycroft_test.wav"

def test_with_models(audio_files):
    """Test the generated audio with the wake word models"""
    print("\nTesting wake word models with generated audio:")
    
    # Load models
    model_paths = [
        "models/alexa_v0.1.onnx",
        "models/hey_mycroft_v0.1.onnx",
        "models/hey_jarvis_v0.1.onnx"
    ]
    
    # Check if models exist
    for model_path in model_paths:
        if not os.path.exists(model_path):
            print(f"Warning: Model file not found: {model_path}")
    
    # Initialize model
    try:
        model = Model(
            wakeword_models=model_paths,
            inference_framework='onnx',
            vad_threshold=0.1,
            enable_speex_noise_suppression=False
        )
        
        print(f"Loaded models: {list(model.models.keys())}")
        
        # Test each audio file
        for audio_file in audio_files:
            print(f"\nTesting with {audio_file}:")
            
            # Load audio file
            with wave.open(audio_file, 'rb') as wf:
                audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            
            # Process in chunks to simulate streaming
            chunk_size = 4096
            total_chunks = len(audio_data) // chunk_size
            
            for i in range(total_chunks):
                chunk = audio_data[i * chunk_size:(i + 1) * chunk_size]
                predictions = model.predict(chunk)
                
                # Print non-zero predictions
                for key, value in predictions.items():
                    if value > 0.1:
                        print(f"  Model {key}: {value:.4f}")
            
            # Also test the entire file at once
            predictions = model.predict(audio_data)
            print(f"Full file predictions:")
            for key, value in predictions.items():
                print(f"  Model {key}: {value:.4f}")
                
    except Exception as e:
        print(f"Error testing models: {e}")

def search_for_wake_word_data():
    """Search for real wake word recordings in the workspace"""
    potential_sources = [
        "recordings",
        "notebooks/training_tutorial_data"
    ]
    
    found_files = []
    
    for source in potential_sources:
        if os.path.exists(source):
            for root, dirs, files in os.walk(source):
                for file in files:
                    if file.endswith(('.wav', '.mp3', '.ogg')):
                        found_files.append(os.path.join(root, file))
                        if len(found_files) >= 10:  # Limit to 10 files
                            break
    
    print(f"Found {len(found_files)} potential audio files for testing")
    return found_files[:5]  # Return first 5 files for testing

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and test wake word audio")
    parser.add_argument("--generate-only", action="store_true", help="Only generate test audio, don't test models")
    args = parser.parse_args()
    
    # Generate synthetic test audio
    hey_jarvis_file, ok_mycroft_file = generate_test_audio()
    
    if not args.generate_only:
        # Test with models
        test_with_models([hey_jarvis_file, ok_mycroft_file])
        
        # Find and test with real recordings if available
        real_audio_files = search_for_wake_word_data()
        if real_audio_files:
            print("\nTesting with real audio recordings:")
            test_with_models(real_audio_files) 