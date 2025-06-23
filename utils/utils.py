import re
STOPWORDS = {
    "y", "o", "es", "en", "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "para", "que", "cómo", "como", "qué", "cuando", "cuál", "cuáles",
    "con", "sin", "por", "sobre", "al", "se", "su", "sus", "le", "les", "lo", "mi",
}

def clean_prompt(text: str) -> str:
    text = text.lower()

    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),
                 ("à","a"),("è","e"),("ì","i"),("ò","o"),("ù","u"),
                 ("ä","a"),("ë","e"),("ï","i"),("ö","o"),("ü","u")]:
        text = text.replace(a, b)

    text = re.sub(r"[^\w\s]", " ", text)
    tokens = [pal for pal in text.split() if pal not in STOPWORDS]
    return " ".join(tokens)