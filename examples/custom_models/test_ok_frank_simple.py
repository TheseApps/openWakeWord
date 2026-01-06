"""
Simple test for OK Frank - Reads access key from .secrets file
"""
import pvporcupine
import pyaudio
import struct
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import secure secrets manager
from utils.secrets import get_required_secret

# ============================================================
# Access key is loaded securely from .secrets file
# To set it up:
# 1. Open the .secrets file in project root
# 2. Add: PICOVOICE_ACCESS_KEY=your_actual_key_here
# 3. Save the file
# ============================================================

def test():
    # Load access key securely
    print("\nLoading access key from .secrets file...")
    ACCESS_KEY = get_required_secret("PICOVOICE_ACCESS_KEY")
    
    print("Initializing OK Frank...")
    
    # Create detector
    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=["examples/custom_models/OK-Frank_en_windows_v4_0_0.ppn"],
            sensitivities=[0.5]
        )
    except pvporcupine.PorcupineActivationError:
        print("\nERROR: Invalid access key!")
        print("Please check your key at: https://console.picovoice.ai/")
        sys.exit(1)
    
    # Setup audio
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=16000, channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=512
    )
    
    print("\n" + "=" * 50)
    print("LISTENING FOR 'OK FRANK'")
    print("=" * 50)
    print("Say: 'OK Frank' (Press Ctrl+C to stop)\n")
    
    try:
        while True:
            pcm = stream.read(512, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * 512, pcm)
            
            if porcupine.process(pcm) >= 0:
                print(f"[{datetime.now():%H:%M:%S}] OK FRANK DETECTED!")
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stream.close()
        pa.terminate()
        porcupine.delete()

if __name__ == "__main__":
    test()
