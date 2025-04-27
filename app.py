from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as ena
import random
import math
from textblob import TextBlob

# Initialize Flask
app = Flask(__name__)
CORS(app)  # Allow CORS so frontend can call this API

# Configure Gemini API
API_KEY = "AIzaSyBILa0l3c3kHS9Kw04dEBYqFyBxIdej4KY"  # Ideally, keep this secret using environment variables!
ena.configure(api_key=API_KEY)
model = ena.GenerativeModel("gemini-2.0-flash")
chat_bot = model.start_chat()

# Ena Emotion Engine Class
class EnaEmotionEngine:
    def __init__(self):
        self.emotion = "neutral"
        self.previous_message = ""
        self.context_history = []
        self.sentiment_score = 0

    def calculate_entropy(self, message):
        words = message.lower().split()
        unique_words = set(words)
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
        self.sentiment_score = self.analyze_sentiment(user_message)

        if self.sentiment_score > 0.2:
            self.emotion = "happy"
        elif self.sentiment_score < -0.2:
            self.emotion = "sad"
        else:
            self.emotion = "neutral"

        if entropy > 1.5:
            self.emotion = random.choice(["happy", "sad", "neutral", "confused", "surprised", "angry"])

        if "happy" in self.context_history[-3:]:
            self.emotion = "happy"
        elif "sad" in self.context_history[-3:]:
            self.emotion = "sad"

        if entropy > 1.0 and self.sentiment_score < 0:
            self.emotion = "angry"

    def get_emotion_prompt(self):
        if self.emotion == "happy":
            return "Respond cheerfully with excitement."
        elif self.emotion == "sad":
            return "Respond softly with sadness."
        elif self.emotion == "neutral":
            return "Respond neutrally, without any strong emotional tone."
        elif self.emotion == "confused":
            return "Respond with slight confusion and curiosity."
        elif self.emotion == "surprised":
            return "Respond with astonishment and curiosity."
        elif self.emotion == "angry":
            return "Respond with frustration and intensity."
        else:
            return "Respond neutrally."

# Create Ena Emotion Engine
ena_emotions = EnaEmotionEngine()

# Define the chat route
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message', '')

    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    # Update Ena's emotional state
    ena_emotions.update_emotion(user_input)

    # Get emotional instruction
    emotion_instruction = ena_emotions.get_emotion_prompt()

    # Combine emotional instruction with user input
    full_prompt = f"{emotion_instruction} {user_input}"

    try:
        # Get response from Gemini model
        response = chat_bot.send_message(full_prompt)
        reply_text = response.text
    except Exception as e:
        reply_text = "Sorry, I couldn't generate a response due to an internal error."

    # Return response
    return jsonify({
        "reply": reply_text,
        "emotion": ena_emotions.emotion
    })

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
