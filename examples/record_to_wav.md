

### Usage examples (from repo root, venv active)

- Fixed-length recording (15 seconds, default path under recordings/)
```powershell
python -m examples.record_to_wav --mode fixed --seconds 15
```

- Fixed-length with custom output file
```powershell
python -m examples.record_to_wav --mode fixed --seconds 20 --out .\recordings\memo_2025-10-27.wav
```

- Record until trailing silence (e.g., stop after ~1.2s of silence)
```powershell
python -m examples.record_to_wav --mode silence --silence_ms 1200
```

- Adjust silence sensitivity (lower rms_thresh = more sensitive to quiet; higher = requires louder speech)
```powershell
python -m examples.record_to_wav --mode silence --silence_ms 1500 --rms_thresh 350
```

Notes:
- Output WAVs are 16 kHz mono PCM and default to `recordings/rec_<mode>_<timestamp>.wav` if `--out` is not set.
- Requires `pyaudio` in your venv. If missing: `pip install pyaudio`.

- Summary: Use `--mode fixed` with `--seconds N` for a timed capture, or `--mode silence` with `--silence_ms`/`--rms_thresh` to auto-stop on silence; files save under `recordings/` by default.