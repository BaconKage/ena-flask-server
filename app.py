from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import math
import random
import os
from textblob import TextBlob

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama3-8b-8192"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

user_sessions = {}

class EnaTherapistCore:
    def __init__(self):
        self.emotion = "neutral"
        self.context_history = []
        self.sentiment_score = 0
        self.mood_score = 0
        self.prev_mood_score = 0
        self.prev_emotion = "neutral"
        self.user_state = {
            "emotional_valence": "neutral",
            "energy_level": "neutral",
            "needs": "listening"
        }

    def calculate_entropy(self, message):
        words = message.lower().split()
        if not words:
            return 0
        unique_words = set(words)
        prob_dist = [words.count(w)/len(words) for w in unique_words]
        return -sum(p * math.log2(p) for p in prob_dist)

    def analyze_sentiment(self, message):
        return TextBlob(message).sentiment.polarity

    def boost_sentiment(self, message, sentiment):
        positive_keywords = ["happy", "excited", "love", "peaceful", "good", "fun", "relax", "chilling"]
        if any(k in message.lower() for k in positive_keywords):
            return min(sentiment + 0.3, 1.0)
        return sentiment

    def update_emotion(self, message):
        self.context_history.append(message)
        if len(self.context_history) > 6:
            self.context_history.pop(0)

        sentiment = self.analyze_sentiment(message)
        boosted = self.boost_sentiment(message, sentiment)
        self.sentiment_score = boosted
        entropy = self.calculate_entropy(message)

        mood_shift = (boosted * 2.5) + random.uniform(-0.1, 0.1)
        if entropy > 2.2 and abs(boosted) < 0.2:
            mood_shift += random.uniform(-0.2, 0.1)

        self.mood_score = max(min(self.mood_score + mood_shift, 5), -5)

        if abs(self.mood_score - self.prev_mood_score) < 1:
            self.emotion = self.prev_emotion
        else:
            self.emotion = (
                "happy" if self.mood_score >= 3 else
                "hopeful" if self.mood_score >= 1 else
                "neutral" if self.mood_score > -1 else
                "sad" if self.mood_score > -4 else
                "distressed"
            )

        self.prev_mood_score = self.mood_score
        self.prev_emotion = self.emotion

        # Emotional valence
        self.user_state["emotional_valence"] = (
            "positive" if boosted > 0.3 else
            "negative" if boosted < -0.3 else
            "neutral"
        )

        # Energy level
        msg = message.lower()
        if any(w in msg for w in ["tired", "exhausted", "drained", "done"]):
            self.user_state["energy_level"] = "low"
        elif any(w in msg for w in ["motivated", "productive", "excited"]):
            self.user_state["energy_level"] = "high"
        else:
            self.user_state["energy_level"] = "neutral"

        # Needs
        if "help" in msg or "talk" in msg or "support" in msg:
            self.user_state["needs"] = "support"
        elif "idk" in msg or "confused" in msg or entropy > 2.8:
            self.user_state["needs"] = "clarity"
        else:
            self.user_state["needs"] = "listening"

    def get_context_memory(self):
        return "; ".join(self.context_history[-3:])

    def generate_final_prompt(self):
        last_msg = self.context_history[-1].strip().lower()
        greetings = ["hi", "hello", "hey", "hii", "hola", "yo"]
        is_greeting = last_msg in greetings

        if is_greeting:
            return (
                "You are Ena, a gentle and attentive AI therapist. The user greeted you. "
                "Say hello warmly, and invite them to share what's on their mind at their own pace. "
                "Don't analyze. Just be welcoming and open."
            )

        avoid_greeting = "Avoid greeting again. You're already in conversation."

        emotion_tone = {
            "happy": "Use warm encouragement and ask open questions.",
            "hopeful": "Use affirming, curious tone and offer perspective.",
            "neutral": "Be calm, reflective and non-intrusive.",
            "sad": "Be gentle, slow-paced, and emotionally validating.",
            "distressed": "Be grounding, non-judgmental, and offer space."
        }[self.emotion]

        memory = self.get_context_memory()

        pacing = (
            "Only ask 1 short follow-up at a time. Mirror what the user says. "
            "If user is sarcastic or angry, acknowledge their tone without probing too much. "
            "Never assume facts unless the user has said them explicitly."
        )

        return (
            f"You are Ena, an emotionally aware, grounded AI therapist. {avoid_greeting} "
            f"Current user emotion: {self.emotion}, energy: {self.user_state['energy_level']}, need: {self.user_state['needs']}. "
            f"{emotion_tone} {pacing} Use a natural, conversational tone. Avoid inspirational quotes. "
            f"Recent memory: {memory}"
        )

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")
    session_id = request.headers.get("Session-ID", request.remote_addr)

    if session_id not in user_sessions:
        user_sessions[session_id] = EnaTherapistCore()
    ena = user_sessions[session_id]

    if not user_input:
        return jsonify({"error": "No message received."}), 400

    ena.update_emotion(user_input)
    prompt = ena.generate_final_prompt() + "\n" + user_input

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": f"You are Ena, a compassionate therapist AI. Your job is to listen, reflect, validate and gently respond. Never diagnose. Current emotion: {ena.emotion}. Energy: {ena.user_state['energy_level']}, Need: {ena.user_state['needs']}."
            },
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        reply = response.json()["choices"][0]["message"]["content"]
    except Exception:
        reply = "I'm here, but something went wrong on my end. Can we try again in a moment?"

    return jsonify({"reply": reply, "emotion": ena.emotion})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
