# oauth.py
import os
import json
from flask import Flask, redirect, url_for, session, request, flash
from flask_oauthlib.client import OAuth
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============ GET CREDENTIALS FROM .env ============
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/google/callback')
# ================================================

def init_oauth(app):
    """Initialize Google OAuth"""
    oauth = OAuth(app)
    
    google = oauth.remote_app(
        'google',
        consumer_key=GOOGLE_CLIENT_ID,
        consumer_secret=GOOGLE_CLIENT_SECRET,
        request_token_params={
            'scope': 'email profile',
        },
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
    )
    
    # Token getter for Flask-OAuthlib
    @google.tokengetter
    def get_google_oauth_token():
        return session.get('google_oauth_token')
    
    return google

def get_google_user_info(google_token):
    """Get user info from Google"""
    headers = {'Authorization': f'Bearer {google_token}'}
    response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
    
    if response.status_code == 200:
        return response.json()
    return None