from __future__ import print_function
import os
import pickle
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
from config import Config

app = Flask(__name__)
CORS(app)  # Enable CORS for the entire application

def get_credentials():
    """Gets valid user credentials from storage or initiates OAuth flow to obtain new credentials."""
    creds = None
    if os.path.exists(Config.TOKEN_PICKLE):
        with open(Config.TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config({
                "web": {
                    "client_id": Config.GOOGLE_CLIENT_ID,
                    "client_secret": Config.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": ["http://localhost"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }, Config.SCOPES)
            creds = flow.run_local_server(port=0)
        with open(Config.TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
    return creds

@app.route('/create_appointment', methods=['POST'])
def create_appointment():
    data = request.json

    # Log the received data
    app.logger.info(f"Received data: {data}")

    event = {
        'summary': data.get('summary', 'No Title'),
        'location': data.get('location', ''),
        'description': data.get('description', ''),
        'start': {
            'dateTime': data['start']['dateTime'],
            'timeZone': data['start']['timeZone'],
        },
        'end': {
            'dateTime': data['end']['dateTime'],
            'timeZone': data['end']['timeZone'],
        },
        'recurrence': data.get('recurrence', []),
        'attendees': data.get('attendees', []),
        'reminders': data.get('reminders', {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        }),
    }

    try:
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId='primary', body=event).execute()
        app.logger.info(f"Event created: {event.get('htmlLink')}")
        return jsonify({'status': 'success', 'eventLink': event.get('htmlLink')}), 201
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/read_appointments', methods=['GET'])
def read_appointments():
    try:
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        app.logger.info(f"Retrieved events: {events}")
        return jsonify({'status': 'success', 'events': events}), 200
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete_appointment/<event_id>', methods=['DELETE'])
def delete_appointment(event_id):
    try:
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        app.logger.info(f"Event deleted: {event_id}")
        return jsonify({'status': 'success', 'message': 'Event deleted'}), 204
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
