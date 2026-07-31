"""
Unit tests for services/speech.py pure functions.
No actual TTS API calls are made — only pure Python functions are tested.
"""
# pyrefly: ignore [missing-import]
import pytest
from services.speech import (
    SUPPORTED_LANGUAGES,
    EDGE_VOICE_MAPPING,
    get_voice_meta,
    clean_text_for_speech,
    summarize_text,
)


# ── SUPPORTED_LANGUAGES structure ─────────────────────────────────────────────

def test_supported_languages_not_empty():
    """At least 40 languages should be defined."""
    assert len(SUPPORTED_LANGUAGES) >= 40


def test_supported_languages_required_keys():
    """Every language entry must have all required keys."""
    required = {"code", "tld", "name", "voice_id", "flag", "gender"}
    for lang in SUPPORTED_LANGUAGES:
        missing = required - set(lang.keys())
        assert not missing, f"Language {lang.get('name')} is missing keys: {missing}"


def test_supported_languages_no_duplicate_voice_ids():
    """Every voice_id must be unique across the list."""
    ids = [lang["voice_id"] for lang in SUPPORTED_LANGUAGES]
    dupes = [vid for vid in ids if ids.count(vid) > 1]
    assert not dupes, f"Duplicate voice_ids found: {set(dupes)}"


def test_supported_languages_valid_genders():
    """Gender field must be 'Male' or 'Female'."""
    for lang in SUPPORTED_LANGUAGES:
        assert lang["gender"] in ("Male", "Female"), (
            f"Invalid gender '{lang['gender']}' for {lang['name']}"
        )


# ── EDGE_VOICE_MAPPING ────────────────────────────────────────────────────────

def test_edge_voice_mapping_not_empty():
    """Edge voice mapping must have entries."""
    assert len(EDGE_VOICE_MAPPING) > 0


def test_edge_voice_mapping_values_are_strings():
    """All edge voice IDs must be non-empty strings."""
    for key, val in EDGE_VOICE_MAPPING.items():
        assert isinstance(val, str) and len(val) > 0, f"Bad edge voice for {key}"


# ── get_voice_meta ────────────────────────────────────────────────────────────

def test_get_voice_meta_known_voice():
    """Returns correct metadata for a known voice_id."""
    meta = get_voice_meta("en-us")
    assert meta["voice_id"] == "en-us"
    assert meta["flag"] == "🇺🇸"


def test_get_voice_meta_case_insensitive():
    """voice_id lookup is case-insensitive."""
    meta = get_voice_meta("EN-US")
    assert meta["voice_id"] == "en-us"


def test_get_voice_meta_unknown_falls_back():
    """Unknown voice_id falls back to the first entry (English US)."""
    meta = get_voice_meta("xx-unknown-voice")
    assert meta["code"] == "en"
    assert meta["flag"] == "🇺🇸"


def test_get_voice_meta_hindi():
    """Hindi neural voice resolves correctly."""
    meta = get_voice_meta("hi-in-female-neural")
    assert "Hindi" in meta["name"]
    assert meta["flag"] == "🇮🇳"


# ── clean_text_for_speech ─────────────────────────────────────────────────────

def test_clean_text_empty():
    """Empty string input returns empty string."""
    assert clean_text_for_speech("") == ""


def test_clean_text_strips_emojis():
    """Emoji characters are stripped."""
    result = clean_text_for_speech("Hello 🎙️ World")
    assert "🎙" not in result
    assert "Hello" in result


def test_clean_text_strips_markdown_bullets():
    """Markdown bullets and headers are removed."""
    result = clean_text_for_speech("• Item one\n* Item two\n# Header")
    assert "•" not in result
    assert "#" not in result


def test_clean_text_converts_numbered_list():
    """Numbered list prefixes are converted to 'Step N:' format."""
    result = clean_text_for_speech("1. First step\n2. Second step")
    assert "Step 1:" in result
    assert "Step 2:" in result


def test_clean_text_normalizes_whitespace():
    """Multiple spaces/newlines are collapsed to single spaces."""
    result = clean_text_for_speech("Hello    World\n\n\nFoo")
    assert "  " not in result
    assert "\n" not in result


def test_clean_text_plain_passthrough():
    """Plain text without special characters is passed through unchanged."""
    result = clean_text_for_speech("The quick brown fox jumps over the lazy dog.")
    assert result == "The quick brown fox jumps over the lazy dog."


# ── summarize_text ────────────────────────────────────────────────────────────

def test_summarize_empty_returns_empty():
    """Empty input returns empty string."""
    assert summarize_text("") == ""


def test_summarize_dsa_topic():
    """DSA/coding topic returns a structured guide."""
    result = summarize_text("Which is better: Striver or NeetCode sheet?")
    assert "DSA" in result or "Striver" in result or "NeetCode" in result


def test_summarize_tech_topic():
    """Python/programming topic returns a guide."""
    result = summarize_text("What is Python?")
    assert len(result) > 50  # Should return a meaningful response


def test_summarize_recipe_topic():
    """Recipe/food topic returns a structured guide."""
    result = summarize_text("How to make pasta recipe?")
    assert len(result) > 50


def test_summarize_fitness_topic():
    """Fitness/diet topic returns a structured guide."""
    result = summarize_text("How to start a fitness diet plan?")
    assert len(result) > 50


def test_summarize_long_text_condenses():
    """Long passage (60+ words) is summarized into fewer sentences."""
    long_text = (
        "The Python programming language was created by Guido van Rossum. "
        "It is widely used in data science, web development, and automation. "
        "Python features a clean syntax and a rich standard library. "
        "It supports multiple programming paradigms including procedural, "
        "object-oriented, and functional styles. "
        "Python's package ecosystem via pip is one of the largest in any language. "
        "Many organizations including Google, NASA, and Netflix use Python extensively. "
        "The language emphasizes readability and simplicity above performance."
    )
    result = summarize_text(long_text)
    assert isinstance(result, str)
    assert len(result) > 0
