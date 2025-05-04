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

class EnaTherapyEngine:
    def __init__(self):
        self.context = []
        self.emotion = "neutral"
        self.mood = 0
        self.prev_response = ""
        self.state = {"valence": "neutral", "energy": "medium", "need": "listening"}

    def update_context(self, user_input):
        self.context.append(user_input)
        if len(self.context) > 8:
            self.context.pop(0)

    def detect_category(self, text):
        lower = text.lower()
        if any(w in lower for w in ["died", "loss", "passed away", "funeral"]):
            return "grief"
        if any(w in lower for w in ["kill myself", "suicidal", "end it all", "nothing matters", "disappear"]):
            return "crisis"
        if any(w in lower for w in ["idk", "nothing", "bored", "meh"]):
            return "flat"
        if any(w in lower for w in ["you are weird", "dumb bot", "lol", "haha"]):
            return "sarcasm"
        if any(w in lower for w in ["what is life", "meaning of life", "why am i here", "am i a bad person"]):
            return "deep"
        if any(w in lower for w in ["anxious", "depressed", "panic", "can't sleep"]):
            return "mental_health"
        if any(w in lower for w in ["hate this", "this sucks", "i’m angry", "why me"]):
            return "vent"
        return "neutral"

    def analyze_sentiment(self, text):
        return TextBlob(text).sentiment.polarity

    def generate_prompt(self, user_input):
        category = self.detect_category(user_input)
        memory = " ".join(self.context[-3:])

        base = "You are Ena, an emotionally intelligent AI therapist. Avoid repeating facts. Avoid being robotic. Prioritize presence over productivity."

        category_prompts = {
            "grief": "User is grieving. Respond with tenderness. Validate their loss without rushing them. No 'cheer up'. Just be with them.",
            "crisis": "User may be in distress or danger. Do not offer medical advice. Be fully present. Say they matter. Offer support and suggest talking more. Never leave them alone emotionally.",
            "flat": "User is emotionally flat or disengaged. Don't probe. Say it's okay to feel nothing. Offer calm companionship.",
            "sarcasm": "User is sarcastic or defensive. Don’t react. Respond kindly and curiously, asking if they want to share more genuinely.",
            "deep": "User asked a philosophical question. Reflect it. Don’t answer. Ask where it’s coming from emotionally.",
            "mental_health": "User is sharing mental health symptoms. Do not diagnose. Validate their struggle. Ask about how it feels emotionally.",
            "vent": "User is venting frustration. Do not fix it. Validate. Ask one grounding follow-up.",
            "neutral": "Respond calmly and openly. Invite gentle exploration. Offer space if user seems unsure."
        }

        prompt = f"{base} Category: {category}. {category_prompts[category]} Memory: {memory}"
        return prompt

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = request.headers.get("Session-ID", request.remote_addr)

    if not message:
        return jsonify({"error": "No input provided."}), 400

    if session_id not in user_sessions:
        user_sessions[session_id] = EnaTherapyEngine()
    ena = user_sessions[session_id]

    ena.update_context(message)
    prompt = ena.generate_prompt(message) + "\nUser said: " + message

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Respond like a real, grounded, emotionally intelligent therapist. Don't be robotic or overly chatty."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        content = response.json()["choices"][0]["message"]["content"]
        ena.prev_response = content
    except Exception:
        content = "I'm here, but something went wrong. Let's pause and try again in a bit."

    return jsonify({"reply": content})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
