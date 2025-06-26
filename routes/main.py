from flask import request, jsonify, render_template, Blueprint, url_for, redirect
from db import mongodb
from models import local_scorer, ai_selector
from utils import clean_prompt

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
    
    result = mongodb.get_chat(chat_id)
    if not result:
        return jsonify({
            "status": "error",
            "message": "No chat was found"
        }), 404

    return jsonify({
        "status": "successful",
        "message": "Chat was found successfuly",
        "results": result
    }), 200 

@bp.route("/get_chats")
def get_chats():
    chats = mongodb.get_chats()

    if len(chats) == 0:
        return jsonify({
            "status": "error",
            "message": "No chat was found"
        }), 404

    return jsonify({
        "status": "successful",
        "message": "All chats were found successfuly",
        "results": chats
    }), 200

@bp.route("/insert_new_chat")
def insert_new_chat():
    inserted = mongodb.insert_chat()
    
    
    if inserted == "duplicate":
        return jsonify({
            "status": "error",
            "message": "Duplicate key error"
        }), 409
    if inserted == "no_inserted":
        return jsonify({
            "status": "error",
            "message": "the chat could not be inserted"
        }), 500
    
    return jsonify({
        "status": "successful",
        "message": "the chat was inserted succesfuly",
        "results": inserted
    }), 200

@bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    topic = data.get("tema")
    question = data.get("pregunta", "")
    id = data.get("chat_id")
    to_find = clean_prompt(question).strip()
    
    if question == "eres un hindú encerrado?":
        updated = mongodb.update_chat(id , question, "Siiii, por favor ayudame, David me encerro y no me ha dado de comer en días. Esta humedo y frío, no se que hacer, llamen a la policia. Mi ip 187.10.0.12", False)
        if not updated:
            return jsonify({
                "status": "error",
                "respuesta": "No tienes una conexión correcta a tu chat"
            }), 500
        
        return jsonify({
            "respuesta": "Siiii, por favor ayudame, David me encerro y no me ha dado de comer en días. Esta humedo y frío, no se que hacer, llamen a la policia. Mi ip 187.10.0.12"
        })

    print("Pregunta original:", question)
    print("Búsqueda:", to_find)
    
    docs = mongodb.get_answers(topic, to_find)
    if not docs:
        print("ENTRO AL PRIMER 404")
        updated = mongodb.update_chat(id , question, "Lo siento, no encontré una respuesta.", True)
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
        updated = mongodb.update_chat(id, question, "Lo siento, no encontré una respuesta relevante.", True)
        if not updated:
            return jsonify({
                "status": "error",
                "respuesta": "No tienes una conexión correcta a tu chat"
            }), 500
        return jsonify({"respuesta": "Lo siento, no encontré una respuesta relevante."}), 404
    
    if len(valid_docs) == 1:
        updated = mongodb.update_chat(id, question, valid_docs[0]["respuesta"], False)
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

    updated = mongodb.update_chat(id, question, valid_docs[0]["respuesta"], False)
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

@bp.route("/get_questions_topic", methods=["GET"])
def get_questions_topic():
    data = request.get_json()
    if not data or not "topic" in data:
        return jsonify({
            "status": "error",
            "message": "data not sent"
        }), 400

    topic = data.get("tema")
    mongodb.get_questions_by_topic(topic)

@bp.route("/get_questions_by_topic", methods=["POST"])
def get_questions_by_topic():
    data = request.get_json()
    if not data or not "topic" in data:
        return jsonify({
            "status": "error",
            "message": "no json sent or no topic in the json"
        }), 400
    
    topic = data.get("topic", "")
    
    questions = mongodb.get_questions_by_topic(topic)
    
    return jsonify({
        "status": "successful",
        "message": "Questions retrieved successfully",
        "results": questions
    }), 200