from config import settings
import requests
import re

class AISelector:
    def __init__(self):
        
        self.ollama_url = "http://localhost:11434/api/generate"
        
        self.hf_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

        self.hf_headers = {"Authorization": settings.HF_TOKEN}
    
    def select_best_answer_ollama(self, question, answers):
        try:
            answers_text = "\n".join([f"{i+1}. {ans['respuesta']}" for i, ans in enumerate(answers)])
            
            prompt = f"""Eres un asistente que debe seleccionar la respuesta más relevante para una pregunta.

Pregunta: {question}

Respuestas disponibles:
{answers_text}

Responde SOLO con el número de la respuesta más relevante (1, 2, 3, 4 o 5). No expliques, solo el número."""

            payload = {
                "model": "llama3.2:1b",  
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
                
                numbers = re.findall(r'\b([1-5])\b', answer_text)
                if numbers:
                    return int(numbers[0]) - 1  
            
        except Exception as e:
            print(f"Error con Ollama: {e}")
        
        return None
    
    def select_best_answer_hf(self, question, answers):
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
    
ai_selector = AISelector()