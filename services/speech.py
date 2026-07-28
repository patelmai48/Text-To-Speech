import os
import uuid
import re
from collections import Counter
from gtts import gTTS

SUPPORTED_LANGUAGES = [
    {"code": "en", "tld": "com", "name": "English (US)", "voice_id": "en-us", "flag": "🇺🇸", "gender": "Female"},
    {"code": "en", "tld": "co.uk", "name": "English (UK)", "voice_id": "en-uk", "flag": "🇬🇧", "gender": "Female"},
    {"code": "en", "tld": "co.in", "name": "English (India)", "voice_id": "en-in", "flag": "🇮🇳", "gender": "Female"},
    {"code": "en", "tld": "com.au", "name": "English (Australia)", "voice_id": "en-au", "flag": "🇦🇺", "gender": "Female"},
    {"code": "es", "tld": "es", "name": "Spanish (Spain)", "voice_id": "es-es", "flag": "🇪🇸", "gender": "Female"},
    {"code": "es", "tld": "com.mx", "name": "Spanish (Mexico)", "voice_id": "es-mx", "flag": "🇲🇽", "gender": "Female"},
    {"code": "fr", "tld": "fr", "name": "French (France)", "voice_id": "fr-fr", "flag": "🇫🇷", "gender": "Female"},
    {"code": "fr", "tld": "ca", "name": "French (Canada)", "voice_id": "fr-ca", "flag": "🇨🇦", "gender": "Female"},
    {"code": "de", "tld": "de", "name": "German (Germany)", "voice_id": "de-de", "flag": "🇩🇪", "gender": "Female"},
    {"code": "hi", "tld": "co.in", "name": "Hindi (India)", "voice_id": "hi-in", "flag": "🇮🇳", "gender": "Female"},
    {"code": "ja", "tld": "co.jp", "name": "Japanese (Japan)", "voice_id": "ja-jp", "flag": "🇯🇵", "gender": "Female"},
    {"code": "zh-CN", "tld": "com", "name": "Chinese (Mandarin)", "voice_id": "zh-cn", "flag": "🇨🇳", "gender": "Female"},
    {"code": "it", "tld": "it", "name": "Italian (Italy)", "voice_id": "it-it", "flag": "🇮🇹", "gender": "Female"},
    {"code": "pt", "tld": "com.br", "name": "Portuguese (Brazil)", "voice_id": "pt-br", "flag": "🇧🇷", "gender": "Female"},
    {"code": "ru", "tld": "ru", "name": "Russian (Russia)", "voice_id": "ru-ru", "flag": "🇷🇺", "gender": "Female"},
    {"code": "ar", "tld": "com", "name": "Arabic (Standard)", "voice_id": "ar-sa", "flag": "🇸🇦", "gender": "Female"},
    {"code": "ko", "tld": "co.kr", "name": "Korean (South Korea)", "voice_id": "ko-kr", "flag": "🇰🇷", "gender": "Female"},
    
    # High-quality Microsoft Edge Neural Voices (including Male voices)
    {"code": "en", "tld": "edge", "name": "English (US) - Male", "voice_id": "en-us-male", "flag": "🇺🇸", "gender": "Male"},
    {"code": "en", "tld": "edge", "name": "English (UK) - Male", "voice_id": "en-uk-male", "flag": "🇬🇧", "gender": "Male"},
    {"code": "en", "tld": "edge", "name": "English (India) - Male", "voice_id": "en-in-male", "flag": "🇮🇳", "gender": "Male"},
    {"code": "hi", "tld": "edge", "name": "Hindi (India) - Male", "voice_id": "hi-in-male", "flag": "🇮🇳", "gender": "Male"},
    {"code": "en", "tld": "edge", "name": "English (US) - Female (Neural)", "voice_id": "en-us-female-neural", "flag": "🇺🇸", "gender": "Female"},
    {"code": "es", "tld": "edge", "name": "Spanish (Spain) - Male", "voice_id": "es-es-male", "flag": "🇪🇸", "gender": "Male"},
    {"code": "es", "tld": "edge", "name": "Spanish (Mexico) - Male", "voice_id": "es-mx-male", "flag": "🇲🇽", "gender": "Male"},
    {"code": "fr", "tld": "edge", "name": "French (France) - Male", "voice_id": "fr-fr-male", "flag": "🇫🇷", "gender": "Male"},
    {"code": "fr", "tld": "edge", "name": "French (Canada) - Male", "voice_id": "fr-ca-male", "flag": "🇨🇦", "gender": "Male"},
    {"code": "de", "tld": "edge", "name": "German (Germany) - Male", "voice_id": "de-de-male", "flag": "🇩🇪", "gender": "Male"},
    {"code": "pt", "tld": "edge", "name": "Portuguese (Brazil) - Male", "voice_id": "pt-br-male", "flag": "🇧🇷", "gender": "Male"},
    {"code": "ru", "tld": "edge", "name": "Russian (Russia) - Male", "voice_id": "ru-ru-male", "flag": "🇷🇺", "gender": "Male"},
    {"code": "ar", "tld": "edge", "name": "Arabic (Standard) - Male", "voice_id": "ar-sa-male", "flag": "🇸🇦", "gender": "Male"},
    {"code": "ko", "tld": "edge", "name": "Korean (South Korea) - Male", "voice_id": "ko-kr-male", "flag": "🇰🇷", "gender": "Male"},
    {"code": "zh-CN", "tld": "edge", "name": "Chinese (Mandarin) - Male", "voice_id": "zh-cn-male", "flag": "🇨🇳", "gender": "Male"},
    {"code": "it", "tld": "edge", "name": "Italian (Italy) - Male", "voice_id": "it-it-male", "flag": "🇮🇹", "gender": "Male"}
]

