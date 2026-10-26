# CodeAlpha_Language_Translation_Tool

A web-based language translator built for the CodeAlpha Artificial Intelligence internship (Task 1).

## What it does
- **User interface**: type or paste text, choose the source language (or let it auto-detect) and the target language
- **Translation API**: the text is sent to a translation API and the translated text comes back
  - Works out of the box with **Google Translate** (free endpoint, no key needed)
  - Switches to the official **Microsoft Translator** or **Google Cloud Translation** API if you add a key (see below)
- **Shows the result** clearly next to the original text, including right-to-left languages like Arabic and Urdu
- **Extras**
  - **Copy** button for the translation
  - **Text-to-speech**: listen to the original or the translated text (uses the browser's built-in voices)
  - **Swap** button that switches the languages and the texts
  - Auto-detects the source language and shows which one it found
  - Re-translates straight away when you change a language
  - `Ctrl + Enter` shortcut, character counter, dark mode, works on phones
  - Remembers your last chosen languages and theme

44 languages are included, among them Hindi, Gujarati, Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi, Urdu, English, Spanish, French, German, Japanese, Chinese and Arabic.

## How to run
1. Install Python 3.9 or newer
2. Open a terminal in this folder
3. (Optional) create a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - Mac/Linux: `python3 -m venv venv` then `source venv/bin/activate`
4. Install the libraries: `pip install -r requirements.txt`
5. Start the app: `python app.py`
6. Open http://127.0.0.1:5000 in your browser

An internet connection is needed, because the translation is done by an online API.

## How it works
```
Browser (index.html)  --text + languages-->  Flask server (app.py)  -->  translator.py  -->  Translation API
                      <---translated text--                          <--                 <--
```
1. The page sends the text and the chosen languages to `/api/translate` as JSON.
2. `app.py` checks the input (not empty, not too long, valid languages).
3. `translator.py` calls the translation API and returns the translated text and the detected language.
4. The page displays the result, and the copy/listen buttons work on it.

The browser never calls the translation API directly. If you use an API key, it stays on the server and is never visible in the web page.

## Project structure
```
codealpha_translation/
├── app.py            # Flask web server (page + /api/translate)
├── translator.py     # calls the translation API (Microsoft / Google Cloud / Google free)
├── .env.example      # template for an optional API key
├── requirements.txt  # libraries needed
└── templates/
    └── index.html    # the translator user interface (HTML, CSS, JavaScript)
```

## Optional: use an official API key
By default the app uses Google Translate's free endpoint, which needs no sign-up. To use an official API instead:

1. Copy `.env.example` to a new file named `.env`
2. Fill in **one** of these:
   - **Microsoft Translator** (free tier: 2 million characters a month): create a *Translator* resource in the
     [Azure portal](https://portal.azure.com), then copy its key and region:
     ```
     AZURE_TRANSLATOR_KEY=your_key
     AZURE_TRANSLATOR_REGION=centralindia
     ```
   - **Google Cloud Translation** (needs a Google Cloud project with billing turned on):
     ```
     GOOGLE_TRANSLATE_API_KEY=your_key
     ```
3. Restart the app with `python app.py`. The footer of the page shows which API is in use.

Never upload your `.env` file to GitHub (`.gitignore` already excludes it).

## Text-to-speech note
Listening uses the voices installed on your computer or phone, so the available languages depend on the device.
Microsoft Edge has natural-sounding voices for most languages, including Indian languages. If a language has
no voice, the app tells you instead of reading it with the wrong voice.
