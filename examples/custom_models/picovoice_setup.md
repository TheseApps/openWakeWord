# Picovoice Integration Guide

## Quick Start with "OK Frank"

### 1. Complete Training on Picovoice Console
- Platform: Select `Windows (x86_64, arm64)` 
- Click "Train" (takes ~10 seconds)
- Download the `.ppn` model file
- Save your Access Key from the console

### 2. Install Picovoice SDK
```bash
pip install pvporcupine
pip install pyaudio
```

### 3. Test Your Model
```bash
# Test Picovoice model alone
python picovoice_integration.py \
  --picovoice_key YOUR_ACCESS_KEY \
  --picovoice_model ok_frank.ppn \
  --mode picovoice

# Run both Picovoice and openWakeWord together
python picovoice_integration.py \
  --picovoice_key YOUR_ACCESS_KEY \
  --picovoice_model ok_frank.ppn \
  --oww_models models/hey_jarvis_v0.1.onnx models/alexa_v0.1.onnx \
  --mode dual
```

## Model Performance Comparison

| Feature | Picovoice | openWakeWord |
|---------|-----------|--------------|
| Training Time | 10 seconds | 45-90 minutes |
| Model Size | ~1-2 MB | ~1-3 MB |
| CPU Usage | Very Low | Low |
| Custom Words | Yes (paid) | Yes (free) |
| Accuracy | 95-98% | 90-95% |
| Languages | 8+ | English |

## Web Integration

If you selected "Web (WASM)" platform:

```html
<!DOCTYPE html>
<html>
<head>
    <title>OK Frank Web Detection</title>
    <script src="https://unpkg.com/@picovoice/porcupine-web/dist/iife/index.js"></script>
    <script src="https://unpkg.com/@picovoice/web-voice-processor/dist/iife/index.js"></script>
</head>
<body>
    <button id="start">Start Listening</button>
    <div id="status">Ready</div>
    
    <script>
        document.getElementById('start').addEventListener('click', async () => {
            const accessKey = "YOUR_ACCESS_KEY";
            const keywordPath = "./ok_frank.ppn";
            
            const porcupine = await PorcupineWeb.PorcupineWorker.create(
                accessKey,
                [keywordPath],
                detection => {
                    document.getElementById('status').textContent = "OK Frank detected!";
                    console.log("Wake word detected!");
                }
            );
            
            await WebVoiceProcessor.WebVoiceProcessor.subscribe(porcupine);
            document.getElementById('status').textContent = "Listening...";
        });
    </script>
</body>
</html>
```

## Tips for Best Results

### With Picovoice:
1. **Free Tier**: 10,000 wake word detections/month
2. **Model Updates**: Can retrain instantly if needed
3. **Multi-Platform**: Same model works everywhere

### Combining Both Systems:
- Use Picovoice for primary wake word ("OK Frank")
- Use openWakeWord for command phrases ("lights on", "play music")
- Run both in parallel for redundancy

## Troubleshooting

### Common Issues:
1. **"Invalid access key"**: Check your Picovoice console for the key
2. **No detection**: Ensure microphone permissions are granted
3. **High CPU**: Use one system at a time if needed

### Performance Tuning:
```python
# Adjust Picovoice sensitivity (0.0 to 1.0)
porcupine = pvporcupine.create(
    access_key=key,
    keyword_paths=[model_path],
    sensitivities=[0.5]  # Default is 0.5
)
```

## Next Steps

1. ✅ Download your "OK Frank" model from Picovoice
2. ✅ Test with the integration script
3. 🔄 Train additional phrases if needed
4. 🚀 Deploy to production!

## Resources
- [Picovoice Docs](https://picovoice.ai/docs/)
- [Picovoice Console](https://console.picovoice.ai/)
- [openWakeWord GitHub](https://github.com/dscripka/openWakeWord)
