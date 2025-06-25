from utils import clean_prompt
from difflib import SequenceMatcher
from collections import Counter
import math

class LocalScorer:
    @staticmethod
    def calculate_similarity(question, answer):
        question_clean = clean_prompt(question).lower()
        answer_clean = clean_prompt(answer).lower()
        
        seq_sim = SequenceMatcher(None, question_clean, answer_clean).ratio()
        
        q_words = set(question_clean.split())
        a_words = set(answer_clean.split())
        common_words = q_words.intersection(a_words)
        keyword_sim = len(common_words) / max(len(q_words), 1)
        
        all_words = list(q_words.union(a_words))
        tfidf_sim = LocalScorer._simple_tfidf_similarity(question_clean, answer_clean, all_words)
        
        final_score = (seq_sim * 0.3) + (keyword_sim * 0.4) + (tfidf_sim * 0.3)
        return final_score
    
    @staticmethod
    def _simple_tfidf_similarity(text1, text2, vocabulary):
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
        
        dot_product = sum(tfidf1[word] * tfidf2[word] for word in vocabulary)
        norm1 = math.sqrt(sum(val**2 for val in tfidf1.values()))
        norm2 = math.sqrt(sum(val**2 for val in tfidf2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)

local_scorer = LocalScorer()