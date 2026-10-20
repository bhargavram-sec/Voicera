import os
import asyncio
import logging
import subprocess
import json
from typing import Dict, Optional, Any, List
import edge_tts
from utils.config import LANGUAGES

# Try importing HuggingFace MMS VITS
try:
    import torch
    from transformers import VitsModel, AutoTokenizer
    import scipy.io.wavfile
    import tempfile
    MMS_AVAILABLE = True
except ImportError:
    MMS_AVAILABLE = False

# Try importing ElevenLabs
try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

"""
TTS Generator Module.
Generates speech using Microsoft Edge TTS (free) or ElevenLabs (premium).
Includes audio normalization and smart speed adjustment.
"""

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSGenerator:
    def __init__(self, language_code: str, voice_gender: str = "female"):
        """
        Initialize TTS Generator.
        
        Args:
            language_code: Language code (e.g., 'hi', 'ta').
            voice_gender: 'male' or 'female'.
        """
        self.language_code = language_code
        self.voice_gender = voice_gender
        self.lang_config = LANGUAGES.get(language_code)
        
        if not self.lang_config:
            raise ValueError(f"Unsupported language: {language_code}")
            
        # Edge TTS Voice
        self.edge_voice = self.lang_config["voices"].get(voice_gender)
        if not self.edge_voice:
            self.edge_voice = list(self.lang_config["voices"].values())[0]
            
        # ElevenLabs Config
        self.use_elevenlabs = False
        self.eleven_api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.client = None
        
        if self.eleven_api_key and ELEVENLABS_AVAILABLE:
            try:
                self.client = ElevenLabs(api_key=self.eleven_api_key)
                self.use_elevenlabs = True
                self.eleven_voice_id = "21m00Tcm4TlvDq8ikWAM" if voice_gender == "female" else "ErXwobaYiN019PkySvjV" 
                logger.info(f"Initialized ElevenLabs TTS for {language_code}")
            except Exception as e:
                logger.error(f"Failed to init ElevenLabs client: {e}. Falling back to MMS/Edge TTS.")
                self.use_elevenlabs = False
                
        # MMS VITS Config (Primary local AI fallback over edge_tts)
        self.use_mms = False
        self.mms_code = self.lang_config.get("mms_code")
        self.mms_model = None
        self.mms_tokenizer = None
        
        if not self.use_elevenlabs and MMS_AVAILABLE and self.mms_code:
            self.use_mms = True
            logger.info(f"Will use MMS TTS model for language: {self.mms_code} as primary natural voice.")
        elif not self.use_elevenlabs:
            logger.info(f"Initialized Edge TTS for {language_code} with voice: {self.edge_voice}")

    async def _generate_edge_tts(self, text: str, output_path: str, rate: str = "+0%") -> None:
        """Generate using Edge TTS"""
        communicate = edge_tts.Communicate(text, self.edge_voice, rate=rate)
        await communicate.save(output_path)

    async def _generate_elevenlabs(self, text: str, output_path: str) -> None:
        """Generate using ElevenLabs"""
        def run_eleven():
            if not self.client:
                raise RuntimeError("ElevenLabs client not initialized")
            audio_generator = self.client.text_to_speech.convert(
                text=text, voice_id=self.eleven_voice_id,
                model_id="eleven_multilingual_v2", output_format="mp3_44100_128"
            )
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_eleven)
        
    async def _generate_mms_tts(self, text: str, output_path: str) -> None:
        """Generate using HuggingFace MMS VITS models dynamically."""
        def run_mms():
            if not self.mms_model:
                model_name = f"facebook/mms-tts-{self.mms_code}"
                # Lazy load model into memory
                self.mms_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.mms_model = VitsModel.from_pretrained(model_name)
                # Optimization for Mac if user has M1/M2/M3
                if torch.backends.mps.is_available():
                    self.mms_model.to("mps")
            
            inputs = self.mms_tokenizer(text, return_tensors="pt")
            
            if torch.backends.mps.is_available():
                inputs = {k: v.to("mps") for k, v in inputs.items()}
                
            with torch.no_grad():
                output = self.mms_model(**inputs).waveform
                
            audio_data = output.cpu().numpy().squeeze()
            
            # Save to temporary WAV, then ffmpeg it to raw_path (mp3 format)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                scipy.io.wavfile.write(tmp_wav.name, rate=self.mms_model.config.sampling_rate, data=audio_data)
                tmp_wav_path = tmp_wav.name
                
            # Convert WAV to MP3 using ffmpeg
            try:
                cmd = ["ffmpeg", "-i", tmp_wav_path, "-y", output_path]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            finally:
                if os.path.exists(tmp_wav_path):
                    os.remove(tmp_wav_path)
                    
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_mms)

    def _normalize_audio(self, input_path: str, output_path: str):
        """
        Apply loudnorm to normalize audio levels.
        """
        try:
            cmd = [
                "ffmpeg", "-i", input_path,
                "-filter:a", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-ar", "44100", "-ac", "2",
                "-y", output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error(f"Normalization failed: {e}. Using original.")
            # Fallback copy
            import shutil
            shutil.copy(input_path, output_path)

    def _get_audio_duration(self, file_path: str) -> float:
        """Get audio duration using ffmpeg because stripped ffprobe lacks show_entries."""
        try:
            cmd = ["ffmpeg", "-i", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stderr
            import re
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
            if match:
                hours, mins, secs = map(float, match.groups())
                return hours * 3600 + mins * 60 + secs
        except Exception as e:
            logger.error(f"Failed to get duration for {file_path}: {e}")
        return 0.0

    async def _generate_with_retry(self, text: str, raw_path: str):
        """Retry logic for generation."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.use_elevenlabs:
                    await self._generate_elevenlabs(text, raw_path)
                elif self.use_mms:
                    try:
                        await self._generate_mms_tts(text, raw_path)
                    except Exception as e:
                        logger.error(f"MMS TTS failed: {e}. Falling back to Edge TTS.")
                        self.use_mms = False
                        await self._generate_edge_tts(text, raw_path)
                else:
                    await self._generate_edge_tts(text, raw_path)
                return
            except Exception as e:
                logger.warning(f"TTS Attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep((attempt + 1) * 2)

    def generate_speech(self, text: str, output_path: str, target_duration: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate speech, normalize it, and optionally adjust speed (carefully).
        """
        try:
            # Check event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            raw_path = output_path.replace(".mp3", "_raw.mp3")
            
            # 1. Generate Raw Audio
            loop.run_until_complete(self._generate_with_retry(text, raw_path))
            
            if not os.path.exists(raw_path):
                raise RuntimeError("Audio file was not created")

            # 2. Normalize Audio
            normalized_path = output_path.replace(".mp3", "_norm.mp3")
            self._normalize_audio(raw_path, normalized_path)
            
            # 3. Check Duration & Adjust if CRITICAL
            duration = self._get_audio_duration(normalized_path)
            final_path = output_path
            
            if target_duration and duration > 0:
                diff = duration - target_duration
                ratio = duration / target_duration
                
                # Logic:
                # If audio is much longer (e.g. > 20% longer), we need to speed up.
                # But we CAP speedup at 1.25x to avoid robotic artifacts.
                # If audio is shorter, we generally DON'T slow down (leave gaps).
                
                if ratio > 1.05: # Only if > 5% longer
                    speed_factor = ratio
                    
                    # Cap speedup
                    if speed_factor > 1.25:
                        logger.warning(f"Audio required {speed_factor:.2f}x speedup. Capping at 1.25x to preserve quality.")
                        speed_factor = 1.25
                        # Result will be longer than target_duration, causing slight desync.
                        # This matches requirement: "Allow slight mismatch"
                    
                    # Apply tempo filter via ffmpeg
                    # tempo filter > 1.0 speeds up
                    filter_str = f"atempo={speed_factor}"
                    
                    cmd = [
                        "ffmpeg", "-i", normalized_path,
                        "-filter:a", filter_str,
                        "-y", final_path
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Recalculate duration
                    duration = self._get_audio_duration(final_path)
                else:
                    # No speed change needed
                    import shutil
                    shutil.move(normalized_path, final_path)
            else:
                 import shutil
                 shutil.move(normalized_path, final_path)

            # Cleanup
            if os.path.exists(raw_path): os.remove(raw_path)
            if os.path.exists(normalized_path) and normalized_path != final_path: os.remove(normalized_path)

            return {
                "audio_path": final_path,
                "duration": duration,
                "text": text
            }
            
        except Exception as e:
            logger.error(f"TTS Generation failed: {e}")
            # Generate silence as fallback?
            raise RuntimeError(f"TTS Generation failed: {e}")

if __name__ == "__main__":
    # Test
    try:
        gen = TTSGenerator("hi", "female")
        # gen.generate_speech("नमस्ते", "test.mp3")
    except Exception as e:
        print(f"Error: {e}")
