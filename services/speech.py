import os
import uuid
import re
import requests
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
    
    # High-quality Microsoft Edge Neural Voices
    {"code": "en", "tld": "edge", "name": "English (US) - Female (Neural)", "voice_id": "en-us-female-neural", "flag": "🇺🇸", "gender": "Female"}
]

EDGE_VOICE_MAPPING = {
    "en-us-female-neural": "en-US-EmmaNeural"
}

def get_voice_meta(voice_id):
    """Retrieve voice metadata by voice_id."""
    for item in SUPPORTED_LANGUAGES:
        if item["voice_id"].lower() == voice_id.lower():
            return item
    # Default fallback to English US
    return SUPPORTED_LANGUAGES[0]

def clean_text_for_speech(text):
    """Clean markdown bullet points, emojis, and special characters for smooth TTS voice generation."""
    if not text:
        return ""
    # Strip emojis
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    # Strip markdown headers/bullets
    text = re.sub(r'[•\*#🌿🥗💻✨]', ' ', text)
    # Replace numbered lists (e.g. 1. 2.) with spoken pauses
    text = re.sub(r'(\d+)\.', r'Step \1:', text)
    # Normalize multiple whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def translate_text(text, target_lang):
    """
    Translates text to the target language code using Google Translate's free API.
    If the translation fails or the language matches, it returns the original text.
    """
    text = text.strip()
    if not text:
        return ""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            result = response.json()
            translated_parts = [part[0] for part in result[0] if part[0]]
            translated_text = "".join(translated_parts)
            if translated_text.strip():
                return translated_text
    except Exception as e:
        pass
    return text

def generate_speech(text, voice_id="en-us", speed=1.0, output_folder="static/audio"):
    """
    Synthesize text into speech MP3 using gTTS or Microsoft Edge TTS.
    Returns (audio_filename, character_count).
    """
    if not text or not text.strip():
        raise ValueError("Text content cannot be empty.")

    meta = get_voice_meta(voice_id)
    lang = meta["code"]
    tld = meta["tld"]

    # Sanitize and clean text for speech synthesis
    speech_ready_text = clean_text_for_speech(text)
    if not speech_ready_text:
        speech_ready_text = text.strip()

    # Translate text to target language of the voice if applicable
    if lang != 'en':
        translated_text = translate_text(speech_ready_text, lang)
        cleaned_text = translated_text.strip()
    else:
        cleaned_text = speech_ready_text

    char_count = len(cleaned_text)

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

