#!/usr/bin/env python3
import numpy as np
import soundfile as sf
import os
import wave
import librosa
import librosa.effects
from openwakeword.model import Model

def generate_realistic_wakewords():
    """Generate more realistic wake word audio by using formant synthesis"""
    output_dir = "test_audio"
    os.makedirs(output_dir, exist_ok=True)
    
    # Parameters
    sample_rate = 16000
    
    # -- "Hey Jarvis" wake word --
    # Generate carrier wave for the word "Hey"
    duration_hey = 0.35  # seconds
    t_hey = np.linspace(0, duration_hey, int(sample_rate * duration_hey))
    
    # Use a mix of sine waves for more realistic formants
    hey_formants = [
        (280, 1.0),   # Fundamental frequency for "H"
        (400, 0.7),   # First formant
        (2200, 0.4),  # Second formant
        (2900, 0.2)   # Third formant
    ]
    
    hey_wave = np.zeros_like(t_hey)
    for freq, amp in hey_formants:
        hey_wave += amp * np.sin(2 * np.pi * freq * t_hey)
    
    # Apply envelope to make it sound more like speech
    envelope = np.concatenate([
        np.linspace(0, 1, int(0.1 * sample_rate)),
        np.ones(int(0.15 * sample_rate)),
        np.linspace(1, 0, int(0.1 * sample_rate))
    ])
    
    if len(envelope) < len(hey_wave):
        envelope = np.pad(envelope, (0, len(hey_wave) - len(envelope)), 'constant')
    else:
        envelope = envelope[:len(hey_wave)]
    
    hey_wave *= envelope
    
    # Generate "Jarvis" segment
    duration_jarvis = 0.7  # seconds
    t_jarvis = np.linspace(0, duration_jarvis, int(sample_rate * duration_jarvis))
    
    jarvis_formants = [
        (180, 1.0),   # Fundamental frequency for "J"
        (500, 0.8),   # First formant
        (1800, 0.5),  # Second formant
        (2500, 0.3)   # Third formant
    ]
    
    jarvis_wave = np.zeros_like(t_jarvis)
    for freq, amp in jarvis_formants:
        jarvis_wave += amp * np.sin(2 * np.pi * freq * t_jarvis)
    
    # Apply envelope to make it sound more like speech
    jarvis_envelope = np.concatenate([
        np.linspace(0, 1, int(0.1 * sample_rate)),
        np.ones(int(0.5 * sample_rate)),
        np.linspace(1, 0, int(0.1 * sample_rate))
    ])
    
    if len(jarvis_envelope) < len(jarvis_wave):
        jarvis_envelope = np.pad(jarvis_envelope, (0, len(jarvis_wave) - len(jarvis_envelope)), 'constant')
    else:
        jarvis_envelope = jarvis_envelope[:len(jarvis_wave)]
    
    jarvis_wave *= jarvis_envelope
    
    # Combine with a small pause
    pause = np.zeros(int(0.1 * sample_rate))
    hey_jarvis = np.concatenate([hey_wave, pause, jarvis_wave])
    
    # --- "Hey Mycroft" wake word ---
    # Reuse "Hey" and create "Mycroft"
    duration_mycroft = 0.8  # seconds
    t_mycroft = np.linspace(0, duration_mycroft, int(sample_rate * duration_mycroft))
    
    mycroft_formants = [
        (190, 1.0),   # Fundamental frequency for "M"
        (550, 0.8),   # First formant
        (1900, 0.5),  # Second formant
        (2700, 0.3)   # Third formant
    ]
    
    mycroft_wave = np.zeros_like(t_mycroft)
    for freq, amp in mycroft_formants:
        mycroft_wave += amp * np.sin(2 * np.pi * freq * t_mycroft)
    
    # Apply envelope to make it sound more like speech
    mycroft_envelope = np.concatenate([
        np.linspace(0, 1, int(0.1 * sample_rate)),
        np.ones(int(0.6 * sample_rate)),
        np.linspace(1, 0, int(0.1 * sample_rate))
    ])
    
    if len(mycroft_envelope) < len(mycroft_wave):
        mycroft_envelope = np.pad(mycroft_envelope, (0, len(mycroft_wave) - len(mycroft_envelope)), 'constant')
    else:
        mycroft_envelope = mycroft_envelope[:len(mycroft_wave)]
    
    mycroft_wave *= mycroft_envelope
    
    # Combine with a small pause
    hey_mycroft = np.concatenate([hey_wave, pause, mycroft_wave])
    
    # Apply audio processing to make it sound more natural
    hey_jarvis = (hey_jarvis * 0.8).astype(np.float32)  # Lower volume a bit
    hey_mycroft = (hey_mycroft * 0.8).astype(np.float32)  # Lower volume a bit
    
    # Apply a slight reverb effect
    hey_jarvis = librosa.effects.preemphasis(hey_jarvis)
    hey_mycroft = librosa.effects.preemphasis(hey_mycroft)
    
    # Convert to int16
    hey_jarvis_int16 = (hey_jarvis * 32767).astype(np.int16)
    hey_mycroft_int16 = (hey_mycroft * 32767).astype(np.int16)
    
    # Save the files
    hey_jarvis_file = f"{output_dir}/hey_jarvis_realistic.wav"
    hey_mycroft_file = f"{output_dir}/hey_mycroft_realistic.wav"
    
    sf.write(hey_jarvis_file, hey_jarvis_int16, sample_rate, subtype='PCM_16')
    sf.write(hey_mycroft_file, hey_mycroft_int16, sample_rate, subtype='PCM_16')
    
    print(f"Generated realistic wake word files in {output_dir}/")
    return hey_jarvis_file, hey_mycroft_file