EDGE_VOICE_MAPPING = {
    "en-us-male": "en-US-AndrewNeural",
    "en-uk-male": "en-GB-RyanNeural",
    "en-in-male": "en-IN-PrabhatNeural",
    "en-us-female-neural": "en-US-EmmaNeural",
    "hi-in-male": "hi-IN-MadhurNeural",
    "es-es-male": "es-ES-AlvaroNeural",
    "es-mx-male": "es-MX-JorgeNeural",
    "fr-fr-male": "fr-FR-HenriNeural",
    "fr-ca-male": "fr-CA-AntoineNeural",
    "de-de-male": "de-DE-ConradNeural",
    "pt-br-male": "pt-BR-AntonioNeural",
    "ru-ru-male": "ru-RU-DmitryNeural",
    "ar-sa-male": "ar-SA-HamedNeural",
    "ko-kr-male": "ko-KR-InJoonNeural",
    "zh-cn-male": "zh-CN-YunxiNeural",
    "it-it-male": "it-IT-DiegoNeural"
}

def get_voice_meta(voice_id):
    """Retrieve voice metadata by voice_id."""
    for item in SUPPORTED_LANGUAGES:
        if item["voice_id"].lower() == voice_id.lower():
            return item
    # Default fallback to English US
    return SUPPORTED_LANGUAGES[0]

def generate_speech(text, voice_id="en-us", speed=1.0, output_folder="static/audio"):
    """
    Synthesize text into speech MP3 using gTTS or Microsoft Edge TTS.
    Returns (audio_filename, character_count).
    """
    if not text or not text.strip():
        raise ValueError("Text content cannot be empty.")

    cleaned_text = text.strip()
    char_count = len(cleaned_text)

    meta = get_voice_meta(voice_id)
    lang = meta["code"]
    tld = meta["tld"]

    # gTTS slow mode check for lower speeds
    is_slow = speed < 0.8

    os.makedirs(output_folder, exist_ok=True)
    filename = f"tts_{uuid.uuid4().hex[:12]}.mp3"
    filepath = os.path.join(output_folder, filename)

    try:
        if tld == "eleven":
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("ELEVEN_LABS_API_KEY")
            if not api_key:
                raise ValueError("ElevenLabs API Key (ELEVEN_LABS_API_KEY) is missing in your .env file.")
            
            import requests
            # Use original case-sensitive voice_id from metadata
            actual_voice_id = meta["voice_id"]
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{actual_voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            data = {
                "text": cleaned_text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            response = requests.post(url, json=data, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(f"ElevenLabs API Error: {response.text}")
            
            with open(filepath, "wb") as f:
                f.write(response.content)
        elif tld == "edge":
            import asyncio
            import edge_tts
            import threading
            
            edge_voice_name = EDGE_VOICE_MAPPING.get(voice_id.lower(), "en-US-AndrewNeural")
            
            # Format speed rate parameter (e.g. "+10%", "-5%", "+0%")
            rate_percentage = int((speed - 1.0) * 100)
            rate_str = f"{rate_percentage:+d}%" if rate_percentage != 0 else "+0%"

            async def run_edge_tts():
                communicate = edge_tts.Communicate(cleaned_text, voice=edge_voice_name, rate=rate_str)
                await communicate.save(filepath)

            def run_async_safely(coro):
                result = []
                error = []

                def target():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        res = loop.run_until_complete(coro)
                        result.append(res)
                    except Exception as ex:
                        error.append(ex)
                    finally:
                        loop.close()

                thread = threading.Thread(target=target)
                thread.start()
                thread.join()

                if error:
                    raise error[0]
                return result[0] if result else None

            run_async_safely(run_edge_tts())
        else:
            tts = gTTS(text=cleaned_text, lang=lang, tld=tld, slow=is_slow)
            tts.save(filepath)
    except Exception as e:
        raise RuntimeError(f"{str(e)}")

    return filename, char_count

def summarize_text(text, target_sentences=2):
    """
    Lightweight extractive text summarizer algorithm.
    Extracts key sentences based on word frequency scoring.
    """
    text = text.strip()
    if not text:
        return ""
    
    sentences = re.split(r'(?<=[.!?]) +', text)
    if len(sentences) <= target_sentences:
        return text

    words = re.findall(r'\w+', text.lower())
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'it', 'this', 'that', 'are', 'was', 'were', 'be', 'been', 'as'}
    filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
    
    word_freq = Counter(filtered_words)
    
    sentence_scores = {}
    for idx, sentence in enumerate(sentences):
        score = 0
        s_words = re.findall(r'\w+', sentence.lower())
        for word in s_words:
            if word in word_freq:
                score += word_freq[word]
        sentence_scores[idx] = score / (len(s_words) + 1)
    
    top_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:target_sentences] # type: ignore
    top_indices.sort()
    
    return ' '.join([sentences[i] for i in top_indices])
