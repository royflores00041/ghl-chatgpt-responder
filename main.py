from flask import Flask, request, jsonify
import openai
import os
import requests

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')
GHL_CLIENT_ID = os.getenv('GHL_CLIENT_ID')
GHL_CLIENT_SECRET = os.getenv('GHL_CLIENT_SECRET')
GHL_BASE_URL = 'https://services.leadconnectorhq.com'

# Get OAuth access token from GHL
def get_ghl_access_token():
    token_url = f"{GHL_BASE_URL}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": GHL_CLIENT_ID,
        "client_secret": GHL_CLIENT_SECRET
    }
    response = requests.post(token_url, json=payload)
    response.raise_for_status()
    return response.json().get("access_token")

# Generate AI email reply
def generate_ai_response(email_body):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Reply professionally to this email: {email_body}"}
        ]
    )
    return response['choices'][0]['message']['content']

@app.route("/", methods=["GET"])
def home():
    return "GHL ChatGPT Auto-Responder is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook data received:", data)

    contact_id = data.get('contact', {}).get('id')
    email_body = data.get('body', '')

    if not contact_id or not email_body:
        return jsonify({'error': 'Missing contact or body'}), 400

    try:
        ai_reply = generate_ai_response(email_body)
        access_token = get_ghl_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        email_payload = {
            "contactId": contact_id,
            "subject": "RE: Your message",
            "body": ai_reply
        }

        email_url = f"{GHL_BASE_URL}/v2/emails/"
        response = requests.post(email_url, headers=headers, json=email_payload)
        response.raise_for_status()

        return jsonify({"status": "sent", "ghl_response": response.json()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)