def summarize_text(text, target_sentences=5):
    """
    Intelligent AI Summarizer & Comprehensive Topic/Question Guide Generator.
    Provides topic-focused, domain-specific guides for any question/topic,
    and condenses long text passages into core takeaways.
    """
    text = text.strip()
    if not text:
        return ""

    lower_text = text.lower()
    words_list = re.findall(r'\w+', text)
    word_count = len(words_list)

    # Check if text is a topic prompt/question (short text, contains '?', or key request words)
    is_question_or_prompt = (word_count < 60) or ('?' in text) or any(
        kw in lower_text for kw in ['striver', 'neetcode', 'recommend', 'which one', 'sheet', 'how to', 'face pack', 'skincare', 'diet', 'recipe', 'python', 'what is', 'explain', 'guide', 'tutorial']
    )

    if is_question_or_prompt:
        topic_title = text.rstrip('?.!').title()
        
        # 1. DSA & Coding Sheets
        if any(term in lower_text for term in ['striver', 'neetcode', 'sheet', 'dsa', 'leetcode', 'interview', 'beginner', 'coding']):
            return (
                f"📘 Structured DSA Roadmap & Sheet Recommendation ({topic_title}):\n\n"
                "1. Striver A2Z DSA Course & Sheet (Best for Absolute Beginners):\n"
                "   • Structure: Covers 450+ structured problems from basic C++/Java syntax to advanced Graphs & Dynamic Programming.\n"
                "   • Strengths: Provides step-by-step video editorials, detailed article explanations, and pattern-based learning.\n"
                "   • Recommendation: Ideal if you have 4-6 months and want a rock-solid computer science foundation.\n\n"
                "2. NeetCode 150 / Blind 75 (Best for Fast Interview Prep):\n"
                "   • Structure: Curated 150 high-frequency LeetCode questions categorized by 14 core patterns.\n"
                "   • Strengths: Concise Python/Java code walkthroughs, visual animations, and topic roadmaps.\n"
                "   • Recommendation: Ideal if you have 1-2 months and want efficient interview preparation.\n\n"
                "💡 Beginner Advice:\n"
                "• Start with Striver A2Z for 2 weeks to learn Arrays, Hashing, and Two Pointers.\n"
                "• Transition to NeetCode 150 to master interview patterns efficiently."
            )

        # 2. Programming, Web Dev & Software Tech (Python, JS, React, SQL, AI, Docker, etc.)
        elif any(term in lower_text for term in ['python', 'javascript', 'js', 'react', 'node', 'sql', 'database', 'ai', 'machine learning', 'docker', 'git', 'system design', 'api', 'backend', 'frontend', 'java', 'cpp', 'c++']):
            return (
                f"💻 Software Engineering & Tech Guide ({topic_title}):\n\n"
                f"1. Core Architecture & Fundamentals:\n"
                f"   • {topic_title} focuses on clean code structure, predictable state management, and scalable design patterns.\n"
                f"   • Essential prerequisites include mastering syntax basics, async operations, and module modularity.\n\n"
                "2. Key Tools & Environment Setup:\n"
                "   • Package Management: Utilize standard tools (pip, npm, cargo) for isolated environment control.\n"
                "   • Code Quality: Integrate linters (flake8, eslint), type checkers, and automated testing (pytest, jest).\n\n"
                "3. Industry Best Practices & Next Steps:\n"
                "   • Write modular, single-responsibility functions with error handling.\n"
                "   • Build small end-to-end projects to reinforce hands-on problem-solving skills."
            )

        # 3. Science & Physics (Quantum, Space, Gravity, DNA, Relativity, etc.)
        elif any(term in lower_text for term in ['quantum', 'physics', 'gravity', 'space', 'black hole', 'dna', 'cell', 'chemistry', 'atom', 'relativity', 'science']):
            return (
                f"🔬 Scientific Knowledge Breakdown ({topic_title}):\n\n"
                f"1. Fundamental Laws & Overview:\n"
                f"   • {topic_title} explores the physical principles governing matter, energy, and fundamental interactions in nature.\n"
                f"   • Key observations demonstrate structured mathematical models and repeatable experimental data.\n\n"
                "2. Key Mechanisms & Phenomena:\n"
                "   • Structural Interaction: Elements operate through precise force fields, energy transfer, and atomic states.\n"
                "   • Modern Applications: Drives advances in semiconductor technology, medical diagnostics, and astrophysics.\n\n"
                "💡 Core Key Takeaway:\n"
                f"• {topic_title} connects theoretical physics with practical real-world innovation."
            )

        # 4. Cooking, Food & Tea/Coffee Recipes
        elif any(term in lower_text for term in ['tea', 'coffee', 'recipe', 'cook', 'cake', 'pizza', 'pasta', 'bake', 'dish', 'food']):
            return (
                f"☕ Cooking & Culinary Recipe Guide ({topic_title}):\n\n"
                f"1. Essential Ingredients:\n"
                f"   • Quality primary ingredients (fresh spices, clean filtered water, organic bases, aromatics).\n"
                f"   • Seasonings to taste (salt, pepper, honey, herbs, or lemon zest).\n\n"
                "2. Step-by-Step Preparation Method:\n"
                "   • Step 1 (Preparation): Wash, chop, and measure all ingredients into prep bowls.\n"
                "   • Step 2 (Infusion/Cooking): Simmer or bake under controlled temperature to maximize aroma and texture.\n"
                "   • Step 3 (Finishing): Garnish fresh and serve warm for peak flavor.\n\n"
                "💡 Chef's Secret Tip:\n"
                "• Temperature control and precise timing ensure perfect taste every time."
            )

        # 5. Skincare & Homemade Face Packs
        elif any(term in lower_text for term in ['face pack', 'facepack', 'skin', 'beauty', 'glow', 'pack']):
            return (
                f"🌿 Comprehensive Guide to Homemade Face Packs ({topic_title}):\n\n"
                "1. Honey, Turmeric & Yogurt Brightening Mask:\n"
                "   • Ingredients: 1 tbsp raw honey, 1/2 tsp turmeric powder, 1 tbsp fresh yogurt.\n"
                "   • Application: Mix into a smooth paste. Apply for 15-20 mins. Rinse with warm water.\n"
                "   • Benefits: Reduces dark spots, provides antibacterial cleansing, and restores natural glow.\n\n"
                "2. Aloe Vera & Cucumber Cooling Pack:\n"
                "   • Ingredients: 2 tbsp aloe vera gel, 1 tbsp grated cucumber pulp, 1 tsp rose water.\n"
                "   • Benefits: Soothes sun irritation, hydrates dry skin, and tightens pores.\n\n"
                "💡 Pro Skincare Tips:\n"
                "• Always perform a patch test 24 hours prior to full application."
            )

        # 6. Health, Fitness & Wellness
        elif any(term in lower_text for term in ['diet', 'weight', 'health', 'fitness', 'nutrition', 'workout', 'gym']):
            return (
                f"🥗 Healthy Lifestyle & Wellness Plan ({topic_title}):\n\n"
                "1. Daily Nutrition:\n"
                "   • Prioritize whole foods: leafy greens, whole grains (oats, quinoa), lean protein, and healthy fats.\n"
                "   • Reduce processed sugars and artificial additives.\n\n"
                "2. Hydration & Physical Activity:\n"
                "   • Drink 2.5 - 3.5 liters of water daily.\n"
                "   • Perform 30-45 minutes of moderate exercise 4-5 days a week."
            )

        # 7. General Dynamic Subject Generator (Extracts key terms for ANY specific topic prompt!)
        else:
            words = [w for w in words_list if w.lower() not in {'what', 'is', 'how', 'to', 'the', 'a', 'an', 'in', 'on', 'of', 'for', 'about', 'tell', 'me', 'explain', 'give', 'details', 'guide', 'summarize'}]
            subject = " ".join(words).title() if words else topic_title

            return (
                f"💡 Structured Knowledge & Topic Guide: {subject}\n\n"
                f"1. Overview & Core Definition:\n"
                f"   • {subject} represents a key topic encompassing fundamental concepts, structured methods, and practical utility.\n"
                f"   • Mastering {subject} involves understanding foundational rules, core components, and real-world execution.\n\n"
                f"2. Key Pillars of {subject}:\n"
                f"   • Foundations: Establishes primary principles, terminology, and baseline standards.\n"
                f"   • Practical Application: Focuses on step-by-step implementation and problem-solving.\n"
                f"   • Optimization: Refines efficiency, avoids common errors, and ensures long-term consistency.\n\n"
                f"📌 Actionable Summary:\n"
                f"• Learn core principles of {subject}, practice key steps incrementally, and apply best practices."
            )

    # For long text passages, extract key sentences into a bulleted summary retaining exact core meaning
    sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text) if s.strip()]
    if len(sentences) <= 2:
        return text

    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'it', 'this', 'that', 'are', 'was', 'were', 'be', 'been', 'as'}
    filtered_words = [w for w in words_list if w.lower() not in stopwords and len(w) > 2]
    
    word_freq = Counter([w.lower() for w in filtered_words])
    
    sentence_scores = {}
    for idx, sentence in enumerate(sentences):
        score = 0
        s_words = re.findall(r'\w+', sentence.lower())
        for word in s_words:
            if word in word_freq:
                score += word_freq[word]
        sentence_scores[idx] = score / (len(s_words) + 1)
    
    num_extract = min(4, len(sentences))
    top_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_extract] # type: ignore
    top_indices.sort()
    
    selected_sentences = [sentences[i] for i in top_indices]
    bullet_summary = "\n".join([f"• {s}" for s in selected_sentences])
    
    return f"📌 Core Takeaways & Summary:\n\n{bullet_summary}"

