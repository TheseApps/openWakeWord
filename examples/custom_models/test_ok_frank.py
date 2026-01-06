"""
Quick test script for OK Frank wake word from Picovoice
"""

import pvporcupine
import pyaudio
import struct
import sys
from datetime import datetime

def test_ok_frank():
    # You need to get your access key from https://console.picovoice.ai/
    # Look for it in the console after logging in
    ACCESS_KEY = None  # Will prompt for it if not set
    
    # Path to your OK Frank model
    model_path = "examples/custom_models/OK-Frank_en_windows_v4_0_0.ppn"
    
    # Get access key if not hardcoded
    if not ACCESS_KEY:
        print("=" * 60)
        print("PICOVOICE ACCESS KEY REQUIRED")
        print("=" * 60)
        print("\nTo get your access key:")
        print("1. Go to: https://console.picovoice.ai/")
        print("2. Sign in (or create free account)")
        print("3. Click 'AccessKey' in the top menu")
        print("4. Copy your key")
        print("\n" + "=" * 60)
        ACCESS_KEY = input("\nPaste your access key here: ").strip()
    
    print("\n>>> Initializing OK Frank detector...")
    
    try:
        # Create Porcupine instance
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[model_path],
            sensitivities=[0.5]  # Adjust 0.0-1.0 if needed (0.5 is default)
        )
        
        # Setup audio
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        
        print("\n" + "=" * 60)
        print("LISTENING FOR 'OK FRANK'")
        print("=" * 60)
        print("\nSpeak clearly and say: 'OK Frank'")
        print("Press Ctrl+C to stop\n")
        
        detection_count = 0
        
        try:
            while True:
                # Read audio frame
                pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                
                # Process audio
                keyword_index = porcupine.process(pcm)
                
                if keyword_index >= 0:
                    detection_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"\n>>> [{timestamp}] OK FRANK DETECTED! (#{detection_count})")
                    print("    - Confidence: HIGH")
                    print("    - Ready for command...\n")
                    
        except KeyboardInterrupt:
            print("\n\nStopping...")
            
    except pvporcupine.PorcupineActivationError:
        print("\nERROR: Invalid access key!")
        print("Please check your access key at: https://console.picovoice.ai/")
        sys.exit(1)
        
    except pvporcupine.PorcupineError as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the .ppn file path is correct")
        print("2. Ensure you have microphone permissions")
        print("3. Check that your access key is valid")
        sys.exit(1)
        
    finally:
        if 'audio_stream' in locals():
            audio_stream.stop_stream()
            audio_stream.close()
        if 'pa' in locals():
            pa.terminate()
        if 'porcupine' in locals():
            porcupine.delete()
            
    print(f"\nTotal detections: {detection_count}")
    print("Test complete!")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("    OK FRANK WAKE WORD TEST")
    print("    Powered by Picovoice Porcupine")
    print("=" * 60)
    test_ok_frank()
