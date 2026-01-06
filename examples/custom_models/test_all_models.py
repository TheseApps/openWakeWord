"""
Test script that can run both Picovoice and openWakeWord models
Demonstrates secure key management pattern
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.secrets import get_secret, ensure_secrets_file
import argparse

# ============================================================
# This script can use multiple API keys from .secrets file
# Optional keys:
# - PICOVOICE_ACCESS_KEY: For Picovoice wake words
# - OPENAI_API_KEY: For AI features (if needed)
# ============================================================

def test_picovoice():
    """Test Picovoice models if key is available"""
    key = get_secret("PICOVOICE_ACCESS_KEY")
    
    if not key:
        print("Picovoice key not found in .secrets")
        print("Skipping Picovoice tests...")
        return False
        
    print(f"Picovoice key loaded: {key[:8]}...")
    
    try:
        import pvporcupine
        import pyaudio
        import struct
        from datetime import datetime
        
        # Test OK Frank model
        porcupine = pvporcupine.create(
            access_key=key,
            keyword_paths=["examples/custom_models/OK-Frank_en_windows_v4_0_0.ppn"]
        )
        
        print("OK Frank model loaded successfully!")
        porcupine.delete()
        return True
        
    except ImportError:
        print("Picovoice not installed. Run: pip install pvporcupine")
        return False
    except Exception as e:
        print(f"Picovoice test failed: {e}")
        return False

def test_openwakeword():
    """Test openWakeWord models (no key required)"""
    print("\nTesting openWakeWord models...")
    
    try:
        from openwakeword.model import Model
        import numpy as np
        
        # Load a model
        model = Model(
            wakeword_models=["models/hey_jarvis_v0.1.onnx"],
            inference_framework="onnx"
        )
        
        # Test with dummy audio
        audio = np.zeros(1280, dtype=np.int16)
        predictions = model.predict(audio)
        
        print("openWakeWord models loaded successfully!")
        print(f"Models available: {list(model.models.keys())}")
        return True
        
    except Exception as e:
        print(f"openWakeWord test failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Test wake word models with secure key management"
    )
    parser.add_argument(
        "--system",
        choices=["all", "picovoice", "openwakeword"],
        default="all",
        help="Which system to test"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("WAKE WORD MODEL TESTER")
    print("=" * 60)
    
    # Ensure secrets file exists
    if not ensure_secrets_file():
        print("\nCreated new .secrets file.")
        print("Please add your API keys and run again.")
        return
    
    results = {}
    
    if args.system in ["all", "picovoice"]:
        results["Picovoice"] = test_picovoice()
        
    if args.system in ["all", "openwakeword"]:
        results["openWakeWord"] = test_openwakeword()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for system, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{system:15} {status}")
    print("=" * 60)

if __name__ == "__main__":
    main()
