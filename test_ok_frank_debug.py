"""
Debug script to test OK Frank with verbose output
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.secrets import get_required_secret

print("Step 1: Loading Picovoice...")
import pvporcupine
print("[OK] Picovoice imported")

print("\nStep 2: Loading access key...")
key = get_required_secret("PICOVOICE_ACCESS_KEY")
print(f"[OK] Key loaded: {key[:10]}...")

print("\nStep 3: Loading OK Frank model...")
model_path = "examples/custom_models/OK-Frank_en_windows_v4_0_0.ppn"
if os.path.exists(model_path):
    print(f"[OK] Model file found: {model_path}")
else:
    print(f"[ERROR] Model file NOT found: {model_path}")
    sys.exit(1)

print("\nStep 4: Creating Porcupine instance...")
try:
    porcupine = pvporcupine.create(
        access_key=key,
        keyword_paths=[model_path],
        sensitivities=[0.5]
    )
    print("[OK] Porcupine created successfully!")
    print(f"  Sample rate: {porcupine.sample_rate} Hz")
    print(f"  Frame length: {porcupine.frame_length} samples")
    
    print("\nStep 5: Testing audio input...")
    import pyaudio
    pa = pyaudio.PyAudio()
    
    # List audio devices
    print("\nAvailable audio input devices:")
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"  [{i}] {info['name']}")
    
    # Open stream
    stream = pa.open(
        rate=16000,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=512
    )
    print("\n[OK] Audio stream opened!")
    
    print("\n" + "="*50)
    print("READY! Say 'OK Frank'")
    print("="*50)
    
    import struct
    from datetime import datetime
    
    frame_count = 0
    while frame_count < 100:  # Test for ~3 seconds
        pcm = stream.read(512, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * 512, pcm)
        
        result = porcupine.process(pcm)
        frame_count += 1
        
        if result >= 0:
            print(f"\n>>> OK FRANK DETECTED at {datetime.now():%H:%M:%S}!")
            break
            
        if frame_count % 10 == 0:
            print(".", end="", flush=True)
    
    print(f"\n\nProcessed {frame_count} frames")
    
    # Cleanup
    stream.close()
    pa.terminate()
    porcupine.delete()
    
except pvporcupine.PorcupineActivationError as e:
    print(f"\n[ERROR] Activation Error: {e}")
    print("Check your access key!")
except pvporcupine.PorcupineError as e:
    print(f"\n[ERROR] Porcupine Error: {e}")
except Exception as e:
    print(f"\n[ERROR] Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
