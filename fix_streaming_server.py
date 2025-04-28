#!/usr/bin/env python3
import os
import shutil
import fileinput
import re
import subprocess
from pathlib import Path

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_path = f"{file_path}.bak"
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
    return backup_path

def fix_streaming_server():
    """Apply fixes to the streaming server code"""
    server_path = "examples/web/streaming_server.py"
    
    # Create backup
    backup_file(server_path)
    
    # Fix 1: Lower detection threshold
    with fileinput.FileInput(server_path, inplace=True) as file:
        for line in file:
            # Lower the wake word detection threshold
            if "if predictions[key] >= 0.5:" in line:
                print(line.replace("if predictions[key] >= 0.5:", "if predictions[key] >= 0.3:  # Lowered threshold for better detection"), end='')
            else:
                print(line, end='')
    
    # Fix 2: Improve audio processing and padding
    chunk_size_fix = """                    # Handle small audio frames that could cause ONNX errors
                    min_frame_size = 8192  # Required minimum size for the model
                    if len(data) < min_frame_size:
                        # Pad with zeros if chunk is too small to avoid ONNX shape errors
                        padding = np.zeros(min_frame_size - len(data), dtype=np.int16)
                        data = np.concatenate([data, padding])
                        logger.info(f"Padded small audio chunk from {len(data) - len(padding)} to {len(data)} samples")
                    
                    # Boost audio levels to improve detection
                    data = np.asarray(data * 1.5, dtype=np.int16)  # Apply 1.5x gain while preserving data type
"""
    
    # Replace the audio padding section
    with open(server_path, 'r') as f:
        content = f.read()
    
    pattern = r"                    # Handle small audio frames that could cause ONNX errors.*?min_frame_size = 8192.*?data = np.concatenate\(\[data, padding\]\)"
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, chunk_size_fix.rstrip(), content, flags=re.DOTALL)
        
        with open(server_path, 'w') as f:
            f.write(content)
    
    # Fix 3: Modify model initialization for better sensitivity
    model_init_fix = """        owwModel = Model(wakeword_models=local_onnx_model_paths,
                         inference_framework=args.inference_framework,
                         vad_threshold=0.1,  # Lower VAD threshold for better sensitivity
                         device="cpu",
                         enable_speex_noise_suppression=False)  # Disable noise suppression to prevent filtering of speech"""
    
    with fileinput.FileInput(server_path, inplace=True) as file:
        for line in file:
            if "owwModel = Model(wakeword_models=local_onnx_model_paths," in line:
                # Found the start of model initialization, replace the next 3 lines
                print(line, end='')  # Print current line
                
                # Skip next 2 lines
                next(file)
                next(file)
                
                # Print our replacement
                print(model_init_fix.split('\n')[1], end='\n')
                print(model_init_fix.split('\n')[2], end='\n')
                print(model_init_fix.split('\n')[3], end='\n')
            else:
                print(line, end='')
    
    # Fix 4: Fix the same for user-provided model paths
    user_model_fix = """        owwModel = Model(wakeword_models=[args.model_path],
                         inference_framework=args.inference_framework,
                         vad_threshold=0.1,  # Lower VAD threshold for better sensitivity
                         device="cpu",
                         enable_speex_noise_suppression=False)  # Disable noise suppression to prevent filtering of speech"""
    
    with fileinput.FileInput(server_path, inplace=True) as file:
        for line in file:
            if "owwModel = Model(wakeword_models=[args.model_path]," in line:
                # Found the start of model initialization, replace the next 3 lines
                print(line, end='')  # Print current line
                
                # Skip next 2 lines
                next(file)
                next(file)
                
                # Print our replacement
                print(user_model_fix.split('\n')[1], end='\n')
                print(user_model_fix.split('\n')[2], end='\n')
                print(user_model_fix.split('\n')[3], end='\n')
            else:
                print(line, end='')
    
    # Fix 5: Add diagnostic logging for predictions
    with fileinput.FileInput(server_path, inplace=True) as file:
        for line in file:
            if "# Check for wake word activations" in line:
                print(line, end='')
                print("                        # Log prediction values for debugging")
                print("                        debug_preds = {k: float(v) for k, v in predictions.items() if v > 0.1}")
                print("                        if debug_preds:")
                print("                            logger.info(f\"Prediction values: {debug_preds}\")")
                print("")
            else:
                print(line, end='')
    
    print("Fixed streaming server code!")
    print("The following improvements were made:")
    print("1. Lowered detection threshold from 0.5 to 0.3 for better wake word sensitivity")
    print("2. Added audio gain boost (1.5x) to make audio signals stronger")
    print("3. Reduced VAD threshold from 0.2 to 0.1 for better speech detection")
    print("4. Disabled noise suppression which might be filtering important speech sounds")
    print("5. Added diagnostic logging to see prediction values during operation")
    
    # Fix client side as well
    client_path = "examples/web/streaming_client.html"
    backup_file(client_path)
    
    # Fix 6: Modify client buffer size
    with fileinput.FileInput(client_path, inplace=True) as file:
        for line in file:
            if "const bufferSize = 2048;" in line:
                print("      const bufferSize = 1024;  // Reduced for more frequent predictions", end='\n')
            else:
                print(line, end='')
    
    print("6. Reduced client buffer size for more frequent predictions")
    
    print("\nChanges complete! Try running the server again with:")
    print("python examples/web/streaming_server.py")

def check_models():
    """Check for wake word models"""
    model_paths = [
        "models/alexa_v0.1.onnx",
        "models/hey_mycroft_v0.1.onnx",
        "models/hey_jarvis_v0.1.onnx",
    ]
    
    missing_models = []
    for model_path in model_paths:
        if not os.path.exists(model_path):
            missing_models.append(model_path)
    
    if missing_models:
        print("WARNING: The following models are missing:")
        for model in missing_models:
            print(f"  - {model}")
        print("\nYou may need to download these models first.")
        
        # Check if openwakeword utility is available
        try:
            import openwakeword
            print("\nYou can download the models by running:")
            print("python -c 'import openwakeword.utils; openwakeword.utils.download_models()'")
        except ImportError:
            print("Openwakeword not found. Make sure it's installed.")
    else:
        print("All models are available!")

if __name__ == "__main__":
    print("OpenWakeWord Streaming Server Fixer")
    print("===================================")
    
    check_models()
    
    confirm = input("\nApply fixes to the streaming server? (y/n): ")
    if confirm.lower() == "y":
        fix_streaming_server()
    else:
        print("No changes were made.") 