# Custom Wake Word Training Guide

## Quick Start Options

### 🌐 Option 1: Google Colab (Recommended for beginners)
1. Open the [Simple Training Notebook](https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb)
2. Upload one of the `.yml` config files from this folder
3. Run all cells (takes ~45-60 minutes)
4. Download your trained `.onnx` model

### 🖥️ Option 2: Local Training (Linux only)
```bash
cd openWakeWord
python openwakeword/train.py --config examples/custom_models/hey_frank_model.yml
```

### ⚡ Option 3: Commercial Services (Fastest)
- **[Picovoice Console](https://console.picovoice.ai/)** - Train in seconds, free tier available
- **[Sensory VoiceHub](https://www.sensory.com/voicehub/)** - Professional grade, no coding required
- **[SoundHound](https://www.soundhound.com/)** - Enterprise solution

## Configuration Files in This Folder

| Model | Config File | Description |
|-------|------------|-------------|
| "I am" | `i_am_model.yml` | Detects "I am" or "I'm" |
| "Hey Frank" | `hey_frank_model.yml` | Detects "Hey Frank", "OK Frank", "Hi Frank" |
| Template | `additional_models.yml` | Examples for other wake words |

## Training Tips

### For "I am" Model
- **Challenge**: Very short phrase (2 syllables)
- **Solution**: Generate more samples (50k+) and use stricter thresholds
- **Test phrases**: "I am ready", "I am here", "I'm listening"

### For "Hey/OK Frank" Model
- **Challenge**: Personal name recognition
- **Solution**: Include variations and similar-sounding negative examples
- **Test with**: Different accents, speeds, and distances from mic

## Testing Your Models

After training, test your models:

```python
from openwakeword.model import Model

# Load your custom model
model = Model(wakeword_models=["examples/custom_models/hey_frank.onnx"])

# Test with microphone
# Run: python examples/detect_from_microphone.py --model_path examples/custom_models/hey_frank.onnx

# Test with WAV files
model.predict_clip("test_audio.wav")
```

## Model Performance Expectations

| Model Complexity | Training Time | Expected Accuracy | False Positives/Hour |
|-----------------|---------------|-------------------|---------------------|
| Simple (1 phrase) | 30-45 min | 90-95% | <1 |
| Medium (2-3 variations) | 45-60 min | 85-92% | <2 |
| Complex (4+ variations) | 60-90 min | 80-90% | <3 |

## Improving Model Performance

1. **More Training Data**: Increase `n_samples` to 100k+
2. **Better Negatives**: Add similar-sounding words to `custom_negative_phrases`
3. **Augmentation**: Increase `augmentation_rounds` for more variety
4. **Architecture**: Try `layer_size: 64` for complex models
5. **Post-Training**: Adjust detection threshold (default 0.5)

## Community Models

Check out community-trained models at:
- [Home Assistant Wake Words Collection](https://github.com/fwartner/home-assistant-wakewords-collection)
- [OpenWakeWord Model Zoo](https://huggingface.co/collections/davidscripka/openwakeword-models)

## Need Help?

- **Discord**: Join the openWakeWord community
- **Issues**: Report problems on [GitHub](https://github.com/dscripka/openWakeWord/issues)
- **Documentation**: Full docs at [openWakeWord Wiki](https://github.com/dscripka/openWakeWord/wiki)
