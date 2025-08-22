import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

class MusicRecommendationSystem:
    def __init__(self, db_handler, jamendo_api):
        self.db = db_handler
        self.jamendo_api = jamendo_api
        self.all_genres = [
            'pop', 'rock', 'electronic', 'indie', 'trance', 'rap', 'hip-hop', 'metal', 
            'jazz', 'ambient', 'classical', 'folk', 'reggae', 'funk', 'blues', 
            'dance', 'country', 'alternative', 'punk', 'soul', 'r&b', 'Unknown'
        ]
        self.all_moods = [
            'happy', 'sad', 'angry', 'calm', 'energetic', 'neutral', 
            'surprise', 'romantic', 'melancholy', 'excited', 'peaceful'
        ]

    def vectorize_track(self, track):
        try:
            genre = track.get('genre', 'Unknown').lower()
            genre_vector = [1 if genre == g.lower() else 0 for g in self.all_genres]
            mood = track.get('mood', 'neutral').lower()
            mood_vector = [1 if mood == m.lower() else 0 for m in self.all_moods]
            artist = track.get('artist', 'Unknown').lower()
            artist_hash = abs(hash(artist)) % 50
            artist_vector = [1 if i == artist_hash else 0 for i in range(50)]
            combined_vector = genre_vector + mood_vector + artist_vector
            return np.array(combined_vector, dtype=np.float32)
        except Exception as e:
            print(f"Error vectorizing track: {e}")
            return np.zeros(len(self.all_genres) + len(self.all_moods) + 50, dtype=np.float32)

    def get_user_preference_vector(self, user_id, mood):
        try:
            liked_tracks = self.db.get_user_liked_tracks(user_id, mood)
            if not liked_tracks:
                return None
            vectors = []
            for track in liked_tracks:
                vector = self.vectorize_track(track)
                vectors.append(vector)
            if not vectors:
                return None
            user_vector = np.mean(vectors, axis=0)
            return user_vector
        except Exception as e:
            print(f"Error getting user preference vector: {e}")
            return None

    def get_recommendations(self, user_id, mood, top_n=10):
        try:
            user_vector = self.get_user_preference_vector(user_id, mood)
            if user_vector is None:
                print(f"No user preferences found for mood: {mood}")
                return []
            candidate_tracks = self.jamendo_api.fetch_tracks_by_mood(mood, limit=50)
            if not candidate_tracks:
                print("No candidate tracks found")
                return []
            liked_tracks = self.db.get_user_liked_tracks(user_id)
            liked_track_ids = set(track.get('trackId') for track in liked_tracks)
            similarities = []
            for track in candidate_tracks:
                if track['id'] in liked_track_ids:
                    continue
                track_vector = self.vectorize_track(track)
                similarity = cosine_similarity(
                    user_vector.reshape(1, -1),
                    track_vector.reshape(1, -1)
                )[0][0]
                similarities.append({
                    'track': track,
                    'similarity': float(similarity)
                })
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            recommendations = similarities[:top_n]
            print(f"Generated {len(recommendations)} recommendations for mood: {mood}")
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []

    def get_diversity_recommendations(self, user_id, mood, top_n=10):
        try:
            recommendations = self.get_recommendations(user_id, mood, top_n * 2)
            if not recommendations:
                return []
            genre_groups = {}
            for rec in recommendations:
                genre = rec['track'].get('genre', 'Unknown')
                if genre not in genre_groups:
                    genre_groups[genre] = []
                genre_groups[genre].append(rec)
            diverse_recs = []
            for genre, recs in genre_groups.items():
                diverse_recs.extend(recs[:2])
                if len(diverse_recs) >= top_n:
                    break
            diverse_recs.sort(key=lambda x: x['similarity'], reverse=True)
            return diverse_recs[:top_n]
        except Exception as e:
            print(f"Error generating diverse recommendations: {e}")
            return []

    def get_user_music_insights(self, user_id):
        try:
            liked_tracks = self.db.get_user_liked_tracks(user_id)
            if not liked_tracks:
                return {}
            moods = [track.get('mood', 'unknown') for track in liked_tracks]
            genres = [track.get('genre', 'Unknown') for track in liked_tracks]
            artists = [track.get('artist', 'Unknown') for track in liked_tracks]
            mood_counts = Counter(moods)
            genre_counts = Counter(genres)
            artist_counts = Counter(artists)
            return {
                'total_tracks': len(liked_tracks),
                'favorite_moods': dict(mood_counts.most_common(5)),
                'favorite_genres': dict(genre_counts.most_common(5)),
                'favorite_artists': dict(artist_counts.most_common(5)),
                'mood_diversity': len(mood_counts),
                'genre_diversity': len(genre_counts)
            }
        except Exception as e:
            print(f"Error getting user insights: {e}")
            return {}