from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as ena
import random
import math
from textblob import TextBlob

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow frontend to talk to backend

# Configure Gemini AI
API_KEY = "AIzaSyBILa0l3c3kHS9Kw04dEBYqFyBxIdej4KY"
ena.configure(api_key=API_KEY)
model = ena.GenerativeModel("gemini-2.0-flash")
chat_bot = model.start_chat()

# Define Ena's Emotional Engine
class EnaEmotionEngine:
    def __init__(self):
        self.emotion = "neutral"
        self.context_history = []
        self.sentiment_score = 0
        self.mood_score = 0  # Mood score from -5 (very angry) to +5 (very happy)

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

    def update_emotion(self, user_message):
        self.context_history.append(user_message)
        if len(self.context_history) > 5:
            self.context_history.pop(0)

        entropy = self.calculate_entropy(user_message)
        sentiment = self.analyze_sentiment(user_message)
        self.sentiment_score = sentiment

        # Update mood based on sentiment
        self.mood_score += (sentiment * 2) + random.uniform(-0.2, 0.2)

        # Influence by entropy
        if entropy > 2.0 and abs(sentiment) < 0.3:
            self.mood_score += random.uniform(-0.5, 0.5)

        # Clamp mood between -5 and +5
        self.mood_score = max(min(self.mood_score, 5), -5)

        # Determine current emotion
        if self.mood_score >= 3:
            self.emotion = "happy"
        elif self.mood_score >= 1:
            self.emotion = "surprised"
        elif self.mood_score > -1:
            self.emotion = "neutral"
        elif self.mood_score > -4:
            self.emotion = "sad"
        else:
            self.emotion = "angry"

    def get_emotion_prompt(self):
        if self.emotion == "happy":
            return "You are a supportive therapist. Respond with warm encouragement and shared happiness."
        elif self.emotion == "sad":
            return "You are a supportive therapist. Respond gently and offer emotional support."
        elif self.emotion == "neutral":
            return "You are a supportive therapist. Respond calmly, keeping a balanced and professional tone."
        elif self.emotion == "confused":
            return "You are a supportive therapist. Respond curiously and ask clarifying questions in a caring way."
        elif self.emotion == "surprised":
            return "You are a supportive therapist. Respond with kind astonishment and invite the user to share more."
        elif self.emotion == "angry":
            return "You are a supportive therapist. Respond with calm empathy, validating the user's emotions while maintaining peace."
        else:
            return "You are a supportive therapist. Respond calmly and kindly."

# Create Ena instance
ena_emotions = EnaEmotionEngine()

# Define chat route
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message', '')

    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    # Update Ena's emotional state
    ena_emotions.update_emotion(user_input)

    # Build emotional prompt
    emotion_instruction = ena_emotions.get_emotion_prompt()

    full_prompt = f"{emotion_instruction} {user_input}"

    try:
        response = chat_bot.send_message(full_prompt)
        reply_text = response.text
    except Exception as e:
        reply_text = "Sorry, I couldn't generate a response right now."

    return jsonify({
        "reply": reply_text,
        "emotion": ena_emotions.emotion
    })

# Run Flask app (for local testing)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
