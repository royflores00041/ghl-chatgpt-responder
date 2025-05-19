from flask import Flask, request, jsonify
import openai
import os
import requests

app = Flask(__name__)

# Load your API keys from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')
GHL_API_KEY = os.getenv('GHL_API_KEY')
GHL_BASE_URL = 'https://rest.gohighlevel.com/v1'

# Set this to your email for testing AI replies
FORWARD_TO_EMAIL = ["roy.flores0226@gmail.com", "rsptaurus21@gmail.com", "georgemccleary@gmail.com", "jai.labesores@gmail.com"]  # 👈 Replace with your testing email

# Function to generate reply from ChatGPT
def generate_ai_response(email_body):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Reply professionally to this email: {email_body}"}
        ]
    )
    return response['choices'][0]['message']['content']

# Health check endpoint
@app.route("/", methods=["GET"])
def home():
    return "GHL ChatGPT Auto-Responder is running!"

# Webhook endpoint triggered by GHL
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook data received:", data)

    email_body = data.get('body', '')
    contact_info = data.get('contact', {})
    contact_name = contact_info.get('name', 'Unknown Contact')
    original_sender_email = contact_info.get('email', 'unknown@example.com')

    if not email_body:
        return jsonify({'error': 'Missing email body'}), 400

    try:
        ai_reply = generate_ai_response(email_body)

        headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json"
        }

        # Construct detailed body with sender info
        full_message = f"""
Original Sender: {contact_name} <{original_sender_email}>

--- Original Message ---
{email_body}

--- AI Suggested Reply ---
{ai_reply}
"""

        email_payload = {
            "toAddress": FORWARD_TO_EMAIL,
            "subject": f"AI Reply for: {contact_name} ({original_sender_email})",
            "body": full_message.strip()
        }

        response = requests.post(f"{GHL_BASE_URL}/emails/send", headers=headers, json=email_payload)
        return jsonify({"status": "sent to fixed address", "ghl_response": response.json()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
