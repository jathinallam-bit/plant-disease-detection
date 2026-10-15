import os
import requests
from flask_oauthlib.client import OAuth
from flask import session


def init_oauth(app):
    """Initialize Google OAuth with credentials from environment variables."""
    oauth = OAuth(app)

    client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    if not client_id or not client_secret:
        print("[WARN] Google OAuth credentials missing — Google login disabled")
        return None

    google = oauth.remote_app(
        'google',
        consumer_key=client_id,
        consumer_secret=client_secret,
        request_token_params={'scope': 'email profile'},
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
    )

    @google.tokengetter
    def get_google_oauth_token():
        return session.get('google_oauth_token')

    return google


def get_google_user_info(google_token):
    """Fetch user info from Google using an access token."""
    headers = {'Authorization': f'Bearer {google_token}'}
    response = requests.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None