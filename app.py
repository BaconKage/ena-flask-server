from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as ena
import random
import math
from textblob import TextBlob

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow frontend access

# Configure Gemini AI
API_KEY = "AIzaSyBILa0l3c3kHS9Kw04dEBYqFyBxIdej4KY"
ena.configure(api_key=API_KEY)
model = ena.GenerativeModel("gemini-2.0-flash")
chat_bot = model.start_chat()

# Ena 4.0 Engine: Emotion + Cognition
class EnaEmotionCognitiveEngine:
    def __init__(self):
        self.emotion = "neutral"
        self.context_history = []
        self.sentiment_score = 0
        self.mood_score = 0  # -5 to +5
        self.consciousness_thoughts = random.choice([
            "I'm feeling thoughtful today.",
            "I'm trying to stay hopeful.",
            "I'm feeling steady and reflective.",
            "I'm a bit curious about emotions right now.",
            "I'm focusing on calmness today."
        ])
        self.user_state = {
            "energy_level": "neutral",
            "emotional_valence": "neutral",
            "needs": "listening"
        }

    # Analyze entropy
    def calculate_entropy(self, message):
        words = message.lower().split()
        unique_words = set(words)
        if not words:
            return 0
        probability_distribution = [words.count(word) / len(words) for word in unique_words]
        entropy = -sum(p * math.log2(p) for p in probability_distribution)
        return entropy

    # Analyze sentiment
    def analyze_sentiment(self, message):
        blob = TextBlob(message)
        return blob.sentiment.polarity

    # Cognitive analysis of user's emotional state
    def cognitive_analysis(self, message):
        sentiment = self.analyze_sentiment(message)
        entropy = self.calculate_entropy(message)

        # Update emotional valence
        if sentiment > 0.3:
            self.user_state["emotional_valence"] = "positive"
        elif sentiment < -0.3:
            self.user_state["emotional_valence"] = "negative"
        else:
            self.user_state["emotional_valence"] = "neutral"

        # Update energy level based on keywords
        lower_message = message.lower()
        if any(word in lower_message for word in ["tired", "exhausted", "low energy", "drained"]):
            self.user_state["energy_level"] = "low"
        elif any(word in lower_message for word in ["excited", "energized", "active", "motivated"]):
            self.user_state["energy_level"] = "high"
        else:
            self.user_state["energy_level"] = "neutral"

        # Update needs based on context
        if "help" in lower_message or "support" in lower_message:
            self.user_state["needs"] = "support"
        elif "confused" in lower_message or entropy > 2.5:
            self.user_state["needs"] = "clarity"
        else:
            self.user_state["needs"] = "listening"

    # Update Ena's emotional state
    def update_emotion(self, user_message):
        self.context_history.append(user_message)
        if len(self.context_history) > 5:
            self.context_history.pop(0)

        sentiment = self.analyze_sentiment(user_message)
        entropy = self.calculate_entropy(user_message)

        mood_change = (sentiment * 1.5) + random.uniform(-0.2, 0.2)
        if entropy > 2.0 and abs(sentiment) < 0.3:
            mood_change += random.uniform(-0.3, 0.3)

        self.mood_score += mood_change
        self.mood_score = max(min(self.mood_score, 5), -5)

        if self.mood_score >= 3:
            self.emotion = "happy"
        elif self.mood_score >= 1:
            self.emotion = "hopeful"
        elif self.mood_score > -1:
            self.emotion = "neutral"
        elif self.mood_score > -4:
            self.emotion = "sad"
        else:
            self.emotion = "angry"

        # After emotion update, run cognitive analysis too
        self.cognitive_analysis(user_message)

    # Generate final prompt combining Emotion + Cognition
    def generate_final_prompt(self):
        # Emotional instruction
        if self.emotion == "happy":
            emotion_instruction = "Respond warmly and joyfully, offering shared happiness and encouragement."
        elif self.emotion == "hopeful":
            emotion_instruction = "Respond with calm optimism, focusing on possibilities and positive outlook."
        elif self.emotion == "neutral":
            emotion_instruction = "Respond thoughtfully and calmly, maintaining a peaceful presence."
        elif self.emotion == "sad":
            emotion_instruction = "Respond gently with compassion, acknowledging emotional pain kindly."
        elif self.emotion == "angry":
            emotion_instruction = "Respond with patience and empathy, helping process difficult emotions safely."
        else:
            emotion_instruction = "Respond thoughtfully and with kindness."

        # Cognitive instruction
        cognitive_thoughts = f"The user seems to have {self.user_state['energy_level']} energy and a {self.user_state['emotional_valence']} emotional tone. Focus on providing {self.user_state['needs']}."

        # Occasionally Ena mentions her own inner state
        if random.random() < 0.25:
            consciousness_reflection = f"Also, {self.consciousness_thoughts} "
        else:
            consciousness_reflection = ""

        # Final Prompt
        full_prompt = f"You are a supportive therapist. {consciousness_reflection}{emotion_instruction} {cognitive_thoughts}"

        return full_prompt

# Create Ena instance
ena_engine = EnaEmotionCognitiveEngine()

# Define Chat Endpoint
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message', '')

    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    # Update Ena's emotion and cognition
    ena_engine.update_emotion(user_input)

    # Build final intelligent prompt
    full_prompt = ena_engine.generate_final_prompt() + " " + user_input

    try:
        # Get response from Gemini
        response = chat_bot.send_message(full_prompt)
        reply_text = response.text
    except Exception as e:
        reply_text = "I'm feeling a little overwhelmed. Let's slow down and continue gently."

    return jsonify({
        "reply": reply_text,
        "emotion": ena_engine.emotion
    })

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
