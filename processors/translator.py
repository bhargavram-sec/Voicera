
"""
Translation Module.
Handles text translation while preserving technical terms.
"""

import re
import logging
from typing import List, Dict, Tuple, Any
from deep_translator import GoogleTranslator
from utils.config import TECHNICAL_TERMS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationEngine:
    def __init__(self, source_lang: str, target_lang: str):
        """
        Initialize translation engine.
        
        Args:
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'hi')
        """
        # Normalize codes (e.g. 'en-US' -> 'en')
        self.source_lang = source_lang.split('-')[0].lower() if source_lang else 'auto'
        self.target_lang = target_lang.split('-')[0].lower()
        
        # Skip translation if languages are effectively the same
        self.skip_translation = (self.source_lang == self.target_lang)
        self.translator = None

        if not self.skip_translation:
            try:
                # Validate source/target support or let library handle it
                # We try to init with specific source first
                self.translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)
            except Exception as e:
                logger.warning(f"Translator init failed for source='{self.source_lang}': {e}. Retrying with source='auto'.")
                try:
                    self.translator = GoogleTranslator(source='auto', target=self.target_lang)
                except Exception as e2:
                    logger.error(f"Translator init failed even with auto: {e2}")
                    # Will fail gracefully during translate_segment by returning original text
        
        # Compile regex for technical terms (case-insensitive)
        # Sort by length descending to match longest terms first
        sorted_terms = sorted(TECHNICAL_TERMS, key=len, reverse=True)
        # Bounded by \b to match whole words/phrases
        self.term_pattern = re.compile(
            r'\b(' + '|'.join(map(re.escape, sorted_terms)) + r')\b', 
            re.IGNORECASE
        )

    def detect_technical_terms(self, text: str) -> List[str]:
        """
        Find all technical terms in the text.
        """
        return self.term_pattern.findall(text)

    def _replace_terms_with_placeholders(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace technical terms with numbered placeholders (e.g., __TERM_0__).
        Returns modified text and a map of placeholders to original terms.
        """
        mapping = {}
        count = 0
        
        def replace(match):
            nonlocal count
            term = match.group(0)
            placeholder = f"__TERM_{count}__"
            mapping[placeholder] = term
            count += 1
            return placeholder

        masked_text = self.term_pattern.sub(replace, text)
        return masked_text, mapping

    def _restore_terms(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Replace placeholders back with original technical terms.
        """
        for placeholder, term in mapping.items():
            # Simply replace usually works
            text = text.replace(placeholder, term)
            # Handle potential spaces/formatting issues introduced by translation engiens
            # e.g., "__ TERM_0 __" instead of "__TERM_0__"
            # We try a few variants if strict replace didn't catch it (optional enhancement)
            
            # Additional cleanup for spaced variants
            text = text.replace(placeholder.replace("__", " __"), term) 
            text = text.replace(placeholder.replace("TERM", " TERM"), term)
            
        return text

    def translate_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate a single segment preserving technical terms.
        
        Args:
            segment: A dictionary segment from the transcriber.
            
        Returns:
            Dictionary with translation details.
        """
        original_text = segment['text']
        start_time = segment['start']
        end_time = segment['end']
        duration = end_time - start_time
        
        # If languages match or translator broken, return original
        if self.skip_translation or not self.translator:
            logger.info(f"Skipping translation (Same Lang or No Translator): {original_text[:20]}...")
            return {
                "original_text": original_text,
                "translated_text": original_text,
                "preserved_terms": [],
                "expansion_ratio": 1.0,
                "start": start_time,
                "end": end_time,
                "duration": duration,
                "id": segment.get("id")
            }
        
        try:
            # 1. Mask technical terms
            masked_text, mapping = self._replace_terms_with_placeholders(original_text)
            
            # 2. Translate
            # deep-translator handles limits? Usually text segments are short enough.
            translated_text_masked = self.translator.translate(masked_text)
            
            # If API returns None or empty
            if not translated_text_masked:
                raise ValueError("Translation returned empty response")

            # 3. Restore terms
            final_text = self._restore_terms(translated_text_masked, mapping)
            
            # 4. Check length/expansion
            expansion_ratio = len(final_text) / len(original_text) if len(original_text) > 0 else 1.0
            
            return {
                "original_text": original_text,
                "translated_text": final_text,
                "preserved_terms": list(mapping.values()),
                "expansion_ratio": expansion_ratio,
                "start": start_time,
                "end": end_time,
                "duration": duration,
                "id": segment.get("id")
            }
            
        except Exception as e:
            logger.error(f"Translation error source={self.source_lang} target={self.target_lang} for segment {segment.get('id')}: {e}")
            # Fallback: return original text if translation fails
            return {
                "original_text": original_text,
                "translated_text": original_text, # Fallback
                "preserved_terms": [],
                "expansion_ratio": 1.0,
                "start": start_time,
                "end": end_time,
                "duration": duration,
                "id": segment.get("id"),
                "error": str(e)
            }

    def _expand_numbers(self, text: str, lang_code: str) -> str:
        """
        Convert numbers to words in target language if supported.
        """
        try:
            from num2words import num2words
            # Map common codes to num2words supported languages
            # extending this map as needed.
            lang_map = {
                'en': 'en',
                'hi': 'hi',
                'gu': 'gu', # Gujarati
                'kn': 'kn', # Kannada
                'ml': 'ml', # Malayalam (supported?) - likely 'en' fallback if not
                'mr': 'mr', # Marathi
                'pa': 'pa', # Punjabi
                'te': 'en', # Telugu num2words support might be limited, fallback to english or check specific lib
                'ta': 'en', # Tamil same
            }
            
            # Use 'en' as safe default if specific lang not supported by library
            n2w_lang = lang_map.get(lang_code, 'en') 
            
            def replace_num(match):
                num_str = match.group()
                # Handle comma/decimals or plain digits
                try:
                    val = float(num_str.replace(',', ''))
                    # If integer, convert as int
                    if val.is_integer():
                        return num2words(int(val), lang=n2w_lang)
                    return num2words(val, lang=n2w_lang)
                except:
                    return num_str

            # Regex for numbers
            return re.sub(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', replace_num, text)
        except ImportError:
            logger.warning("num2words not installed. Skipping number expansion.")
            return text
        except Exception as e:
            logger.warning(f"Error expanding numbers: {e}")
            return text

    def _enhance_text(self, text: str) -> str:
        """
        Apply text enhancements:
        - Number expansion
        - Punctuation fixes
        - Sentence splitting marks (for TTS pausing)
        """
        # 1. Expand numbers
        text = self._expand_numbers(text, self.target_lang)
        
        # 2. Add pauses for commas (TTS specific, might use <break> tags if SSML supported, 
        # but for now we rely on punctuation)
        # Ensure comma has space
        text = text.replace(',', ', ')
        
        # 3. Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 4. Remove Roman chars if target is Indian language but keep Technical terms?
        # This is risky if we have "iPhone 15". Technical terms are preserved via placeholders.
        # But if translation left some english words, we might want to keep them or transliterate.
        # For now, we trust the translation + technical term preservation.
        
        return text

    def translate_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate a single segment preserving technical terms.
        """
        original_text = segment['text']
        start_time = segment['start']
        end_time = segment['end']
        duration = end_time - start_time
        
        # If languages match or translator broken, return original
        if self.skip_translation or not self.translator:
            logger.info(f"Skipping translation (Same Lang or No Translator): {original_text[:20]}...")
            return {
                "original_text": original_text,
                "translated_text": original_text,
                "preserved_terms": [],
                "expansion_ratio": 1.0,
                "start": start_time,
                "end": end_time,
                "duration": duration,
                "id": segment.get("id")
            }
        
        try:
            # 1. Mask technical terms
            masked_text, mapping = self._replace_terms_with_placeholders(original_text)
            
            # 2. Translate
            translated_text_masked = self.translator.translate(masked_text)
            
            if not translated_text_masked:
                raise ValueError("Translation returned empty response")

            # 3. Restore terms
            restored_text = self._restore_terms(translated_text_masked, mapping)
            
            # 4. Enhance Text (New Layer)
            final_text = self._enhance_text(restored_text)
            
            # 5. Check length/expansion
            expansion_ratio = len(final_text) / len(original_text) if len(original_text) > 0 else 1.0
            
            return {
                "original_text": original_text,
                "translated_text": final_text,
                "preserved_terms": list(mapping.values()),
                "expansion_ratio": expansion_ratio,
                "start": start_time,
                "end": end_time,
                "duration": duration,
                "id": segment.get("id")
            }
            
        except Exception as e:
            logger.error(f"Translation error for segment {segment.get('id')}: {e}")
            return {
                "original_text": original_text,
                "translated_text": original_text, # Fallback
                "preserved_terms": [],
                "expansion_ratio": 1.0,
                "start": start_time,
                "end": end_time,
                "duration": duration,
                "id": segment.get("id"),
                "error": str(e)
            }
