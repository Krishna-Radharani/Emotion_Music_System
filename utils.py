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
        # Your exact emotion list - Gemini MUST choose from these
        emotion_options = [
            "action", "adventure", "advertising", "background", "ballad", "calm", "children", "christmas",
            "commercial", "cool", "corporate", "dark", "deep", "documentary", "drama", "dramatic", "dream",
            "emotional", "energetic", "epic", "fast", "film", "fun", "funny", "game", "groovy", "happy", "heavy",
            "holiday", "hopeful", "inspiring", "love", "meditative", "melancholic", "mellow", "melodic",
            "motivational", "movie", "nature", "party", "positive", "powerful", "relaxing", "retro", "romantic",
            "sad", "sexy", "slow", "soft", "soundscape", "space", "sport", "summer", "trailer", "travel", "upbeat",
            "uplifting"
        ]
        
        # Create the options string for the prompt
        options_str = ", ".join(emotion_options)
        
        payload = {
            "contents": [
                {"parts": [{"text": f"Analyze the emotion in this sentence: '{user_text}' Return only one word from these options ({options_str})."}]}
            ]
        }
        
        response = requests.post(GEMINI_API_URL, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            emotion = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
            
            # Clean up the response (remove any extra text, punctuation)
            import re
            emotion = re.sub(r'[^a-z]', '', emotion)  # Keep only lowercase letters
            
            # Validate the emotion is in our allowed list
            if emotion in emotion_options:
                confidence = 0.85
                return emotion, confidence  # Return exact emotion from your list!
            else:
                # If Gemini returns something not in the list, find closest match
                print(f"Gemini returned '{emotion}' which is not in the allowed list")
                
                # Simple fallback mapping for common cases
                fallback_mapping = {
                    'nostalgic': 'melancholic',
                    'longing': 'romantic', 
                    'missing': 'melancholic',
                    'joyful': 'happy',
                    'excited': 'energetic',
                    'peaceful': 'calm',
                    'angry': 'dramatic',
                    'fear': 'dark',
                    'surprised': 'epic'
                }
                
                fallback_emotion = fallback_mapping.get(emotion, 'emotional')
                return fallback_emotion, 0.7
        else:
            print(f"Gemini API error: {response.status_code}")
            return None, 0
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None, 0
