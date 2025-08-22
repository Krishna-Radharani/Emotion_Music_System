import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

class TextMoodAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.analyzer = SentimentIntensityAnalyzer()
        self.mood_keywords = {
            'happy': ['happy', 'joy', 'excited', 'cheerful', 'glad', 'elated', 'euphoric', 'delighted', 'amazing', 'wonderful', 'great', 'fantastic', 'awesome'],
            'sad': ['sad', 'depressed', 'down', 'blue', 'melancholy', 'gloomy', 'sorrowful', 'heartbroken', 'crying', 'tears', 'lonely', 'empty'],
            'angry': ['angry', 'mad', 'furious', 'rage', 'annoyed', 'irritated', 'frustrated', 'pissed', 'hate', 'livid', 'outraged'],
            'fear': ['scared', 'afraid', 'terrified', 'anxious', 'worried', 'nervous', 'panic', 'frightened', 'fearful', 'apprehensive'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'stunned', 'bewildered', 'confused', 'unexpected'],
            'neutral': ['okay', 'fine', 'normal', 'regular', 'usual', 'typical', 'average'],
            'energetic': ['energetic', 'active', 'pumped', 'motivated', 'driven', 'dynamic', 'vigorous', 'lively'],
            'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'quiet', 'restful', 'zen', 'meditative'],
        }

    def preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        tokens = word_tokenize(text)
        processed_tokens = []
        for token in tokens:
            if token not in self.stop_words and len(token) > 2:
                lemmatized = self.lemmatizer.lemmatize(token)
                processed_tokens.append(lemmatized)
        return processed_tokens

    def extract_mood_from_keywords(self, tokens):
        mood_scores = {mood: 0 for mood in self.mood_keywords.keys()}
        for token in tokens:
            for mood, keywords in self.mood_keywords.items():
                if token in keywords:
                    mood_scores[mood] += 1
        if max(mood_scores.values()) > 0:
            return max(mood_scores, key=mood_scores.get)
        return None

    def analyze_sentiment(self, text):
        vader_scores = self.analyzer.polarity_scores(text)
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        compound = vader_scores['compound']
        if compound >= 0.5 or textblob_polarity > 0.3:
            return 'happy'
        elif compound <= -0.5 or textblob_polarity < -0.3:
            return 'sad'
        elif vader_scores['neg'] > 0.6:
            return 'angry'
        elif abs(compound) < 0.1 and abs(textblob_polarity) < 0.1:
            return 'neutral'
        elif compound > 0.1:
            return 'calm'
        else:
            return 'neutral'

    def predict_mood(self, user_input):
        if not user_input.strip():
            return 'neutral', 0.5
        tokens = self.preprocess_text(user_input)
        keyword_mood = self.extract_mood_from_keywords(tokens)
        sentiment_mood = self.analyze_sentiment(user_input)
        final_mood = keyword_mood if keyword_mood else sentiment_mood
        confidence = 0.8 if keyword_mood else 0.6
        return final_mood, confidence