# config.py
import os

class Config:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    CLIENT_SECRET_FILE = 'credentials.json'
    TOKEN_PICKLE = 'token.pickle'
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
