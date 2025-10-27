
### Wakeword dispatcher: practical usage (from repo root, venv active)

- Basic run (default routes, ONNX)
```powershell
python -m examples.wakeword_dispatcher --inference_framework onnx
```
- With a single explicit model
```powershell
python -m examples.wakeword_dispatcher --inference_framework onnx --model_path .\models\hey_mycroft_v0.1.onnx
```
- Tune detection sensitivity and repeat suppression
```powershell
python -m examples.wakeword_dispatcher --threshold 0.40 --debounce 1.5
```
- Enable voice activity gating (0 disables VAD; try small values like 0.1–0.2)
```powershell
python -m examples.wakeword_dispatcher --vad_threshold 0.1
```
- Use TFLite models instead of ONNX
```powershell
python -m examples.wakeword_dispatcher --inference_framework tflite
```

### Custom routes file
- Create `routes.json` in the repo root:
```json
{
  "alexa_v0.1": {
    "type": "second_stage",
    "command": ["python", "-m", "examples.direct_wakeword_test_simple", "--inference_framework", "onnx", "--model_path", "models/alexa_v0.1.onnx"]
  },
  "hey_jarvis_v0.1": {
    "type": "fixed_record",
    "seconds": 20,
    "out_pattern": "recordings/jarvis_{ts}.wav"
  },
  "stop": {
    "type": "command",
    "command": ["cmd", "/c", "echo", "Stopping..."]
  }
}
```
- Run with the custom routes:
```powershell
python -m examples.wakeword_dispatcher --routes .\routes.json
```

### What happens on activation
- Fixed record: spawns `examples.record_to_wav` to save WAV under `recordings/` using `out_pattern`.
- Second stage: spawns another listener process (e.g., `examples.direct_wakeword_test_simple`).
- Command: runs any shell command you define.

### Logs and outputs
- Activations are appended to `logs\dispatcher_YYYYMMDD.log`.
- Recordings are written to `recordings\` (ensure the folder is writable).

Troubleshooting
- Missing audio backend: `pip install pyaudio`. On Windows, if needed: `pip install pipwin && pipwin install pyaudio`.
- No detections: lower `--threshold` (e.g., 0.35) or set `--vad_threshold 0`.
- Too many repeats: increase `--debounce` (e.g., 2.0).

- Summary:
  - Run with `--inference_framework onnx` (or `tflite`), tune `--threshold`, `--debounce`, and optional `--vad_threshold`.
  - Use `--routes .\routes.json` to map wakewords to actions: second-stage processes, fixed-length recording, or commands.
  - Logs in `logs/`, recordings in `recordings/`.