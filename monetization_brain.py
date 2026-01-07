"""
Monetization Brain Module (Gemini Authority Mode)
-------------------------------------------------
Acts as the YOUTUBE SHORTS CAPTION EDITOR & SAFETY OFFICER.
Goal: Pass YPP Human Review by enforcing strictly editorial/transformative captions.

**SINGLE SOURCE OF TRUTH: GEMINI**
- No OpenAI usage.
- Strict Text Parsing for robustness.
"""

import os
import json
import logging
import re
import google.generativeai as genai
from typing import Dict, Optional, List
from datetime import datetime
import shutil
import tempfile

logger = logging.getLogger("monetization_brain")

# YPP STRICT EDITOR PROMPT (GEMINI AUTHORITY)
# YPP STRICT EDITOR PROMPT (GEMINI AUTHORITY)
EDITOR_PROMPT = """
YOU ARE THE MONETIZATION & CAPTION AUTHORITY.

GLOBAL RULES (HARD):
- GEMINI IS THE ONLY MODEL USED.
- NEVER output labels like: "Aesthetic", "Editorial", "Safe", "Approved".
- NEVER overwrite captions with classification words.
- ONE caption = ONE truth.

CAPTION GENERATION RULES
You must generate a DISPLAY-READY caption.
- Natural, human, editorial tone
- Monetization safe (YPP friendly)
- No sexual wording
- No thirst language
- Emojis allowed (max 1)
- Length: 8-15 words ONLY
- Do NOT include hashtags
- Do NOT include usernames
- Do NOT include formatting symbols (*, #, [], etc.)

Examples of GOOD captions:
- "Mixing vintage denim with modern confidence for a timeless look"
- "A quiet moment of reflection capturing the essence of style"
- "Every detail feels intentional making this outfit truly stand out"
- "Effortless energy that defines the modern aesthetic perfectly"

RETURN FORMAT (CRITICAL)
YOUTUBE POLICY KNOWLEDGE (STRICT):
- **Reused Content (BAD)**: Clips with minimal edits, templates, music collections, or non-verbal reactions. AUTOMATIC REJECTION.
- **Transformative Content (GOOD)**:
    - Must add *significant* original value.
    - **Critical Review**: Uses clips to support an argument.
    - **Editorial Commentary**: Voiceover that recontextualizes the visual.
    - **Visual Reconstruction**: Significant changes to speed, color, and focus (zoom/crop).

ANALYSIS INSTRUCTIONS:
1. Review 'Transformations Applied'.
2. If 'Voiceover' OR 'Inpainting' (Logo Removal) is present -> Score > 40 (Transformative).
3. If ONLY 'Speed'/'Color' -> Score < 30 (Derivative).
4. If Raw -> Score 0.

You MUST return valid JSON ONLY.

Schema:
{{
  "caption_final": "<DISPLAY TEXT>",
  "approved": true,
  "risk_level": "LOW|MEDIUM|HIGH",
  "risk_reason": "<SHORT 1-SENTENCE REASON>",
  "transformation_score": <0-100>,
  "verdict": "<Transformative|Derivative|High Risk>"
}}

Rules:
- caption_final MUST be the exact text to show on screen
- approved MUST be true or false
- risk_level MUST be one of LOW, MEDIUM, HIGH based on YPP safety (sexual/violent/controversial = HIGH)
- risk_reason MUST explicitly explain WHY the risk level was chosen (e.g. "Safe fashion content", "Potential skin exposure", "Explicit language")
- transformation_score represents how much the content differs from raw source (0=Raw, 100=Original). 
- verdict should be "Transformative" if score > 30, else "Derivative".
- NEVER return analysis text
- NEVER return explanations
- NEVER return labels instead of captions

INPUT:
Visual Description: {input_description}
Niche: {content_origin}
Transformations Applied: {transformations}
"""

