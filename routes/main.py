from flask import Flask, request, jsonify, render_template, Blueprint
from db import mongodb
from models import QADocument, QAItem
from utils import clean_prompt
import re

bp = Blueprint("main_routes", "__name__")

@bp.before_first_request
def setup_indexes():
    temas = ["mate", "historia"]
    for t in temas:
        mongodb.ensure_text_index(t)

@bp.route("/")
def index():
    temas = ["mate", "historia"]
    return render_template("chat.html", temas=temas)

@bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    topic = data.get("tema")
    question = data.get("pregunta", "")
    to_find = clean_prompt(question)

    colec = mongodb.get_collection(topic)
    doc = colec.find_one(
        {"$text": {"$search": to_find}},
        {"score": {"$meta": "textScore"}, "respuesta": 1},
        sort=[("score", {"$meta": "textScore"})]
    )

    if not doc:
        return jsonify({"respuesta": "Lo siento, no encontré una respuesta."})
    return jsonify({"respuesta": doc["respuesta"]})