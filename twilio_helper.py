from twilio.rest import Client
from config import Config
import os

def send_fall_alert(lat, long, contact_number, contact_name):
    account_sid = Config.TWILIO_ACCOUNT_SID
    auth_token = Config.TWILIO_AUTH_TOKEN
    from_number = Config.TWILIO_FROM_NUMBER
    
    if not account_sid or not auth_token or not from_number:
        print("Twilio credentials not found. Skipping alert.")
        return False

    client = Client(account_sid, auth_token)
    
    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{long}"
    message_body = f"URGENT: Fall Detected! Location: {maps_link}"

    try:
        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=contact_number
        )
        print(f"SMS sent to {contact_name}: {message.sid}")
        
        # Make Call (Optional, requires TwiML Bin or URL)
        # call = client.calls.create(...)
        
        return True
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False