class MonetizationStrategist:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.provider = "none"
        self.model = None
        
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                self.model = genai.GenerativeModel(model_name)
                self.provider = "gemini"
                logger.info(f"🧠 YPP Editor Brain: ACTIVE (Model: {model_name})")
            except Exception as e:
                logger.error(f"❌ Gemini Brain Init Failed: {e}")
        else:
            logger.warning("🧠 YPP Editor Brain: INACTIVE (No Gemini Key)")

    def analyze_content(self, title: str, duration: float, transformations: Dict = {}) -> Dict:
        """
        Analyzes content using Gemini as the sole authority.
        """
        if self.provider != "gemini" or not self.model:
            return self._fallback_response(title)

        try:
            # 1. Input Sanitization (Safety First)
            # Remove control chars, strip whitespace, truncate to 200 chars
            clean_title = re.sub(r'[\x00-\x1F\x7F]', '', title).strip()
            clean_title = clean_title[:200]
            
            # Prepare Prompt
            # ORIGIN LOGIC: Standardize to public_social_media for internal logic, but concise for prompt
            origin = "public_social_media" 
            
            # Format transformation string
            trans_str = "None"
            if transformations:
                trans_str = ", ".join([f"{k}: {v}" for k,v in transformations.items()])
                
            final_prompt = EDITOR_PROMPT.format(
                input_description=clean_title, 
                content_origin=origin,
                transformations=trans_str
            )
            
            # Call Gemini
            response = self.model.generate_content(
                final_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3, 
                    response_mime_type="application/json"
                )
            )
            
            response_text = response.text.strip()
            logger.info(f"🧠 RAW GEMINI RESPONSE: {response_text}")
            return self._parse_json_response(response_text, clean_title)

        except Exception as e:
            logger.error(f"🧠 Brain Analysis Error: {e}")
            return self._fallback_response(title, error=e)

    def _parse_json_response(self, text: str, original_title: str) -> Dict:
        """
        Parses strictly JSON response with Regex extraction and Logic Validation.
        """
        try:
            # 1. Extract JSON Object (Strict Regex)
            # Look for non-greedy match between first { and last }
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if not match:
                 logger.warning("🧠 Invalid JSON format: No brackets found.")
                 return self._fallback_response(original_title, error=ValueError("Invalid JSON"))
                 
            json_str = match.group(1)
            data = json.loads(json_str)
            
            if not data.get("approved"):
                 return {
                    "final_caption": original_title, # Fallback but rejected
                    "risk_level": "HIGH",
                    "risk_reason": data.get("risk_reason", "Brain rejected content"),
                    "source": "public_social_media" 
                 }
            
            # 2. Strict Caption Validation
            caption = data.get("caption_final", "").strip()
            
            # Rule A: Length Upgrade (8-15 preferred, allow up to 25 words due to new micro-commentary)
            word_count = len(caption.split())
            if word_count < 4 or word_count > 25:
                 logger.warning(f"🧠 Validation Fail: Length ({word_count}) - '{caption}'")
                 return self._fallback_response(original_title, error=ValueError("Validation: Length"))
                 
            # Rule B: Banned Prefixes
            lower_cap = caption.lower()
            if lower_cap.startswith(("caption:", "title:", "description:", "output:")):
                 logger.warning(f"🧠 Validation Fail: Prefix - '{caption}'")
                 return self._fallback_response(original_title, error=ValueError("Validation: Prefix"))

            # Rule C: Metadata / Classifications
            banned_keywords = ["editorial", "approved", "safe context", "public domain", "ypp safe"]
            if lower_cap in banned_keywords:
                 logger.warning(f"🧠 Validation Fail: Classification Word - '{caption}'")
                 return self._fallback_response(original_title, error=ValueError("Validation: Classification"))

            # Rule D: Hashtags / Allowlist characters
            if "#" in caption or "@" in caption:
                 logger.warning(f"🧠 Validation Fail: Hashtag/Mention - '{caption}'")
                 return self._fallback_response(original_title, error=ValueError("Validation: Hashtag"))

            # Success
            return {
                "approved": True,
                "final_caption": caption, 
                "caption_style": "EDITORIAL",
                "risk_level": data.get("risk_level", "LOW"),
                "risk_reason": data.get("risk_reason", "Approved by safety filter"),
                "transformation_score": data.get("transformation_score", 10),
                "verdict": data.get("verdict", "Derivative"),
                "source": "public_social_media"
            }
            
        except json.JSONDecodeError:
            logger.error(f"🧠 JSON Decode Failed: {text[:50]}...")
            return self._fallback_response(original_title, error=ValueError("JSON Decode"))
        except Exception as e:
            logger.error(f"🧠 Parsing Error: {e}")
            return self._fallback_response(original_title, error=e)

    def _fallback_response(self, caption: str, error: Exception = None) -> Dict:
        """
        Returns a FAIL-SAFE response using Local Templates.
        Normalized Schema to match Success case.
        """
        safe_cap = self.get_safe_fallback()
        
        # Default Values
        risk = "LOW"
        reason = "Brain Offline - Used Safe Template"
        
        # Check for Quota Error
        if error:
            err_str = str(error).lower()
            if "429" in err_str or "quota" in err_str:
                risk = "UNKNOWN"
                reason = "Quota Exceeded (429 Error), so Brain is Offline."
        
        return {
            "approved": True, # Fallback is ostensibly safe
            "final_caption": safe_cap,
            "caption": safe_cap, # Legacy key
            "caption_style": "FALLBACK",
            "risk_level": risk, 
            "risk_reason": reason,
            "source": "public_social_media"
        }

    def get_safe_fallback(self) -> str:
        """
        Returns a guaranteed safe caption from:
        1. Local Storage (caption_prompt.json)
        2. Hardcoded Revenue-Safe Templates
        """
        try:
            if os.path.exists("caption_prompt.json"):
                with open("caption_prompt.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "caption_final" in data and len(data["caption_final"]) > 5:
                         val = data["caption_final"]
                         # Quick re-validate stored caption
                         if "#" not in val and len(val.split()) >= 2:
                             logger.info(f"🛡️ Using Stored Fallback: {val}")
                             return val
        except Exception: pass
            
        return "A quiet moment captured today"

    def save_successful_caption(self, caption: str, source: str, style: str):
        """
        Persists the safe caption to disk ATOMICALLY.
        """
        try:
            data = {
                "caption_final": caption,
                "last_source": source,
                "timestamp": datetime.now().isoformat()
            }
            
            # Atomic Write via Temp
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=".", encoding='utf-8') as tmp:
                json.dump(data, tmp, indent=2)
                tmp_path = tmp.name
                
            shutil.move(tmp_path, "caption_prompt.json")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to save caption persistence: {e}")

# Singleton
brain = MonetizationStrategist()
