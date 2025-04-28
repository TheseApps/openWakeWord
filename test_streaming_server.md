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