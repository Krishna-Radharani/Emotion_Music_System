import streamlit as st
import requests

JAMENDO_CLIENT_ID = st.secrets["JAMENDO_CLIENT_ID"]

class JamendoAPI:
    def __init__(self):
        self.client_id = JAMENDO_CLIENT_ID
        self.base_url = "https://api.jamendo.com/v3.0"
        self.tracks_endpoint = f"{self.base_url}/tracks/"
        self.albums_endpoint = f"{self.base_url}/albums/"

    def fetch_tracks_by_mood(self, mood, limit=100):
        params = {
            'client_id': self.client_id,
            'format': 'json',
            'limit': limit,
            'fuzzytags': mood,
            'include': 'musicinfo',
            'audioformat': 'mp31'
        }
        try:
            response = requests.get(self.tracks_endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            tracks = []
            for track in data.get('results', []):
                processed_track = self._process_track_data(track, mood)
                if processed_track:
                    tracks.append(processed_track)
            return tracks
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            return []
        except Exception as e:
            print(f"Error processing tracks: {e}")
            return []

    def get_track_details(self, track_id):
        if not track_id:
            return None
        params = {
            'client_id': self.client_id,
            'format': 'json',
            'id': track_id,
            'include': 'musicinfo'
        }
        try:
            response = requests.get(self.tracks_endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('results'):
                return self._process_track_data(data['results'][0])
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting track details: {e}")
            return None

    def search_tracks(self, query, limit=20):
        params = {
            'client_id': self.client_id,
            'format': 'json',
            'limit': limit,
            'search': query,
            'include': 'musicinfo',
            'audioformat': 'mp31'
        }
        try:
            response = requests.get(self.tracks_endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            tracks = []
            for track in data.get('results', []):
                processed_track = self._process_track_data(track)
                if processed_track:
                    tracks.append(processed_track)
            return tracks
        except requests.exceptions.RequestException as e:
            print(f"Search error: {e}")
            return []

    def _process_track_data(self, track, default_mood=None):
        try:
            musicinfo = track.get('musicinfo', {})
            tags_data = musicinfo.get('tags', {})
            genres = tags_data.get('genres', [])
            vartags = tags_data.get('vartags', [])
            speed = tags_data.get('speed', [])
            instruments = tags_data.get('instruments', [])
            genre = 'Unknown'
            if genres:
                genre = genres[0]
            elif vartags:
                genre = vartags
            elif track.get('tags'):
                genre = track['tags'] if track['tags'] else 'Unknown'
            album_image = track.get('album_image', '')
            if album_image:
                album_image = album_image.replace('1.100', '1.400')
            processed_track = {
                'id': track.get('id'),
                'title': track.get('name', 'Unknown Title'),
                'artist': track.get('artist_name', 'Unknown Artist'),
                'genre': genre,
                'mood': default_mood or self._infer_mood_from_tags(vartags + genres),
                'audio_url': track.get('audio', ''),
                'album_image': album_image,
                'album': track.get('album_name', 'Unknown Album'),
                'duration': track.get('duration', 0),
                'releasedate': track.get('releasedate', ''),
                'license': track.get('license_ccurl', ''),
                'tags': track.get('tags', []),
                'vartags': vartags,
                'genres': genres,
                'speed': speed,
                'instruments': instruments,
                'artist_id': track.get('artist_id', ''),
                'album_id': track.get('album_id', '')
            }
            return processed_track
        except Exception as e:
            print(f"Error processing track data: {e}")
            return None

    def _infer_mood_from_tags(self, tags):
        mood_mapping = {
            'happy': ['happy', 'upbeat', 'cheerful', 'joyful', 'positive', 'uplifting'],
            'sad': ['sad', 'melancholy', 'depressing', 'somber', 'sorrowful', 'melancholic'],
            'angry': ['angry', 'aggressive', 'intense', 'rage', 'furious', 'hostile'],
            'calm': ['calm', 'peaceful', 'relaxing', 'serene', 'tranquil', 'soothing'],
            'energetic': ['energetic', 'dynamic', 'powerful', 'fast', 'intense', 'driving'],
            'neutral': ['neutral', 'moderate', 'balanced']
        }
        tags_lower = [tag.lower() for tag in tags]
        for mood, keywords in mood_mapping.items():
            for keyword in keywords:
                if any(keyword in tag for tag in tags_lower):
                    return mood
        return 'neutral'

    def get_popular_tracks(self, limit=50):
        params = {
            'client_id': self.client_id,
            'format': 'json',
            'limit': limit,
            'order': 'popularity_total',
            'include': 'musicinfo',
            'audioformat': 'mp31'
        }
        try:
            response = requests.get(self.tracks_endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            tracks = []
            for track in data.get('results', []):
                processed_track = self._process_track_data(track)
                if processed_track:
                    tracks.append(processed_track)
            return tracks
        except requests.exceptions.RequestException as e:
            print(f"Error getting popular tracks: {e}")
            return []