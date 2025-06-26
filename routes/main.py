from flask import request, jsonify, render_template, Blueprint, url_for, redirect
from db import mongodb
from models import local_scorer, ai_selector
from utils import clean_prompt
import requests
import json
from difflib import SequenceMatcher
import re
from collections import Counter
import math
from config import settings
from bson import ObjectId
from pymongo import DESCENDING, errors
from datetime import datetime
import pytz


bp = Blueprint("main_routes", "__name__")

@bp.route("/")
def index():
    return render_template("main.html")

@bp.route("/chat")
def chat():
    chat_id = request.args.get("chat_id")
    if not chat_id:
        return render_template("not_found.html")
    
    return render_template("index.html", chat_id=chat_id)

@bp.route("/get_chat", methods=["POST"])
def get_chat():
    data = request.get_json()
    if not data or not "chat_id" in data:
        return jsonify({
            "status": "error",
            "message": "not json sent or not chat_id in the json"
        }), 400
    
    chat_id = data.get("chat_id", "")
    
    colec = mongodb.get_collection("historial")
    query = {"_id": ObjectId(chat_id)}
    result = colec.find_one(query)
    if not result:
        return jsonify({
            "status": "error",
            "message": "No chat was found"
        }), 404

    result["_id"] = str(result.get("_id", ""))

    return jsonify({
        "status": "successful",
        "message": "Chat was found successfuly",
        "results": result
    }), 200 

@bp.route("/get_chats")
def get_chats():
    colec = mongodb.get_collection("historial")
    cursor = colec.find().sort("fecha_creada", DESCENDING).limit(10)
    chats = list(cursor)

    if len(chats) == 0:
        return jsonify({
            "status": "error",
            "message": "No chat was found"
        }), 404

    for chat in chats:
        chat["_id"] = str(chat.get("_id", ""))
        chat["fecha_creada"] = chat["fecha_creada"].isoformat()

    return jsonify({
        "status": "successful",
        "message": "All chats were found successfuly",
        "results": chats
    }), 200

@bp.route("/insert_new_chat")
def insert_new_chat():
    local_zone = pytz.timezone('America/Chihuahua')
    local_date = datetime.now(local_zone)

    colec = mongodb.get_collection("historial")
    query = {
        "fecha_creada": local_date,
        "chat": []
        }
    
    try:
        result = colec.insert_one(query)
        chat_id = str(result.inserted_id)
        return jsonify({
            "status": "successful",
            "message": "the chat was inserted succesfuly",
            "results": chat_id
        }), 200
    except errors.DuplicateKeyError:
        return jsonify({
            "status": "error",
            "message": "Duplicate key error"
        }), 409
    except errors.PyMongoError as e:
        print(f"Error inserting a new chat: {e}")
        return jsonify({
            "status": "error",
            "message": "the chat could not be inserted"
        }), 500

@bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    topic = data.get("tema")
    question = data.get("pregunta", "")
    id = data.get("chat_id")
    to_find = clean_prompt(question).strip()
    
    print("Pregunta original:", question)
    print("Búsqueda:", to_find)
    
    colec = mongodb.get_collection(topic)
    
    docs = list(colec.find(
        {"$text": {"$search": to_find}},
        {
            "score": {"$meta": "textScore"},
            "respuesta": 1,
            "pregunta": 1
        }
    ).sort([("score", {"$meta": "textScore"})]).limit(5))
    
    if not docs:
        print("ENTRO AL PRIMER 404")
        updated = update_chat(id , question, "Lo siento, no encontré una respuesta.", True)
        if not updated:
            return jsonify({
                "status": "error",
                "respuesta": "No tienes una conexión correcta a tu chat"
            }), 500
        
        return jsonify({"respuesta": "Lo siento, no encontré una respuesta."}), 404
    
    print("Estos son los docs: ", docs)
    # Filtrar por score mínimo
    min_score = 3.0
    valid_docs = [doc for doc in docs if doc.get("score", 0) >= min_score]
    
    if not valid_docs:
        updated = update_chat(id, question, "Lo siento, no encontré una respuesta relevante.", True)
        if not updated:
            return jsonify({
                "status": "error",
                "respuesta": "No tienes una conexión correcta a tu chat"
            }), 500
        return jsonify({"respuesta": "Lo siento, no encontré una respuesta relevante."}), 404
    
    if len(valid_docs) == 1:
        updated = update_chat(id, question, valid_docs[0]["respuesta"], False)
        if not updated:
            return jsonify({
                "status": "error",
                "respuesta": "No tienes una conexión correcta a tu chat"
            }), 500
        
        return jsonify({
            "respuesta": valid_docs[0]["respuesta"],
            "metodo": "unica_respuesta",
            "score": valid_docs[0]["score"]
        }), 200
    
    best_index = None
    selection_method = "local_scoring"
    
    best_index = ai_selector.select_best_answer_ollama(question, valid_docs)
    if best_index is not None:
        selection_method = "ollama_ai"
    else:
        best_index = ai_selector.select_best_answer_hf(question, valid_docs)
        if best_index is not None:
            selection_method = "huggingface_ai"
    
    if best_index is None:
        similarities = []
        for doc in valid_docs:
            full_text = f"{doc.get('pregunta', '')} {doc.get('respuesta', '')} {' '.join(doc.get('tags', []))}"
            similarity = local_scorer.calculate_similarity(question, full_text)
            similarities.append(similarity)
        
        best_index = similarities.index(max(similarities))
        selection_method = "local_scoring"
    
    if best_index < 0 or best_index >= len(valid_docs):
        best_index = 0
    
    selected_doc = valid_docs[best_index]

    print("Se termino usando: ", selection_method)

    updated = update_chat(id, question, valid_docs[0]["respuesta"], False)
    if not updated:
        return jsonify({
            "status": "error",
            "respuesta": "No tienes una conexión correcta a tu chat"
        }), 500
    
    return jsonify({
        "respuesta": selected_doc["respuesta"],
        "metodo": selection_method,
        "score": selected_doc.get("score"),
        "total_encontradas": len(docs),
        "validas": len(valid_docs),
        "subtema": selected_doc.get("subtema")
    }), 200


def update_chat(id, question, answer, error: bool):
    collection = mongodb.get_collection("historial")
    chat_id = ObjectId(id)
    query = {
        "_id": chat_id
    }
    chat = collection.find_one(query)
    messages = chat["chat"]

    message = {
        "usuario": question,
        "bot": answer,
        "error": error
    }

    messages.append(message)

    if len(messages) > 25:
        messages = messages[-25]

    try:
        collection.update_one(
            {"_id": chat_id},
            {"$set": {"chat": messages}}
        )
        print("EVERYTHING WENT WELL WITH THE UPDATE")
        updated = True
    except:
        print("BRO, YOU DON'T EVEN KNOW HOW TO MAKE AN UPDATE")
        updated = False
    return updated