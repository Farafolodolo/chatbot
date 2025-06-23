from flask import request, jsonify, render_template, Blueprint
from db import mongodb
from models import QADocument, QAItem
from utils import clean_prompt

bp = Blueprint("main_routes", "__name__")

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/ask", methods=["POST"])
def ask():
    data     = request.get_json()
    topic    = data.get("tema")
    question = data.get("pregunta", "")
    to_find  = clean_prompt(question).strip()
    print("Esto se va a buscar: ", to_find)
    colec = mongodb.get_collection(topic)
    doc = colec.find_one(
        { "$text": { "$search": to_find } },
        {
          "score": {"$meta": "textScore"},
          "respuesta": 1
        },
        sort=[("score", {"$meta": "textScore"})]
    )

    if not doc:
        return jsonify({"respuesta": "Lo siento, no encontré una respuesta."}), 404

    score = float(doc["score"])

    print(score)

    validation_score = 6.0 
    if score < validation_score:
        return jsonify({"respuesta": "Lo siento, no encontré una respuesta."}), 404

    return jsonify({"respuesta": doc["respuesta"]}), 200