# Testing the Fixed OpenWakeWord Streaming Server

We've made several key improvements to make the wake word detection more sensitive and reliable:

1. **Lowered detection threshold** from 0.5 to 0.3
2. **Boosted audio gain** by 1.5x to make spoken words clearer
3. **Reduced VAD threshold** from 0.2 to 0.1 for better speech detection
4. **Disabled noise suppression** which might have been filtering important speech sounds
5. **Added diagnostic logging** to see prediction values
6. **Reduced client buffer size** for more frequent predictions

## Running the Server

1. Start the server:
   ```
   python examples/web/streaming_server.py
   ```

2. Open the client in your browser:
   - Navigate to http://localhost:9000 in your web browser
   - Click "Start Listening"

## Testing Wake Words

When testing, try these approaches:

1. **Speak clearly** but at a normal volume
2. Say the complete wake phrase:
   - "Hey Jarvis"
   - "Hey Mycroft"
   - "Alexa"
3. **Pause briefly** (about 0.5 seconds) after saying the wake word
4. **Monitor the console output** - you should see prediction values in the logs now
5. Try different distances from your microphone

## Troubleshooting

If you're still having issues:

1. Check the server logs:
   - Look for prediction values - even values above 0.1 will be shown
   - When you say a wake word correctly, you should see values climbing

2. Try listening to our test audio:
   - Open `test_audio_player.html` in your browser
   - Listen to both simple and realistic audio examples
   - Run `python examples/create_realistic_wakewords.py` to generate more test files

3. Try speaking like the test audio:
   - "Hey" should be slightly higher pitched
   - Slight pause between "Hey" and "Jarvis"
   - "Jarvis" should be slightly lower pitched

4. Check model availability:
   - Ensure the wake word models are installed
   - If missing, run: `python -c 'import openwakeword.utils; openwakeword.utils.download_models()'`

## Common Issues

- **Too quiet**: Speak up or move closer to the microphone
- **Too fast**: Say the wake word slightly slower than normal conversation
- **Background noise**: Try in a quieter environment
- **Accent differences**: The models were trained on specific accents, so you might need to adjust your pronunciation

## Recovery

If anything goes wrong, you can restore the original files:
- `examples/web/streaming_server.py.bak`
- `examples/web/streaming_client.html.bak` 



-----


I'll help you review and understand your openWakeWord codebase! Let me explore it systematically to remind you how everything works.

[12 tools called]

## 🧠 **openWakeWord System Summary** | journal(remember_this)

Let me walk you through your wake word detection system and fix that streaming server issue!

### 🎯 **What This System Does** | core.purpose()
Your **openWakeWord** project is a real-time wake word detection framework that listens for specific trigger phrases (like "Alexa", "Hey Jarvis", etc.) in audio streams. Think of it as an always-listening ear that perks up when it hears its name!

### 🏗️ **Architecture Overview** | system.compartments()

[27 tools called]

## 🎉 **Success!** Your streaming server is now running on http://localhost:9000

---

# 📚 **openWakeWord System Documentation** | omniGlyph.summary()

## 🧬 **Core Architecture** | system.DNA()

### **Three-Layer Model Stack** | compartment.models()
```
┌─────────────────────────────┐
│   1. Melspectrogram Layer   │ ← Audio → Frequency
├─────────────────────────────┤
│   2. Embedding Model         │ ← Features → Vectors  
├─────────────────────────────┤
│   3. Wake Word Classifiers  │ ← Vectors → Predictions
└─────────────────────────┘
```

### **Key Actors & Roles** | actors.define()

1. **AudioFeatures** | role: `preprocessor`
   - Converts raw audio (16kHz PCM) into mel-spectrograms
   - Manages sliding window of audio frames (80ms chunks)

2. **Model Class** | role: `orchestrator`
   - Manages multiple wake word models simultaneously
   - Handles prediction pipeline and scoring
   - Optional VAD (Voice Activity Detection) filtering

3. **WebSocket Handler** | role: `listener`
   - Receives audio streams from web browsers
   - Manages real-time bidirectional communication
   - Sends detection events back to clients

### **Available Wake Words** | vocabulary.list()
- 🔵 **"Alexa"** 
- 🟢 **"Hey Jarvis"**
- 🟡 **"Hey Mycroft"**
- 🟣 **"Hey Rhasspy"**
- ⏰ **Timer phrases** ("set a timer")
- ☁️ **Weather phrases** ("what's the weather")

## 🔧 **How It Works** | process.flow()

### **Detection Pipeline** | verb: `detect()`
1. **Audio Capture** → 16kHz mono audio stream
2. **Buffering** → Accumulate 80ms frames (1,280 samples)
3. **Feature Extraction** → Convert to mel-spectrogram
4. **Embedding Generation** → Google's speech embeddings
5. **Classification** → Score each wake word model (0.0-1.0)
6. **Thresholding** → Trigger if score > 0.5 (configurable)

### **Performance Metrics** | rank.quality()
- **False Reject Rate**: < 5% (misses intended activations)
- **False Accept Rate**: < 0.5/hour (unintended activations)
- **Latency**: ~80-160ms detection time
- **CPU Usage**: Can run 15-20 models on RPi3 single core

## 🚀 **Quick Start Commands** | action.execute()

### **Start Streaming Server**
```powershell
# From project root:
.\.venv312\Scripts\Activate.ps1
python examples/web/streaming_server.py
```

### **Open Web Interface**
```
http://localhost:9000
# Then open: examples/web/streaming_client.html
```

### **Test with Microphone**
```powershell
python examples/detect_from_microphone.py
```

### **Capture Training Data**
```powershell
python examples/capture_activations.py
```

## 🗂️ **File Organization** | compartment.structure()

```
📦 openWakeWord/
├── 🧠 openwakeword/          # Core library
│   ├── model.py              # Main Model class
│   ├── utils.py              # Audio processing
│   └── vad.py                # Voice detection
├── 🎯 models/                # Pre-trained models
│   ├── *.onnx                # ONNX format models
│   └── *.tflite              # TensorFlow Lite models
├── 🌐 examples/web/          # Web interfaces
│   ├── streaming_server.py   # WebSocket server
│   └── streaming_client.html # Browser interface
└── 📊 notebooks/             # Training tutorials
```

## 💡 **Key Insights** | journal.remember()

1. **Synthetic Training** - All models trained on 100% synthetic speech (no real recordings needed!)
2. **Multi-Model Support** - Run many wake words simultaneously with shared computation
3. **Framework Agnostic** - Supports both ONNX and TFLite runtimes
4. **Privacy First** - Everything runs locally, no cloud needed
5. **Extensible** - Easy to train custom wake words with provided notebooks

## 🐛 **Common Issues & Fixes** | debug.solutions()

1. **Missing Path import** → Fixed by adding `from pathlib import Path`
2. **Models not found** → Run `openwakeword.utils.download_models()` 
3. **PowerShell syntax** → Use `;` instead of `&&` for command chaining
4. **VAD model missing** → Set `vad_threshold=0` to disable

---

Your wake word detection system is now **fully operational**! You can open http://localhost:9000 in your browser and then load the `streaming_client.html` file to start testing voice commands. Say "Hey Jarvis" or "Alexa" to see it in action! 🎤✨