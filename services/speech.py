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
    {"code": "ko", "tld": "co.kr", "name": "Korean (South Korea)", "voice_id": "ko-kr", "flag": "🇰🇷", "gender": "🇰🇷"}
]

def get_voice_meta(voice_id):
    """Retrieve voice metadata by voice_id."""
    for item in SUPPORTED_LANGUAGES:
        if item["voice_id"] == voice_id.lower():
            return item
    # Default fallback to English US
    return SUPPORTED_LANGUAGES[0]

def generate_speech(text, voice_id="en-us", speed=1.0, output_folder="static/audio"):
    """
    Synthesize text into speech MP3 using gTTS.
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
        tts = gTTS(text=cleaned_text, lang=lang, tld=tld, slow=is_slow)
        tts.save(filepath)
    except Exception as e:
        raise RuntimeError(f"Failed to generate speech audio: {str(e)}")

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
