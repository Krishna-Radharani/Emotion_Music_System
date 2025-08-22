import streamlit as st
import nltk
import requests
import json

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def nltk_setup():
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)

def call_gemini_emotion_api(user_text):
    try:
        payload = {
            "contents": [
                {"parts": [{"text": f"Analyze the emotion in this sentence: '{user_text}' Return only one word from these options (Happy, Sad, Angry, Energetic, Neutral, Fear, Surprise, Calm)."}]}
            ]
        }
        response = requests.post(GEMINI_API_URL, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            emotion = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
            mood_mapping = {
                'happy': 'happy',
                'sad': 'sad',
                'angry': 'angry',
                'energetic': 'energetic',
                'neutral': 'neutral',
                'fear': 'fear',
                'surprise': 'surprise',
                'calm': 'calm',
                'excited': 'energetic',
                'relaxed': 'calm'
            }
            detected_mood = mood_mapping.get(emotion, 'neutral')
            confidence = 0.85
            return detected_mood, confidence
        else:
            print(f"Gemini API error: {response.status_code}")
            return None, 0
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None, 0