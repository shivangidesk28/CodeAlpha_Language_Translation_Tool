"""
translator.py - sends text to a translation API and returns the translated text.

Which API is used (checked in this order):
  1. Microsoft Translator        - if AZURE_TRANSLATOR_KEY is set in .env
  2. Google Cloud Translation    - if GOOGLE_TRANSLATE_API_KEY is set in .env
  3. Google Translate (free)     - the default, works without any key

So the app works straight away, and you can switch to an official API
just by adding a key to the .env file (see .env.example).
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()  # reads the .env file in this folder, if it exists

MAX_CHARS = 5000  # longest text we accept in one request
TIMEOUT = 15      # seconds to wait for the API before giving up

# Languages shown in the dropdowns: code -> name (Google Translate codes)
LANGUAGES = {
    "ar": "Arabic",
    "as": "Assamese",
    "bn": "Bengali",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "tl": "Filipino",
    "fi": "Finnish",
    "fr": "French",
    "de": "German",
    "el": "Greek",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "ko": "Korean",
    "ms": "Malay",
    "ml": "Malayalam",
    "mr": "Marathi",
    "ne": "Nepali",
    "or": "Odia",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "pa": "Punjabi",
    "ro": "Romanian",
    "ru": "Russian",
    "es": "Spanish",
    "sw": "Swahili",
    "sv": "Swedish",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
}

# Microsoft uses different codes for a few languages
_TO_MICROSOFT = {"zh-CN": "zh-Hans", "zh-TW": "zh-Hant", "tl": "fil"}

# Codes the APIs may send back -> the codes we use in LANGUAGES
_FROM_API = {"zh-Hans": "zh-CN", "zh-Hant": "zh-TW", "zh": "zh-CN", "fil": "tl", "iw": "he"}


class TranslationError(Exception):
    """Raised when the translation API can't be reached or sends back an error."""


# ---------- The three APIs ----------

def _microsoft(text, source, target):
    # Docs: https://learn.microsoft.com/azure/ai-services/translator/reference/v3-0-translate
    params = {"api-version": "3.0", "to": _TO_MICROSOFT.get(target, target)}
    if source != "auto":
        params["from"] = _TO_MICROSOFT.get(source, source)

    headers = {"Ocp-Apim-Subscription-Key": os.getenv("AZURE_TRANSLATOR_KEY")}
    region = os.getenv("AZURE_TRANSLATOR_REGION")
    if region:  # needed for regional (non-global) Azure resources
        headers["Ocp-Apim-Subscription-Region"] = region

    response = requests.post(
        "https://api.cognitive.microsofttranslator.com/translate",
        params=params, headers=headers, json=[{"Text": text}], timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()[0]
    detected = (result.get("detectedLanguage") or {}).get("language", source)
    return result["translations"][0]["text"], detected


def _google_cloud(text, source, target):
    # Docs: https://cloud.google.com/translate/docs/reference/rest/v2/translate
    body = {"q": text, "target": target, "format": "text"}
    if source != "auto":
        body["source"] = source

    response = requests.post(
        "https://translation.googleapis.com/language/translate/v2",
        params={"key": os.getenv("GOOGLE_TRANSLATE_API_KEY")}, json=body, timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()["data"]["translations"][0]
    return result["translatedText"], result.get("detectedSourceLanguage", source)


def _google_free(text, source, target):
    # The same free endpoint Google's own translate widgets use. No key needed.
    response = requests.post(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": source, "tl": target, "dt": "t"},
        data={"q": text}, timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    # data[0] is a list of [translated_sentence, original_sentence, ...]; data[2] is the source language
    translated = "".join(part[0] for part in data[0] if part[0])
    return translated, data[2]


def _pick_api():
    if os.getenv("AZURE_TRANSLATOR_KEY"):
        return "Microsoft Translator", _microsoft
    if os.getenv("GOOGLE_TRANSLATE_API_KEY"):
        return "Google Cloud Translation", _google_cloud
    return "Google Translate", _google_free


def provider_name():
    """Name of the API in use, shown at the bottom of the page."""
    return _pick_api()[0]


def translate(text, source="auto", target="en"):
    """
    Translate text from `source` to `target` (codes from LANGUAGES; source may be "auto").
    Returns {"text": translated text, "detected": source language code, "provider": API name}.
    Raises TranslationError if the API fails.
    """
    name, call_api = _pick_api()
    try:
        translated, detected = call_api(text, source, target)
    except requests.HTTPError as err:
        status = err.response.status_code
        print(f"[translator] {name} returned HTTP {status}: {err.response.text[:300]}")
        if status in (401, 403):
            raise TranslationError(f"{name} rejected the API key. Check the key in your .env file.") from err
        if status == 429:
            raise TranslationError("Too many requests. Please wait a minute and try again.") from err
        raise TranslationError(f"{name} returned an error (HTTP {status}). Please try again.") from err
    except requests.RequestException as err:  # no internet, timeout, bad JSON, ...
        print(f"[translator] {name} request failed: {type(err).__name__}: {err}")
        raise TranslationError("Could not reach the translation service. Check your internet connection.") from err
    except (KeyError, IndexError, TypeError) as err:  # the API answered in an unexpected format
        print(f"[translator] Unexpected answer from {name}: {type(err).__name__}: {err}")
        raise TranslationError("The translation service sent an unexpected answer. Please try again.") from err

    detected = _FROM_API.get(detected, detected)
    return {"text": translated, "detected": detected, "provider": name}
