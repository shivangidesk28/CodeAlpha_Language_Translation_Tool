"""
app.py - the web server. It shows the translator page and handles translate requests.
Run it with:  python app.py

The browser never talks to the translation API directly. It sends the text to
/api/translate here, and this server calls the API. That keeps any API key
secret on the server instead of exposing it in the web page.
"""

from flask import Flask, jsonify, render_template, request

from translator import LANGUAGES, MAX_CHARS, TranslationError, provider_name, translate

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", languages=LANGUAGES, max_chars=MAX_CHARS,
                           provider=provider_name())


@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    source = str(data.get("source", "auto"))
    target = str(data.get("target", "en"))

    if not text:
        return jsonify({"error": "Please type some text to translate."}), 400
    if len(text) > MAX_CHARS:
        return jsonify({"error": f"Text is too long. The limit is {MAX_CHARS} characters."}), 400
    if target not in LANGUAGES or (source != "auto" and source not in LANGUAGES):
        return jsonify({"error": "Please choose a valid language."}), 400

    try:
        return jsonify(translate(text, source, target))
    except TranslationError as err:
        return jsonify({"error": str(err)}), 502


if __name__ == "__main__":
    app.run(debug=True, port=5000)