def test_with_models(audio_files):
    """Test the generated audio with the wake word models"""
    print("\nTesting wake word models with realistic audio:")
    
    # Load models
    model_paths = [
        "models/alexa_v0.1.onnx",
        "models/hey_mycroft_v0.1.onnx",
        "models/hey_jarvis_v0.1.onnx"
    ]
    
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
            total_chunks = max(1, len(audio_data) // chunk_size)
            
            for i in range(total_chunks):
                chunk = audio_data[i * chunk_size:min(len(audio_data), (i + 1) * chunk_size)]
                
                # Pad if needed
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')
                
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

if __name__ == "__main__":
    # Generate realistic wake word audio
    hey_jarvis_file, hey_mycroft_file = generate_realistic_wakewords()
    
    # Test with models
    test_with_models([hey_jarvis_file, hey_mycroft_file])
    
    # Update the HTML player with the new files
    html_file = "test_audio_player.html"
    if os.path.exists(html_file):
        with open(html_file, 'r') as f:
            content = f.read()
        
        # Add new audio elements
        if "hey_jarvis_realistic.wav" not in content:
            insert_point = content.find('</div>\n\n    <h2>Test Scripts</h2>')
            if insert_point > 0:
                new_audio = """    <div class="audio-container">
        <div class="audio-title">"Hey Jarvis" Realistic Test Audio</div>
        <audio controls>
            <source src="test_audio/hey_jarvis_realistic.wav" type="audio/wav">
            Your browser doesn't support audio playback.
        </audio>
        <div class="description">
            This is a more realistic test file generated with formant synthesis.
        </div>
    </div>

    <div class="audio-container">
        <div class="audio-title">"Hey Mycroft" Realistic Test Audio</div>
        <audio controls>
            <source src="test_audio/hey_mycroft_realistic.wav" type="audio/wav">
            Your browser doesn't support audio playback.
        </audio>
        <div class="description">
            This is a more realistic test file generated with formant synthesis.
        </div>
    </div>
"""
                updated_content = content[:insert_point] + new_audio + content[insert_point:]
                
                with open(html_file, 'w') as f:
                    f.write(updated_content)
                    
                print(f"Updated {html_file} with new audio players") 