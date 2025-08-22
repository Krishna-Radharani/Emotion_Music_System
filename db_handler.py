import streamlit as st
import pymongo
from bson import ObjectId
from datetime import datetime
import bcrypt

MONGO_URI = st.secrets["MONGO_URI"]

class MongoDBHandler:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client['emotion_music_composer']
        self.users_collection = self.db['users']

    def create_user(self, username, email, password):
        try:
            if self.users_collection.find_one({'email': email}):
                return None
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user_data = {
                'username': username,
                'email': email,
                'password': hashed_password,
                'likedTracks': [],
                'createdAt': datetime.now(),
                'lastLogin': None
            }
            result = self.users_collection.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def authenticate_user(self, email, password):
        try:
            user = self.users_collection.find_one({'email': email})
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                self.users_collection.update_one(
                    {'_id': user['_id']},
                    {'$set': {'lastLogin': datetime.now()}}
                )
                return user
            return None
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None

    def get_user_by_id(self, user_id):
        try:
            return self.users_collection.find_one({'_id': ObjectId(user_id)})
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def add_liked_track(self, user_id, track):
        try:
            track_id = track.get('id') or track.get('trackId')
            exists = self.users_collection.find_one({
                '_id': ObjectId(user_id),
                'likedTracks.trackId': track_id
            })
            if exists:
                return False
            track_data = {
                'trackId': track_id,
                'title': track['title'],
                'artist': track['artist'],
                'genre': track['genre'],
                'mood': track['mood'],
                'album': track.get('album', 'Unknown'),
                'duration': track.get('duration', 0),
                'likedAt': datetime.now()
            }
            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$push': {'likedTracks': track_data}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding liked track: {e}")
            return False

    def get_user_liked_tracks(self, user_id, mood=None):
        try:
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                return []
            liked_tracks = user.get('likedTracks', [])
            if mood:
                liked_tracks = [t for t in liked_tracks if t.get('mood') == mood]
            return liked_tracks
        except Exception as e:
            print(f"Error getting liked tracks: {e}")
            return []

    def remove_liked_track(self, user_id, track_id):
        try:
            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$pull': {'likedTracks': {'trackId': track_id}}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error removing liked track: {e}")
            return False

    def get_user_stats(self, user_id):
        try:
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                return {}
            liked_tracks = user.get('likedTracks', [])
            mood_counts = {}
            genre_counts = {}
            total_duration = 0
            for track in liked_tracks:
                mood = track.get('mood', 'unknown')
                genre = track.get('genre', 'Unknown')
                duration = track.get('duration', 0)
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
                total_duration += duration
            return {
                'total_tracks': len(liked_tracks),
                'total_duration_minutes': total_duration // 60,
                'mood_distribution': mood_counts,
                'genre_distribution': genre_counts,
                'account_created': user.get('createdAt'),
                'last_login': user.get('lastLogin')
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {}