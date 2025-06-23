from flask import request, jsonify, render_template, Blueprint
from db import mongodb
from models import QADocument, QAItem
from utils import clean_prompt
import requests
import json
from difflib import SequenceMatcher
import re
from collections import Counter
import math
from config import settings

bp = Blueprint("main_routes", "__name__")

class AISelector:
    def __init__(self):
        # Ollama local (gratuito, sin límites)
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Backup: Hugging Face Inference API (gratuito con límites generosos)
        self.hf_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

        
        self.hf_headers = {"Authorization": settings.HF_TOKEN}  # Opcional, mejor con token
    
    def select_best_answer_ollama(self, question, answers):
        """Usa Ollama local para seleccionar la mejor respuesta"""
        try:
            answers_text = "\n".join([f"{i+1}. {ans['respuesta']}" for i, ans in enumerate(answers)])
            
            prompt = f"""Eres un asistente que debe seleccionar la respuesta más relevante para una pregunta.

Pregunta: {question}

Respuestas disponibles:
{answers_text}

Responde SOLO con el número de la respuesta más relevante (1, 2, 3, 4 o 5). No expliques, solo el número."""

            payload = {
                "model": "llama3.2:1b",  # Modelo ligero y rápido
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 5
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                answer_text = result.get('response', '').strip()
                
                # Extraer número de la respuesta
                numbers = re.findall(r'\b([1-5])\b', answer_text)
                if numbers:
                    return int(numbers[0]) - 1  # Convertir a índice (0-4)
            
        except Exception as e:
            print(f"Error con Ollama: {e}")
        
        return None
    
    def select_best_answer_hf(self, question, answers):
        """Usa Hugging Face como backup"""
        try:
            answers_text = " | ".join([f"{i+1}:{ans['respuesta'][:50]}..." for i, ans in enumerate(answers)])
            
            payload = {
                "inputs": f"Question: {question} | Choose best from: {answers_text} | Answer number:",
                "parameters": {
                    "max_length": 10,
                    "temperature": 0.1
                }
            }
            
            response = requests.post(self.hf_url, headers=self.hf_headers, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0:
                    answer_text = result[0].get('generated_text', '')
                    numbers = re.findall(r'\b([1-5])\b', answer_text)
                    if numbers:
                        return int(numbers[0]) - 1
                        
        except Exception as e:
            print(f"Error con HuggingFace: {e}")
        
        return None

class LocalScorer:
    """Scoring local sin IA externa"""
    
    @staticmethod
    def calculate_similarity(question, answer):
        """Calcula similitud usando múltiples métricas"""
        question_clean = clean_prompt(question).lower()
        answer_clean = clean_prompt(answer).lower()
        
        # 1. Similitud de secuencia
        seq_sim = SequenceMatcher(None, question_clean, answer_clean).ratio()
        
        # 2. Palabras clave en común
        q_words = set(question_clean.split())
        a_words = set(answer_clean.split())
        common_words = q_words.intersection(a_words)
        keyword_sim = len(common_words) / max(len(q_words), 1)
        
        # 3. TF-IDF simplificado
        all_words = list(q_words.union(a_words))
        tfidf_sim = LocalScorer._simple_tfidf_similarity(question_clean, answer_clean, all_words)
        
        # Puntuación combinada
        final_score = (seq_sim * 0.3) + (keyword_sim * 0.4) + (tfidf_sim * 0.3)
        return final_score
    
    @staticmethod
    def _simple_tfidf_similarity(text1, text2, vocabulary):
        """TF-IDF simplificado"""
        def get_tf_idf(text, vocab):
            words = text.split()
            tf = Counter(words)
            tf_idf = {}
            for word in vocab:
                tf_score = tf.get(word, 0) / len(words) if words else 0
                idf_score = math.log(2 / (1 + (1 if word in words else 0)))
                tf_idf[word] = tf_score * idf_score
            return tf_idf
        
        tfidf1 = get_tf_idf(text1, vocabulary)
        tfidf2 = get_tf_idf(text2, vocabulary)
        
        # Similitud coseno
        dot_product = sum(tfidf1[word] * tfidf2[word] for word in vocabulary)
        norm1 = math.sqrt(sum(val**2 for val in tfidf1.values()))
        norm2 = math.sqrt(sum(val**2 for val in tfidf2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)

# Instancias globales
ai_selector = AISelector()
local_scorer = LocalScorer()

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    topic = data.get("tema")
    question = data.get("pregunta", "")
    to_find = clean_prompt(question).strip()
    
    print("Pregunta original:", question)
    print("Búsqueda:", to_find)
    
    colec = mongodb.get_collection(topic)
    
    # Obtener las mejores 5 respuestas
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
        return jsonify({"respuesta": "Lo siento, no encontré una respuesta."}), 404
    
    print("Estos son los docs: ", docs)
    # Filtrar por score mínimo
    min_score = 3.0
    valid_docs = [doc for doc in docs if doc.get("score", 0) >= min_score]
    
    if not valid_docs:
        return jsonify({"respuesta": "Lo siento, no encontré una respuesta relevante."}), 404
    
    
    
    # Si solo hay una respuesta válida, devolverla
    if len(valid_docs) == 1:
        return jsonify({
            "respuesta": valid_docs[0]["respuesta"],
            "metodo": "unica_respuesta",
            "score": valid_docs[0]["score"]
        }), 200
    
    # Intentar selección con IA
    best_index = None
    selection_method = "local_scoring"
    
    # 1. Intentar Ollama
    best_index = ai_selector.select_best_answer_ollama(question, valid_docs)
    if best_index is not None:
        selection_method = "ollama_ai"
    else:
        # 2. Intentar Hugging Face
        best_index = ai_selector.select_best_answer_hf(question, valid_docs)
        if best_index is not None:
            selection_method = "huggingface_ai"
    
    # 3. Fallback: Scoring local
    if best_index is None:
        similarities = []
        for doc in valid_docs:
            # Combinar diferentes campos para mejor matching
            full_text = f"{doc.get('pregunta', '')} {doc.get('respuesta', '')} {' '.join(doc.get('tags', []))}"
            similarity = local_scorer.calculate_similarity(question, full_text)
            similarities.append(similarity)
        
        best_index = similarities.index(max(similarities))
        selection_method = "local_scoring"
    
    # Validar índice
    if best_index < 0 or best_index >= len(valid_docs):
        best_index = 0
    
    selected_doc = valid_docs[best_index]

    print("Se termino usando: ", selection_method)
    
    return jsonify({
        "respuesta": selected_doc["respuesta"],
        "metodo": selection_method,
        "score": selected_doc.get("score"),
        "total_encontradas": len(docs),
        "validas": len(valid_docs),
        "subtema": selected_doc.get("subtema")
    }), 200

# Ruta adicional para debugging
@bp.route("/ask-debug", methods=["POST"])
def ask_debug():
    """Versión debug que muestra todas las respuestas y scores"""
    data = request.get_json()
    topic = data.get("tema")
    question = data.get("pregunta", "")
    to_find = clean_prompt(question).strip()
    
    colec = mongodb.get_collection(topic)
    docs = list(colec.find(
        {"$text": {"$search": to_find}},
        {
            "score": {"$meta": "textScore"},
            "respuesta": 1,
            "pregunta": 1,
            "subtema": 1,
            "tags": 1
        }
    ).sort([("score", {"$meta": "textScore"})]).limit(5))
    
    if not docs:
        return jsonify({"error": "No se encontraron respuestas"}), 404
    
    # Calcular scores locales para debugging
    debug_info = []
    for i, doc in enumerate(docs):
        full_text = f"{doc.get('pregunta', '')} {doc.get('respuesta', '')} {' '.join(doc.get('tags', []))}"
        local_sim = local_scorer.calculate_similarity(question, full_text)
        
        debug_info.append({
            "indice": i,
            "mongo_score": doc.get("score"),
            "similitud_local": local_sim,
            "respuesta": doc["respuesta"][:100] + "...",
            "subtema": doc.get("subtema"),
            "tags": doc.get("tags", [])
        })
    
    return jsonify({
        "pregunta": question,
        "busqueda": to_find,
        "resultados": debug_info
    }), 200