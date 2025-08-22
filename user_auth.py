class UserAuth:
    def __init__(self, db_handler):
        self.db = db_handler

    def register(self, username, email, password):
        if not username or not email or not password:
            return False
        if '@' not in email or '.' not in email:
            return False
        if len(password) < 6:
            return False
        user_id = self.db.create_user(username, email, password)
        return user_id is not None

    def login(self, email, password):
        if not email or not password:
            return None
        return self.db.authenticate_user(email, password)

    def get_user_profile(self, user_id):
        user = self.db.get_user_by_id(user_id)
        if not user:
            return None
        return {
            'id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'created_at': user.get('createdAt'),
            'last_login': user.get('lastLogin'),
            'liked_tracks_count': len(user.get('likedTracks', []))
        }