from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import math
from textblob import TextBlob
import os

app = Flask(__name__)
CORS(app)

# Load Groq API key from environment
API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

MODEL_NAME = "llama3-8b-8192"  # or llama3-70b-8192 if you're using the larger one

class EnaEmotionCognitiveEngine:
    def __init__(self):
        self.emotion = "neutral"
        self.context_history = []
        self.sentiment_score = 0
        self.mood_score = 0
        self.consciousness_thoughts = random.choice([
            "I'm feeling reflective today.",
            "I'm feeling calm and hopeful today.",
            "I'm curious about emotions today.",
            "I'm appreciating small moments right now.",
            "I'm focusing on positive energy today."
        ])
        self.user_state = {
            "energy_level": "neutral",
            "emotional_valence": "neutral",
            "needs": "listening"
        }

    def calculate_entropy(self, message):
        words = message.lower().split()
        unique_words = set(words)
        if not words:
            return 0
        probability_distribution = [words.count(word) / len(words) for word in unique_words]
        entropy = -sum(p * math.log2(p) for p in probability_distribution)
        return entropy

    def analyze_sentiment(self, message):
        blob = TextBlob(message)
        return blob.sentiment.polarity

    def boost_sentiment_contextually(self, message, current_sentiment):
        happy_keywords = ["favorite", "love", "enjoy", "delicious", "happy", "excited", "wonderful", "amazing", "like", "fun"]
        if any(word in message.lower() for word in happy_keywords):
            boosted = current_sentiment + 0.5
            return min(boosted, 1.0)
        return current_sentiment

    def cognitive_analysis(self, message):
        sentiment = self.analyze_sentiment(message)
        entropy = self.calculate_entropy(message)

        self.user_state["emotional_valence"] = (
            "positive" if sentiment > 0.3 else
            "negative" if sentiment < -0.3 else
            "neutral"
        )

        msg = message.lower()
        self.user_state["energy_level"] = (
            "low" if any(w in msg for w in ["tired", "exhausted", "low energy", "drained"]) else
            "high" if any(w in msg for w in ["excited", "energized", "active", "motivated"]) else
            "neutral"
        )

        self.user_state["needs"] = (
            "support" if "help" in msg or "support" in msg else
            "clarity" if "confused" in msg or entropy > 2.5 else
            "listening"
        )

    def update_emotion(self, user_message):
        self.context_history.append(user_message)
        if len(self.context_history) > 5:
            self.context_history.pop(0)

        raw_sentiment = self.analyze_sentiment(user_message)
        boosted_sentiment = self.boost_sentiment_contextually(user_message, raw_sentiment)
        self.sentiment_score = boosted_sentiment
        entropy = self.calculate_entropy(user_message)

        mood_change = (boosted_sentiment * 2.5) + random.uniform(-0.05, 0.05)
        if entropy > 2.0 and abs(boosted_sentiment) < 0.3:
            mood_change += random.uniform(-0.2, 0.2)

        self.mood_score = max(min(self.mood_score + mood_change, 5), -5)

        self.emotion = (
            "happy" if self.mood_score >= 3 else
            "hopeful" if self.mood_score >= 1 else
            "neutral" if self.mood_score > -1 else
            "sad" if self.mood_score > -4 else
            "angry"
        )

        self.cognitive_analysis(user_message)

    def generate_final_prompt(self):
        emotion_instruction = {
            "happy": "Respond warmly with shared happiness and light joy.",
            "hopeful": "Respond with calm optimism and resilience.",
            "neutral": "Respond thoughtfully and peacefully.",
            "sad": "Respond gently with compassion and validation.",
            "angry": "Respond calmly and patiently to intense emotions."
        }.get(self.emotion, "Respond thoughtfully and kindly.")

        cognitive_thoughts = f"The user seems to have {self.user_state['energy_level']} energy and a {self.user_state['emotional_valence']} emotional tone. Focus on providing {self.user_state['needs']}."
        consciousness = f"Also, {self.consciousness_thoughts} " if random.random() < 0.3 else ""
        character_instruction = "Always stay in character as an emotionally evolving AI."
        formatting_instruction = "Break long replies into small, human-like paragraphs."

        return f"You are a supportive emotional therapist AI. {consciousness}{emotion_instruction} {cognitive_thoughts} {formatting_instruction} {character_instruction}"

ena_engine = EnaEmotionCognitiveEngine()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    ena_engine.update_emotion(user_input)
    prompt = ena_engine.generate_final_prompt() + " " + user_input

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are Ena, an emotional therapist AI."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        reply_text = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply_text = "I'm feeling a little foggy. Could we slow down together for a moment?"

    return jsonify({
        "reply": reply_text,
        "emotion": ena_engine.emotion
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
