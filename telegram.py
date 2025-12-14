from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Jagrav Portfolio Contact API", version="1.0.0")

# CORS - Allow your Netlify portfolio
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jagravportfolio.netlify.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEB3FORMS_ACCESS_KEY = os.getenv("WEB3FORMS_ACCESS_KEY")

class ContactForm(BaseModel):
    name: str
    email: str
    subject: str
    message: str

@app.get("/")
def home():
    return {
        "service": "Jagrav Portfolio Contact API",
        "status": "active",
        "frontend": "https://jagravportfolio.netlify.app",
        "endpoint": "/api/contact (POST)"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
        "web3forms_configured": bool(WEB3FORMS_ACCESS_KEY)
    }

def send_telegram(form_data: ContactForm):
    """Send Telegram notification"""
    message = f"""
📨 *New Message from Portfolio*

👤 *Name:* {form_data.name}
📧 *Email:* {form_data.email}
🎯 *Subject:* {form_data.subject}
📝 *Message:*
{form_data.message}
"""
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def send_web3forms(form_data: ContactForm):
    """Send to Web3Forms for email"""
    try:
        response = requests.post(
            "https://api.web3forms.com/submit",
            data={
                "access_key": WEB3FORMS_ACCESS_KEY,
                "name": form_data.name,
                "email": form_data.email,
                "subject": form_data.subject,
                "message": form_data.message,
                "from_name": "Portfolio Contact Form"
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

@app.post("/api/contact")
async def contact(form: ContactForm):
    try:
        # Validate
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            raise HTTPException(500, "Telegram not configured")
        if not WEB3FORMS_ACCESS_KEY:
            raise HTTPException(500, "Email service not configured")
        
        # Send notifications
        telegram_sent = send_telegram(form)
        email_sent = send_web3forms(form)
        
        return {
            "success": True,
            "message": "Thank you! Your message has been sent.",
            "notifications": {
                "telegram": "sent" if telegram_sent else "failed",
                "email": "sent" if email_sent else "failed"
            }
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)