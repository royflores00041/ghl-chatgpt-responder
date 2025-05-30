from flask import Flask, request, jsonify
import os
from openai import OpenAI
import sendgrid
from sendgrid.helpers.mail import Mail
import traceback

app = Flask(__name__)

# === API KEYS (set in Replit Secrets) ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# === Admin QA Email Recipients ===
ADMIN_EMAILS = [
    "roy.flores0226@gmail.com",
    "rsptaurus21@gmail.com",
    "georgemccleary@gmail.com"
]

# === Verified From Email in SendGrid ===
FROM_EMAIL = "support@titlefrauddefender.com"  # SendGrid-verified sender

# === Toggle sending directly to customer ===
SEND_TO_CUSTOMER = False

# === Initialize OpenAI client (v1.x) ===
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/', methods=['GET'])
def health_check():
    return "✅ Webhook Flask API is running. Use POST /webhook to receive data."

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json() or {}
        print("RAW PAYLOAD RECEIVED FROM GHL:", data)

        message_body = data.get("message", {}).get("body")
        contact_email = data.get("email")
        contact_name = data.get("full_name") or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
        first_name = data.get("first_name", "there")

        if not message_body or not contact_email:
            return jsonify({"error": "Missing message body or contact email"}), 400

        # Generate AI response
        ai_response = generate_ai_reply(message_body, first_name)

        # Build email content
        full_reply = f"""
=== AI Generated Reply ===

{ai_response}

--- Original Message Info ---
Name: {contact_name}
Email: {contact_email}
Message:
{message_body}
"""

        # Choose recipients
        recipients = [contact_email] if SEND_TO_CUSTOMER else ADMIN_EMAILS
        send_emails(recipients, f"[GHL Reply] AI Response for {contact_name}", full_reply)

        return jsonify({
            "status": "Reply processed",
            "sent_to": recipients
        }), 200

    except Exception:
        error_msg = traceback.format_exc()
        print("Exception occurred:\n", error_msg)
        return jsonify({"error": error_msg}), 500


def generate_ai_reply(user_msg, first_name):
    prompt = f"""
You are a professional assistant for Title Fraud Defender.

Title Fraud Defender monitors property title records, alerts homeowners to suspicious changes, and protects them from title fraud.

Write a professional, clear response to the following message. 
Start with: "Hi [FirstName],"
End with a warm, confident closing and include:

"If you have any other questions, feel free to reach out. We're here to help!"
And sign off with:
"Best regards,
The Title Fraud Defender Team"

Message:
\"\"\"
{user_msg}
\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for Title Fraud Defender."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=400
    )

    ai_text = response.choices[0].message.content.strip()
    return f"Hi {first_name},\n\n{ai_text}"


def send_emails(recipients, subject, content):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    for email in recipients:
        mail = Mail(
            from_email=FROM_EMAIL,
            to_emails=email,
            subject=subject,
            plain_text_content=content
        )
        resp = sg.send(mail)
        print(f"Email sent to {email}: {resp.status_code}")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
