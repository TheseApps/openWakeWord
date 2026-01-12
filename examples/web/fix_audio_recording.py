"""
Fix for audio recording format issue
Converts WebM/Opus to PCM WAV format
"""

import asyncio
from aiohttp import web
import os
import datetime
import subprocess
import tempfile
import wave

async def save_recording_handler_fixed(request):
    """Fixed handler that converts WebM to WAV"""
    try:
        # Create saved_clips directory if needed
        if not os.path.exists('saved_clips'):
            os.makedirs('saved_clips')
            
        reader = await request.multipart()
        field = await reader.next()
        
        if field and field.name == 'audio':
            # Generate filename
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_webm = os.path.join('saved_clips', f'temp_{timestamp}.webm')
            final_wav = os.path.join('saved_clips', f'{timestamp}.wav')
            
            print(f"Saving WebM temporarily to: {temp_webm}")
            
            # Save the WebM data first
            with open(temp_webm, 'wb') as f:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    f.write(chunk)
            
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                
                # Convert WebM to WAV using ffmpeg
                cmd = [
                    'ffmpeg',
                    '-i', temp_webm,           # Input file
                    '-acodec', 'pcm_s16le',    # 16-bit PCM
                    '-ar', '16000',            # 16kHz sample rate
                    '-ac', '1',                # Mono
                    '-y',                      # Overwrite output
                    final_wav                  # Output file
                ]
                
                print(f"Converting with: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"Successfully converted to: {final_wav}")
                    # Clean up temp file
                    os.remove(temp_webm)
                    return web.Response(text=f"File saved as {final_wav}")
                else:
                    print(f"FFmpeg error: {result.stderr}")
                    return web.Response(text=f"Conversion failed: {result.stderr}", status=500)
                    
            except FileNotFoundError:
                print("FFmpeg not found. Install it for audio conversion.")
                print("Download from: https://ffmpeg.org/download.html")
                
                # Fallback: Just rename to indicate it's WebM
                webm_file = os.path.join('saved_clips', f'{timestamp}.webm')
                os.rename(temp_webm, webm_file)
                
                return web.Response(
                    text=f"File saved as {webm_file} (WebM format - install ffmpeg to convert to WAV)",
                    status=200
                )
                
        else:
            return web.Response(text="No audio field found", status=400)
            
    except Exception as e:
        print(f"Error: {e}")
        return web.Response(text=str(e), status=500)


# Alternative: Python-only solution using pydub
async def save_recording_pydub(request):
    """Alternative using pydub library (no ffmpeg needed)"""
    try:
        from pydub import AudioSegment
        
        if not os.path.exists('saved_clips'):
            os.makedirs('saved_clips')
            
        reader = await request.multipart()
        field = await reader.next()
        
        if field and field.name == 'audio':
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_file = os.path.join('saved_clips', f'temp_{timestamp}')
            final_wav = os.path.join('saved_clips', f'{timestamp}.wav')
            
            # Save uploaded data
            with open(temp_file, 'wb') as f:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    f.write(chunk)
            
            # Convert to WAV
            audio = AudioSegment.from_file(temp_file)
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(final_wav, format="wav", parameters=["-acodec", "pcm_s16le"])
            
            os.remove(temp_file)
            print(f"Saved as WAV: {final_wav}")
            
            return web.Response(text=f"File saved as {final_wav}")
            
    except ImportError:
        return web.Response(
            text="pydub not installed. Run: pip install pydub",
            status=500
        )
    except Exception as e:
        return web.Response(text=str(e), status=500)


if __name__ == "__main__":
    print("Audio Recording Format Fix")
    print("=" * 50)
    print("\nThis fixes the WebM -> WAV conversion issue.")
    print("\nOptions:")
    print("1. Install ffmpeg: https://ffmpeg.org/download.html")
    print("2. Or install pydub: pip install pydub")
    print("\nThen update streaming_server.py to use the fixed handler.")