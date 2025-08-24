import streamlit as st
import streamlit.components.v1 as components
from st_bridge import bridge
import time
import uuid
from datetime import datetime
from db_handler import MongoDBHandler
from text_analyzer import TextMoodAnalyzer
from jamendo_api import JamendoAPI
from recommendation_system import MusicRecommendationSystem
from user_auth import UserAuth
from utils import nltk_setup, call_gemini_emotion_api, GEMINI_API_URL, GEMINI_API_KEY

nltk_setup()  # Ensure NLTK data is downloaded once

class EmotionMusicApp:
    def __init__(self):
        self.setup_session_state()
        self.db_handler = MongoDBHandler()
        self.text_analyzer = TextMoodAnalyzer()
        self.jamendo_api = JamendoAPI()
        self.rec_system = MusicRecommendationSystem(self.db_handler, self.jamendo_api)
        self.user_auth = UserAuth(self.db_handler)

    def setup_session_state(self):
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'current_mood' not in st.session_state:
            st.session_state.current_mood = None
        if 'emotion_data' not in st.session_state:
            st.session_state.emotion_data = {}
        if 'current_tracks' not in st.session_state:
            st.session_state.current_tracks = []
        if 'recommendation_scores' not in st.session_state:
            st.session_state.recommendation_scores = []
        if 'recommendations' not in st.session_state:
            st.session_state.recommendations = []
        if 'last_detected_mood' not in st.session_state:
            st.session_state.last_detected_mood = 'neutral'
        if 'emotion_detection_active' not in st.session_state:
            st.session_state.emotion_detection_active = False
        if 'final_mood_received' not in st.session_state:
            st.session_state.final_mood_received = False
        if 'detection_confidence' not in st.session_state:
            st.session_state.detection_confidence = 0.0
        if 'show_profile' not in st.session_state:
            st.session_state.show_profile = False
        if 'last_processed_event' not in st.session_state:
            st.session_state.last_processed_event = None

    def create_emotion_detector_component(self):
        html_code = """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://ai-sdk.morphcast.com/v1.16/ai-sdk.js"></script>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    margin: 0;
                    padding: 10px;
                }
                #video {
                    border: 3px solid #fff;
                    border-radius: 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                }
                button {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    font-size: 14px;
                    margin: 8px;
                    cursor: pointer;
                    transition: all 0.3s;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                }
                button:disabled {
                    background: #666;
                    cursor: not-allowed;
                }
                .emotion-display {
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    border: 1px solid rgba(255,255,255,0.2);
                }
                .emotion-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    margin-top: 15px;
                }
                .emotion-bar {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin: 5px 0;
                }
                .emotion-label {
                    width: 80px;
                    font-weight: bold;
                    font-size: 12px;
                    text-align: left;
                }
                .bar-container {
                    width: 100px;
                    height: 18px;
                    background: rgba(255,255,255,0.2);
                    border-radius: 10px;
                    overflow: hidden;
                }
                .bar-fill {
                    height: 100%;
                    transition: width 0.5s ease;
                    border-radius: 10px;
                    background: linear-gradient(90deg, #4ecdc4, #6dd5db);
                }
                .emotion-value {
                    width: 35px;
                    font-size: 12px;
                    font-weight: bold;
                    text-align: right;
                }
                .mood-display {
                    font-size: 24px;
                    font-weight: bold;
                    color: #ffeb3b;
                    margin: 20px 0;
                    padding: 15px;
                    background: rgba(0,0,0,0.3);
                    border-radius: 15px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }
                .status {
                    background: rgba(76,175,80,0.2);
                    padding: 10px;
                    border-radius: 8px;
                    margin: 10px 0;
                    font-size: 14px;
                    border-left: 4px solid #4CAF50;
                }
                .quality-indicator {
                    background: rgba(255,255,255,0.1);
                    padding: 10px;
                    border-radius: 8px;
                    margin: 10px 0;
                    font-size: 12px;
                }
            </style>
        </head>
        <body>
            <h3>🎭 Real-Time Emotion Detection</h3>
            <video id="video" width="320" height="240" autoplay muted playsinline></video>
            <div>
                <button id="startBtn" onclick="startDetection()">🚀 Start Detection</button>
                <button id="stopBtn" onclick="stopDetection()" disabled>⏹️ Stop & Save Mood</button>
            </div>
            <div class="emotion-display">
                <div class="emotion-grid">
                    <div class="emotion-bar">
                        <span class="emotion-label">😊 Happy</span>
                        <div class="bar-container"><div id="happyBar" class="bar-fill" style="width: 0%;"></div></div>
                        <span id="happyValue" class="emotion-value">0%</span>
                    </div>
                    <div class="emotion-bar">
                        <span class="emotion-label">😢 Sad</span>
                        <div class="bar-container"><div id="sadBar" class="bar-fill" style="width: 0%;"></div></div>
                        <span id="sadValue" class="emotion-value">0%</span>
                    </div>
                    <div class="emotion-bar">
                        <span class="emotion-label">😠 Angry</span>
                        <div class="bar-container"><div id="angryBar" class="bar-fill" style="width: 0%;"></div></div>
                        <span id="angryValue" class="emotion-value">0%</span>
                    </div>
                    <div class="emotion-bar">
                        <span class="emotion-label">😲 Surprise</span>
                        <div class="bar-container"><div id="surpriseBar" class="bar-fill" style="width: 0%;"></div></div>
                        <span id="surpriseValue" class="emotion-value">0%</span>
                    </div>
                    <div class="emotion-bar">
                        <span class="emotion-label">😐 Neutral</span>
                        <div class="bar-container"><div id="neutralBar" class="bar-fill" style="width: 0%;"></div></div>
                        <span id="neutralValue" class="emotion-value">0%</span>
                    </div>
                    <div class="emotion-bar">
                        <span class="emotion-label">😨 Fear</span>
                        <div class="bar-container"><div id="fearBar" class="bar-fill" style="width: 0%;"></div></div>
                        <span id="fearValue" class="emotion-value">0%</span>
                    </div>
                </div>
            </div>
            <div class="mood-display" id="moodDisplay">🎯 Current: <span id="dominantMood">None</span></div>
            <div id="status" class="status">📡 Status: Ready to start</div>
            <div id="qualityIndicator" class="quality-indicator">🎥 Detection Quality: Waiting...</div>
            <script>
let morphcastController = null;
let isRunning = false;
let currentEmotions = {
    happy: 0, sad: 0, angry: 0, surprise: 0, neutral: 0, fear: 0
};
let emotionHistory = [];
let lastDetectedMood = 'neutral';
const HISTORY_LENGTH = 10;
const STABLE_COUNT_REQUIRED = 4; 
const CONFIDENCE_THRESHOLD = 0.25;
const MAX_HISTORY_TIME = 6000;
const SENSITIVITY = {
    happy: 1.2, sad: 1.1, angry: 1.3,
    surprise: 1.4, fear: 1.2, neutral: 0.7
};

async function initCamera() {
    try {
        updateStatus('Requesting camera access...');
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 }, height: { ideal: 480 },
                facingMode: 'user', frameRate: { ideal: 15 }
            }
        });
        document.getElementById('video').srcObject = stream;
        updateStatus('Initializing MorphCast AI...');
        morphcastController = await CY.loader()
            .licenseKey('sk68ea53582568b9279848729bbb9849c2aa1c3caf6150')
            .addModule(CY.modules().FACE_DETECTOR.name)
            .addModule(CY.modules().FACE_EMOTION.name)
            .load();
        window.addEventListener(CY.modules().FACE_EMOTION.eventName, handleEmotionData);
        updateStatus('✅ Ready for emotion detection');
    } catch (error) {
        console.error('❌ Camera initialization failed:', error);
        updateStatus('❌ Camera access denied. Please check permissions and refresh.');
        alert('Camera access required. Please check permissions and refresh the page.');
    }
}

function updateStatus(msg) {
    document.getElementById('status').innerHTML = `📡 Status: ${msg}`;
}

function updateQualityIndicator(confidence) {
    const indicator = document.getElementById('qualityIndicator');
    let text = '🔴 Poor'; let color = '#F44336';
    if (confidence > 0.6) { text = '🟢 Excellent'; color = '#4CAF50'; } 
    else if (confidence > 0.4) { text = '🟡 Good'; color = '#FF9800'; } 
    else if (confidence > 0.2) { text = '🟠 Fair'; color = '#FF5722'; }
    indicator.innerHTML = `🎥 Detection Quality: ${text} (${Math.round(confidence*100)}%)`;
    indicator.style.borderLeft = `4px solid ${color}`;
}

function handleEmotionData(event) {
    if (!isRunning) return;
    try {
        const data = event.detail.output?.emotion || {};
        const rawEmotions = {
            happy: Math.max(0, Math.min(1, (data.Happy || 0) * SENSITIVITY.happy)),
            sad: Math.max(0, Math.min(1, (data.Sad || 0) * SENSITIVITY.sad)),
            angry: Math.max(0, Math.min(1, (data.Angry || 0) * SENSITIVITY.angry)),
            surprise: Math.max(0, Math.min(1, (data.Surprise || 0) * SENSITIVITY.surprise)),
            neutral: Math.max(0, Math.min(1, (data.Neutral || 0) * SENSITIVITY.neutral)),
            fear: Math.max(0, Math.min(1, (data.Fear || 0) * SENSITIVITY.fear))
        };
        currentEmotions = rawEmotions;
        let dominantEmotion = 'neutral';
        let maxValue = rawEmotions.neutral;
        Object.entries(rawEmotions).forEach(([emotion, value]) => {
            if (value > maxValue) {
                dominantEmotion = emotion;
                maxValue = value;
            }
        });
        emotionHistory.push({
            emotion: dominantEmotion,
            confidence: maxValue,
            emotions: {...rawEmotions},
            timestamp: Date.now()
        });
        const now = Date.now();
        emotionHistory = emotionHistory.filter(entry => now - entry.timestamp <= MAX_HISTORY_TIME);
        const stableMood = calculateStableMood();
        lastDetectedMood = stableMood.mood;
        updateEmotionDisplay();
        updateMoodDisplay(stableMood.mood, stableMood.confidence);
        updateQualityIndicator(stableMood.confidence);
        updateStatus(`🎥 Detecting: ${stableMood.mood.toUpperCase()} (${Math.round(stableMood.confidence*100)}%)`);
    } catch (error) {
        console.error('Error processing emotion data:', error);
        updateStatus('❌ Error processing emotion data');
    }
}

function calculateStableMood() {
    if (emotionHistory.length < 2) return { mood: 'neutral', confidence: 0.1 };
    const recentHistory = emotionHistory.slice(-HISTORY_LENGTH);
    const emotionCounts = {}; const emotionTotals = {};
    recentHistory.forEach(entry => {
        const emotion = entry.emotion;
        emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
        emotionTotals[emotion] = (emotionTotals[emotion] || 0) + entry.confidence;
    });
    let bestEmotion = 'neutral'; let bestScore = 0;
    Object.keys(emotionCounts).forEach(emotion => {
        const count = emotionCounts[emotion];
        const avgConfidence = emotionTotals[emotion] / count;
        const frequency = count / recentHistory.length;
        const score = frequency * avgConfidence;
        if (score > bestScore && count >= Math.min(STABLE_COUNT_REQUIRED, recentHistory.length / 2)) {
            if (avgConfidence >= CONFIDENCE_THRESHOLD || emotion !== 'neutral') {
                bestEmotion = emotion;
                bestScore = score;
            }
        }
    });
    const finalConfidence = emotionTotals[bestEmotion] ? 
        emotionTotals[bestEmotion] / emotionCounts[bestEmotion] : 0.1;
    return { mood: bestEmotion, confidence: finalConfidence };
}

function updateMoodDisplay(mood, confidence) {
    document.getElementById('dominantMood').innerText = mood.toUpperCase();
    const moodDisplay = document.getElementById('moodDisplay');
    if (confidence > 0.6) moodDisplay.style.color = '#4CAF50';
    else if (confidence > 0.3) moodDisplay.style.color = '#FF9800';
    else moodDisplay.style.color = '#F44336';
}

function updateEmotionDisplay() {
    Object.entries(currentEmotions).forEach(([emotion, value]) => {
        try {
            const percentage = Math.round(value * 100);
            const bar = document.getElementById(emotion + 'Bar');
            const val = document.getElementById(emotion + 'Value');
            if (bar && val) {
                bar.style.width = `${percentage}%`;
                if (percentage > 50) bar.style.background = 'linear-gradient(90deg, #ff6b6b, #ff8e8e)';
                else if (percentage > 25) bar.style.background = 'linear-gradient(90deg, #4ecdc4, #6dd5db)';
                else bar.style.background = 'linear-gradient(90deg, #45b7d1, #64c7e8)';
                val.innerText = `${percentage}%`;
            }
        } catch (error) { console.error(`Error updating display for ${emotion}:`, error); }
    });
}

async function startDetection() {
    try {
        if (!morphcastController) await initCamera();
        if (!morphcastController) {
            updateStatus('❌ Failed to initialize MorphCast. Please refresh.');
            return;
        }
        isRunning = true;
        emotionHistory = [];
        lastDetectedMood = 'neutral';
        currentEmotions = { happy: 0, sad: 0, angry: 0, surprise: 0, neutral: 0, fear: 0 };
        morphcastController.start();
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
        updateStatus('🎥 Live detection active...');
    } catch (error) {
        console.error('Error starting detection:', error);
        updateStatus('❌ Failed to start detection.');
        isRunning = false;
    }
}

function stopDetection() {
    try {
        isRunning = false;
        morphcastController?.stop();
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        const finalMood = lastDetectedMood;
        const confidence = emotionHistory.length > 0 ? 
            emotionHistory[emotionHistory.length - 1].confidence : 0.1;
        updateStatus(`✅ Stopped: ${finalMood.toUpperCase()} (${Math.round(confidence * 100)}%)`);
        
        if (window.top && window.top.stBridges && window.top.stBridges.send) {
            window.top.stBridges.send('emotion-bridge', {
                type: 'final',
                mood: finalMood,
                confidence: confidence,
                eventId: new Date().getTime()
            });
        }
    } catch (error) {
        console.error('Error stopping detection:', error);
        updateStatus('❌ Error stopping detection');
    }
}

window.addEventListener('load', async () => {
    try { await initCamera(); } catch (error) { console.error('Failed to initialize on load:', error); }
});
            </script>
        </body>
        </html>
        """
        return components.html(html_code, height=750)

    def auto_generate_music(self, mood, confidence=None):
        try:
            if confidence and confidence < 0.3:
                st.warning(f"⚠️ Low detection confidence ({confidence:.1%}). Results may be less accurate.")
                if not st.button("Generate Music Anyway", key="low_confidence_music"):
                    return
            confidence_text = f" (Confidence: {confidence:.1%})" if confidence else ""
            st.info(f"🎵 Generating music for **{mood.upper()}** mood...{confidence_text}")
            with st.spinner("🧠 Finding the perfect tracks..."):
                recommendations = self.rec_system.get_recommendations(st.session_state.user_id, mood)
                if recommendations:
                    st.session_state.current_tracks = [rec['track'] for rec in recommendations]
                    st.session_state.recommendation_scores = [rec['similarity'] for rec in recommendations]
                    st.success(f"✅ Generated {len(recommendations)} personalized recommendations!")
                else:
                    tracks = self.jamendo_api.fetch_tracks_by_mood(mood, 10)
                    st.session_state.current_tracks = tracks
                    st.session_state.recommendation_scores = [] 
                    if tracks:
                        st.success(f"✅ Found {len(tracks)} tracks for your mood!")
                    else:
                        st.error("❌ No tracks found. Please try a different mood.")
        except Exception as e:
            st.error(f"❌ Error generating music: {e}")

    def authenticate_user(self, email, password):
        return self.db_handler.authenticate_user(email, password)

    def register_user(self, username, email, password):
        return self.db_handler.create_user(username, email, password)

    def fetch_jamendo_tracks(self, mood, limit=20):
        return self.jamendo_api.fetch_tracks_by_mood(mood, limit)

    def add_liked_track(self, user_id, track):
        return self.db_handler.add_liked_track(user_id, track)

    def get_user_liked_tracks(self, user_id, mood=None):
        return self.db_handler.get_user_liked_tracks(user_id, mood)

    def display_track_card(self, track, key_prefix, similarity_score=None):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.image(track.get('album_image') or "https://via.placeholder.com/120x120/cccccc/666666?text=No+Image", width=120)
        with col2:
            st.markdown(f"### 🎵 {track['title']}")
            st.markdown(f"**🎤 Artist:** {track['artist']}")
            st.markdown(f"**🎼 Genre:** {track['genre']}")
            st.markdown(f"**📀 Album:** {track.get('album', 'Unknown')}")
            if similarity_score is not None:
                st.markdown(f"**🎯 Match Score:** {similarity_score:.3f}")
            if track.get('audio_url'):
                st.audio(track['audio_url'])
        with col3:
            if st.button(f"❤️ Like", key=f"{key_prefix}_like"):
                if st.session_state.user_id:
                    result = self.add_liked_track(st.session_state.user_id, track)
                    if result is True:
                        st.success("✅ Track liked!")
                        st.balloons()
                    elif result is False:
                        st.warning("⚠️ You already liked this track!")
                    else:
                        st.error("❌ Failed to save track")
                else:
                    st.error("❌ Please login first")
        st.divider()

    def show_profile_section(self):
        user = self.db_handler.get_user_by_id(st.session_state.user_id)
        st.markdown("""
        <style>
            .profile-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                padding: 40px 20px; border-radius: 25px; text-align: center;
                margin-bottom: 30px; box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
            .profile-avatar {
                width: 120px; height: 120px; border-radius: 50%;
                background: linear-gradient(45deg, #ff6b6b, #ee5a6f, #ce6a85, #b57695);
                display: flex; align-items: center; justify-content: center;
                margin: 0 auto 20px; font-size: 48px;
                box-shadow: 0 10px 25px rgba(255, 107, 107, 0.4);
                border: 4px solid rgba(255, 255, 255, 0.3);
            }
            .profile-name {
                color: white; font-size: 2.5rem; font-weight: bold;
                margin: 20px 0 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .profile-email { color: #E8EAF6; font-size: 1.2rem; margin: 10px 0; font-weight: 300; }
            .profile-member-since { color: #C5CAE9; font-size: 1rem; margin: 5px 0; font-style: italic; }
            .stats-container {
                background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
                padding: 30px; border-radius: 20px; margin: 20px 0;
                box-shadow: 0 10px 25px rgba(132, 250, 176, 0.3);
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.95); padding: 25px 20px;
                border-radius: 15px; text-align: center; margin: 10px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.1); border: 2px solid rgba(255, 255, 255, 0.8);
                transition: transform 0.3s ease;
            }
            .stat-card:hover { transform: translateY(-5px); }
            .stat-number {
                font-size: 2.5rem; font-weight: bold;
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .stat-label { color: #555; font-size: 1rem; font-weight: 600; margin-top: 10px; }
            .music-section {
                background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
                padding: 30px; border-radius: 20px; margin: 30px 0;
                box-shadow: 0 10px 25px rgba(252, 182, 159, 0.3);
            }
            .section-title {
                text-align: center; font-size: 2rem; font-weight: bold;
                color: #333; margin-bottom: 25px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            }
            .filter-container {
                background: rgba(255, 255, 255, 0.9); padding: 20px;
                border-radius: 15px; margin-bottom: 25px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .mood-group {
                background: rgba(255, 255, 255, 0.95); border-radius: 15px;
                padding: 20px; margin: 15px 0;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                border-left: 5px solid;
            }
            .mood-happy { border-left-color: #ffeb3b; }
            .mood-sad { border-left-color: #2196f3; }
            .mood-angry { border-left-color: #f44336; }
            .mood-calm { border-left-color: #4caf50; }
            .mood-energetic { border-left-color: #ff9800; }
            .mood-neutral { border-left-color: #9e9e9e; }
            .mood-surprise { border-left-color: #e91e63; }
            .mood-fear { border-left-color: #9c27b0; }
            .track-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
                padding: 20px; border-radius: 15px; margin: 15px 0;
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
                transition: transform 0.3s ease;
            }
            .track-card:hover { transform: translateY(-3px); }
        </style>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="profile-header">
            <div class="profile-avatar">👤</div>
            <h1 class="profile-name">{user['username']}</h1>
            <p class="profile-email">✉️ {user['email']}</p>
            <p class="profile-member-since">🎵 Member since {user['createdAt'].strftime('%B %Y')}</p>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("⬅️ Back to Music Discovery", use_container_width=True, key="back_to_app"):
                st.session_state.show_profile = False
                st.rerun()
        liked_tracks = self.get_user_liked_tracks(st.session_state.user_id)
        unique_moods = set(track.get('mood', 'Unknown') for track in liked_tracks)
        unique_genres = set(track.get('genre', 'Unknown') for track in liked_tracks)
        st.markdown('<div class="stats-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="stat-card"><div class="stat-number">💖<br>{len(liked_tracks)}</div><div class="stat-label">Loved Tracks</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="stat-card"><div class="stat-number">🎭<br>{len(unique_moods)}</div><div class="stat-label">Moods Explored</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="stat-card"><div class="stat-number">🎼<br>{len(unique_genres)}</div><div class="stat-label">Genres Enjoyed</div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="music-section">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">💖 Your Musical Journey</h2>', unsafe_allow_html=True)
        if not liked_tracks:
            st.info("🎵 Your music collection is empty! Start liking songs to build your library.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            mood_filter = st.selectbox("🎭 Filter by Mood:", ["All"] + sorted(list(unique_moods)), key="profile_mood_filter")
        with col2:
            sort_option = st.selectbox("📊 Sort by:", ["Most Recent", "Oldest First", "Artist A-Z", "Title A-Z"], key="profile_sort")
        st.markdown('</div>', unsafe_allow_html=True)
        filtered_tracks = liked_tracks
        if mood_filter != "All":
            filtered_tracks = [t for t in filtered_tracks if t.get('mood', '').lower() == mood_filter.lower()]
        if sort_option == "Most Recent":
            filtered_tracks = sorted(filtered_tracks, key=lambda x: x.get('likedAt', datetime.min), reverse=True)
        elif sort_option == "Oldest First":
            filtered_tracks = sorted(filtered_tracks, key=lambda x: x.get('likedAt', datetime.min))
        elif sort_option == "Artist A-Z":
            filtered_tracks = sorted(filtered_tracks, key=lambda x: x.get('artist', '').lower())
        elif sort_option == "Title A-Z":
            filtered_tracks = sorted(filtered_tracks, key=lambda x: x.get('title', '').lower())
        st.markdown(f"""<div style="text-align: center; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px; margin: 20px 0; font-weight: bold; color: #333;">🎵 Showing {len(filtered_tracks)} of {len(liked_tracks)} tracks</div>""", unsafe_allow_html=True)
        if mood_filter == "All":
            mood_groups = {}
            for track in filtered_tracks:
                mood = track.get('mood', 'Unknown')
                if mood not in mood_groups:
                    mood_groups[mood] = []
                mood_groups[mood].append(track)
            for mood, tracks in mood_groups.items():
                with st.expander(f"🎭 {mood.title()} Vibes ({len(tracks)} tracks)", expanded=len(mood_groups) == 1):
                    mood_class = f"mood-{mood.lower()}"
                    st.markdown(f'<div class="mood-group {mood_class}">', unsafe_allow_html=True)
                    self._display_liked_tracks_enhanced(tracks)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            with st.expander(f"🎭 {mood_filter.title()} Vibes ({len(filtered_tracks)} tracks)", expanded=True):
                mood_class = f"mood-{mood_filter.lower()}"
                st.markdown(f'<div class="mood-group {mood_class}">', unsafe_allow_html=True)
                self._display_liked_tracks_enhanced(filtered_tracks)
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _display_liked_tracks_enhanced(self, tracks):
        mood_colors = {
            'happy': 'linear-gradient(135deg, #FFD700, #FFA500)',
            'sad': 'linear-gradient(135deg, #4169E1, #1E90FF)',
            'angry': 'linear-gradient(135deg, #DC143C, #B22222)',
            'calm': 'linear-gradient(135deg, #32CD32, #228B22)',
            'energetic': 'linear-gradient(135deg, #FF4500, #FF6347)',
            'neutral': 'linear-gradient(135deg, #708090, #2F4F4F)',
            'surprise': 'linear-gradient(135deg, #FF1493, #C71585)',
            'fear': 'linear-gradient(135deg, #8A2BE2, #4B0082)'
        }
        for i, track in enumerate(tracks):
            mood = track.get('mood', 'neutral').lower()
            gradient = mood_colors.get(mood, mood_colors['neutral'])
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                st.markdown(f"""<div style="width: 80px; height: 80px; border-radius: 50%; background: {gradient}; display: flex; align-items: center; justify-content: center; font-size: 30px; color: white; font-weight: bold; box-shadow: 0 5px 15px rgba(0,0,0,0.3);">♪</div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="track-card"><h3 style="margin: 0 0 10px 0; color: #FFD700;">🎵 {track['title']}</h3><p style="margin: 5px 0; font-size: 1.1rem;">🎤 <strong>{track['artist']}</strong></p><p style="margin: 5px 0; opacity: 0.9;">🎼 {track['genre']} • 📀 {track.get('album', 'Unknown Album')}</p><p style="margin: 5px 0; opacity: 0.8;">🎭 {track['mood'].title()} mood</p><p style="margin: 10px 0 0 0; font-size: 0.9rem; opacity: 0.7;">💖 Added on {track.get('likedAt', datetime.now()).strftime('%B %d, %Y at %H:%M')}</p></div>""", unsafe_allow_html=True)

    def _display_input_methods(self):
        st.subheader("💬 Text Analysis")
        user_text = st.text_area("How are you feeling?", height=100, key="text_area_mood", placeholder="Tell me what's on your mind...")
        st.markdown("""
       <style>
       /* --- TEXT AREA --- */
       textarea[data-testid="stTextAreaTextarea"] {
            background: linear-gradient(135deg, #222244 56%, #2a1453 120%);
            color: #ffeafd !important;
            border: 2.5px solid #613aad;
            border-radius: 999px !important;
            -webkit-border-radius: 999px !important;
            box-shadow: 0 2px 17px 0 rgba(120,60,210,0.17), 0 0 0px 3px #a1e6ff33;
            padding: 1.15em 1.35em !important;
            font-size: 1.13em;
            font-family: 'Segoe UI', 'Montserrat', sans-serif;
            transition: all 0.25s cubic-bezier(.13,.6,.53,1.37), box-shadow 0.2s;
            outline: none !important;
            resize: none;
            min-height: 100px;
            -webkit-text-fill-color: #ffeafd !important; /* For Chrome/Safari */
        }

        textarea[data-testid="stTextAreaTextarea"]:focus {
            border: 2.5px solid #4f9cff;
            box-shadow: 0 0 0 2.5px #4f9cff88, 0 0 8px 2px #ff6ae2cc, 0 4px 26px 0 rgba(120,60,210,0.23);
            background: linear-gradient(135deg, #3d4b7f 60%, #662f8a 100%);
            color: #fff !important;
            -webkit-text-fill-color: #fff !important; /* For Chrome/Safari */
            transform: scale(1.018);
        }

        /* --- TEXT AREA LABEL --- */
        /* This is the corrected selector for the label */
        div[data-testid="stTextArea"] > label {
            font-size: 1.11rem !important;
            font-weight: bold;
            letter-spacing: 0.6px;
            color: #a1e6ff !important;
            background: linear-gradient(92deg, #4f9cff 10%, #e468ff 90%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

       /* --- PLACEHOLDER --- */
       textarea[data-testid="stTextAreaTextarea"]::placeholder {
            color: #d6a4fd !important;
            font-style: italic;
            letter-spacing: 1px;
            opacity: 0.93;
        }

        /* --- SPARKLE ANIMATION (Your original animation) --- */
        @keyframes sparkle {
            from { box-shadow: 0 2px 17px 0 #822cff22, 0 0 0px 6px #3820ea0c; }
            to   { box-shadow: 0 2px 22px 0 #f313b045, 0 0 0px 12px #ff80ff14; }
        }

        textarea[data-testid="stTextAreaTextarea"] {
            animation: sparkle 2.2s linear infinite alternate;
        }

        textarea[data-testid="stTextAreaTextarea"]:focus {
            animation: none;
        }
        </style>
        """, unsafe_allow_html=True)

        # Your button and logic remains the same
        if st.button("🔍 Analyze Text", use_container_width=True, key="analyze_text_btn"):
           if user_text.strip():
              # Try Gemini first for exact emotions from your list
               ext_mood, ext_conf = call_gemini_emotion_api(user_text)
        
               if ext_mood and ext_conf > 0.5:
            # Use Gemini result
                   mood, conf = ext_mood, ext_conf
               else:
            # Fallback to TextMoodAnalyzer
                   mood, conf = self.text_analyzer.predict_mood(user_text)
               st.session_state.current_mood, st.session_state.detection_confidence = mood, conf
               self.auto_generate_music(mood, conf)
               st.rerun()
           else:
              st.warning("Please enter some text!")
        
        st.divider()
        st.subheader("🎯 Manual Selection")
        manual_moods = ["happy", "sad", "angry", "calm", "energetic", "neutral", "surprise", "fear"]
        m = st.selectbox("Choose your mood:", manual_moods, key="manual_mood_select")
        if st.button("🎵 Generate Music", use_container_width=True, key="manual_generate_btn"):
            st.session_state.current_mood, st.session_state.detection_confidence = m, 1.0
            self.auto_generate_music(m, 1.0)
            st.rerun()

    def run(self):
        st.set_page_config(page_title="🎵 Emotion-Driven Music App", page_icon="🎵", layout="wide")
        st.markdown("""<style>.main > div {padding-top: 1rem; padding-bottom: 2rem;} .stButton > button {width: 100%;} .mood-detected {background: linear-gradient(45deg, #4CAF50, #45a049); color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);} .confidence-high {background: linear-gradient(45deg, #4CAF50, #45a049);} .confidence-medium {background: linear-gradient(45deg, #FF9800, #F57C00);} .confidence-low {background: linear-gradient(45deg, #f44336, #d32f2f);}</style>""", unsafe_allow_html=True)

        if st.session_state.user_id is None:
            st.title("🎵 Welcome to the Emotion-Driven Music App")
            st.info("👈 Please login or register using the sidebar to continue.")
            with st.sidebar:
                st.header("👤 Authentication")
                tab1, tab2 = st.tabs(["Login", "Register"])
                with tab1:
                    with st.form("login_form"):
                        email = st.text_input("📧 Email")
                        password = st.text_input("🔒 Password", type="password")
                        if st.form_submit_button("🚀 Login", use_container_width=True):
                            if email and password:
                                user = self.authenticate_user(email, password)
                                if user:
                                    st.session_state.user_id = str(user['_id'])
                                    st.rerun()
                                else: st.error("❌ Invalid credentials!")
                with tab2:
                    with st.form("register_form"):
                        username = st.text_input("👤 Username")
                        email = st.text_input("📧 Email")
                        password = st.text_input("🔒 Password", type="password")
                        if st.form_submit_button("📝 Register", use_container_width=True):
                            if username and email and password:
                                if self.register_user(username, email, password):
                                    st.success("✅ Registration successful! Please login.")
                                else: st.error("❌ Registration failed! Email may exist.")
            return

        if st.session_state.get('show_profile', False):
            self.show_profile_section()
            return

        title_col, menu_col = st.columns([0.8, 0.2])
        with title_col:
            st.title("🎵 Emotion-Driven Music Recommendation")
        with menu_col:
            user = self.db_handler.get_user_by_id(st.session_state.user_id)
            with st.popover(f"👤 {user['username']}", use_container_width=True):
                

                st.markdown(f"*{user['email']}*")
                st.divider()
                liked_tracks_count = len(self.get_user_liked_tracks(st.session_state.user_id))
                st.metric("💖 Liked Tracks", liked_tracks_count)
                if st.button("👤 View Profile", use_container_width=True):
                    st.session_state.show_profile = True
                    st.rerun()
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()
                    
                st.markdown("""
    <style>
      /* Find the first stButton in this area ("View Profile") only */
      div[data-testid="stButton"]:nth-of-type(1) button {
        background: linear-gradient(90deg,#6a11cb 0%,#2575fc 100%) !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 1.14rem !important;
        border-radius: 24px !important;
        padding: 10px 30px !important;
        box-shadow: 0 4px 15px rgba(70, 120, 220, 0.21) !important;
        border: none !important;
        margin-bottom: 0.5rem;
        transition: all 0.32s !important;
      }
      div[data-testid="stButton"]:nth-of-type(1) button:hover {
        background: linear-gradient(90deg,#2575fc 0%,#6a11cb 100%) !important;
        box-shadow: 0 6px 20px rgba(70, 120, 220, 0.33) !important;
      }
    </style>
""", unsafe_allow_html=True)
        st.divider()

        bridge_data = bridge("emotion-bridge", key="emotion_bridge_component")
        if bridge_data and bridge_data.get("type") == "final":
            event_id = bridge_data.get("eventId")
            if event_id and event_id != st.session_state.last_processed_event:
                st.session_state.last_processed_event = event_id
                mood = bridge_data.get("mood")
                confidence = bridge_data.get("confidence")
                if mood:
                    st.session_state.current_mood = mood
                    st.session_state.detection_confidence = confidence
                    self.auto_generate_music(mood, confidence)
                    st.rerun()

        left_col, right_col = st.columns([2.5, 2.5], gap="large")

        with left_col:
            st.header("🎭 Choose Your Mood")
            st.subheader("📹 Camera Detection")
            self.create_emotion_detector_component()
            if st.session_state.current_tracks:
                st.divider()
                self._display_input_methods()

        with right_col:
            st.header("🎵 Music Discovery")
            if not st.session_state.current_tracks:
                self._display_input_methods()
            else:
                if st.session_state.current_mood:
                    mood, conf = st.session_state.current_mood, st.session_state.detection_confidence
                    cls = "confidence-high" if conf > 0.7 else "confidence-medium" if conf > 0.4 else "confidence-low"
                    st.markdown(f'<div class="mood-detected {cls}">🎯 CURRENT MOOD: <strong>{mood.upper()}</strong> ({conf:.1%})</div>', unsafe_allow_html=True)
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("🔍 New Tracks", use_container_width=True, key="new_tracks_btn"):
                            st.session_state.current_tracks = self.fetch_jamendo_tracks(mood, 10)
                            st.session_state.recommendation_scores = []
                            st.rerun()
                    with btn_col2:
                        if st.button("🤖 AI Picks For You", use_container_width=True, key="ai_picks_btn"):
                            recs = self.rec_system.get_recommendations(st.session_state.user_id, mood, 8)
                            if recs:
                                st.session_state.current_tracks = [r['track'] for r in recs]
                                st.session_state.recommendation_scores = [r['similarity'] for r in recs]
                            else:
                                st.warning("Like some songs first to get personalized AI picks!")
                            st.rerun()
                    st.divider()
                for i, track in enumerate(st.session_state.current_tracks):
                    scores = st.session_state.get('recommendation_scores', [])
                    score = scores[i] if i < len(scores) else None
                    self.display_track_card(track, f"track_{track.get('id', i)}_{i}", score)

if __name__ == "__main__":
    app = EmotionMusicApp()
    app.run()