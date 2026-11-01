import os
import asyncio
import logging
import subprocess
import json
import base64
from typing import Dict, Optional, Any, List
import requests
from dotenv import load_dotenv
import edge_tts
from utils.config import LANGUAGES

# Load environment variables
load_dotenv()

# Try importing ElevenLabs
try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

"""
TTS Generator Module.
Generates speech using Sarvam AI Bulbul (primary for Indian languages),
Microsoft Edge TTS (fallback), or ElevenLabs (premium).
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
            
        # Sarvam AI Config (Primary for Indian languages)
        self.sarvam_api_key = os.getenv("SARVAM_API_KEY")
        self.use_sarvam = bool(self.sarvam_api_key)
        if self.use_sarvam:
            logger.info(f"Initialized Sarvam AI Bulbul TTS for {language_code} (gender: {voice_gender})")
            
        # Edge TTS Voice (Fallback or international languages)
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
                logger.error(f"Failed to init ElevenLabs client: {e}. Falling back to Sarvam/Edge TTS.")
                self.use_elevenlabs = False
                
        # MMS VITS Config (Primary local AI fallback over edge_tts)
        self.use_mms = False
        self.mms_code = self.lang_config.get("mms_code")
        self.mms_model = None
        self.mms_tokenizer = None
        
        # Prefer Edge TTS by default for fast, natural neural speech
        self.use_mms = False
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
        
    async def _generate_sarvam_tts(self, text: str, output_path: str, pace: float = 1.0) -> None:
        """Generate using Sarvam AI Bulbul TTS (natural Indian voices)."""
        def run_sarvam():
            target_lang_code = self.lang_config.get("code", f"{self.language_code}-IN")
            speaker = "shubh" if self.voice_gender == "male" else "ritu"
            
            payload = {
                "inputs": [text],
                "target_language_code": target_lang_code,
                "speaker": speaker,
                "model": "bulbul:v3",
                "audio_format": "mp3",
                "speech_sample_rate": 22050
            }
            if 0.5 <= pace <= 2.0 and pace != 1.0:
                payload["pace"] = round(pace, 2)
                
            headers = {
                "api-subscription-key": self.sarvam_api_key,
                "Content-Type": "application/json"
            }
            resp = requests.post("https://api.sarvam.ai/text-to-speech", headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                raise RuntimeError(f"Sarvam TTS failed ({resp.status_code}): {resp.text}")
                
            res_data = resp.json()
            audios = res_data.get("audios", [])
            if not audios:
                raise RuntimeError("Sarvam TTS returned no audio data")
                
            audio_bytes = base64.b64decode(audios[0])
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_sarvam)

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
            import shutil
            shutil.copy(input_path, output_path)

    def _get_audio_duration(self, file_path: str) -> float:
        """Get audio duration using ffmpeg."""
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

    async def _generate_with_retry(self, text: str, raw_path: str, pace: float = 1.0):
        """Retry logic for generation with dynamic pace."""
        max_retries = 3
        edge_rate = f"{int((pace - 1.0) * 100):+d}%"
        for attempt in range(max_retries):
            try:
                if self.use_sarvam:
                    try:
                        await self._generate_sarvam_tts(text, raw_path, pace=pace)
                    except Exception as e:
                        logger.warning(f"Sarvam TTS attempt {attempt+1} failed: {e}. Trying Edge TTS fallback...")
                        await self._generate_edge_tts(text, raw_path, rate=edge_rate)
                elif self.use_elevenlabs:
                    await self._generate_elevenlabs(text, raw_path)
                else:
                    await self._generate_edge_tts(text, raw_path, rate=edge_rate)
                return
            except Exception as e:
                logger.warning(f"TTS Attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep((attempt + 1) * 2)

    def generate_speech(self, text: str, output_path: str, target_duration: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate speech, normalize it, and adjust speed adaptively based on sentence length and video slot.
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
            
            # 1. Compute dynamic pace according to sentence words and video slot
            pace = 1.0
            if target_duration and target_duration > 0:
                words = text.split()
                # Average natural speaking rate for Indian languages: ~2.5 words/second
                est_natural_duration = len(words) / 2.5
                required_pace = est_natural_duration / target_duration
                # Smoothly clamp between 0.90x (calm) and 1.25x (brisk)
                pace = round(max(0.90, min(1.25, required_pace)), 2)
                logger.info(f"Dynamic pace for segment: {pace}x (target={target_duration:.2f}s, words={len(words)})")

            # 2. Generate Raw Audio with dynamic pace natively in Sarvam / Edge
            loop.run_until_complete(self._generate_with_retry(text, raw_path, pace=pace))
            
            if not os.path.exists(raw_path):
                raise RuntimeError("Audio file was not created")

            # 3. Normalize Audio
            normalized_path = output_path.replace(".mp3", "_norm.mp3")
            self._normalize_audio(raw_path, normalized_path)
            
            # 4. Check Duration & Micro-adjust only if needed
            duration = self._get_audio_duration(normalized_path)
            final_path = output_path
            
            if target_duration and duration > 0:
                ratio = duration / target_duration
                # Only apply secondary atempo if still over by > 10%
                if ratio > 1.10:
                    speed_factor = min(1.15, ratio)
                    logger.info(f"Fine-tuning audio tempo by {speed_factor:.2f}x to fit video slot perfectly.")
                    filter_str = f"atempo={speed_factor:.2f}"
                    cmd = [
                        "ffmpeg", "-i", normalized_path,
                        "-filter:a", filter_str,
                        "-y", final_path
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    duration = self._get_audio_duration(final_path)
                else:
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
