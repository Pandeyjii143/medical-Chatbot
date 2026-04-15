import json
from fastapi import FastAPI, Form
from fastapi.responses import Response
import os
from dotenv import load_dotenv
from openai import OpenAI
import sqlite3

conn = sqlite3.connect("chat.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    symptoms TEXT,
    result TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usage (
    user TEXT,
    count INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS gpt_logs (
    user TEXT,
    query TEXT,
    response TEXT
)
""")

conn.commit()

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt(msg):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful medical assistant.

Give response in this format:
- Possible Condition
- Medicine (OTC)
- Food Advice
- Short Explanation

Keep it simple and safe."""
                },
                {"role": "user", "content": msg}
            ],
            max_tokens=150,  # 💰 control cost
            temperature=0.5
        )

        return response.choices[0].message.content

    except Exception as e:
        return "❗ AI service temporarily unavailable"

app = FastAPI()

# 🧠 MEMORY
user_state = {}
user_symptoms = {}

# 📂 LOAD JSON
with open("human_diseases.json") as f:
    human_db = json.load(f)

with open("agri_diseases.json") as f:
    agri_db = json.load(f)

with open("animal_diseases.json") as f:
    animal_db = json.load(f)

# 🌐 LANGUAGE
def detect_language(msg):
    hindi_words = ["bukhar","dard","pet","khansi","ulti"]
    return "hindi" if any(w in msg for w in hindi_words) else "english"

# 🚨 EMERGENCY
def check_emergency(msg):
    danger = ["chest pain","breathing","unconscious","severe"]
    return any(d in msg for d in danger)

# 📋 MENU
def main_menu(lang="english"):
    return """👋 Smart Assistant

1️⃣ Human Health 🧑‍⚕️
2️⃣ Agriculture 🌾
3️⃣ Animal Health 🐄

👉 Or type your problem directly
"""

# 🧠 MULTI-SYMPTOM MATCH
def match_disease(msg, db):
    words = msg.lower().split()

    best_match = None
    max_score = 0

    for disease in db.values():
        score = sum(1 for k in disease["keywords"] if any(k in w for w in words))

        if score > max_score:
            max_score = score
            best_match = disease

    return best_match, max_score

# 🧾 HUMAN RESPONSE (PARAGRAPH)
def format_human(d, confidence):

    return f"""
🩺 Based on your symptoms, you may have *{d['disease']}*

📊 Confidence: {confidence}%

This usually happens due to infection, weather change, or body weakness.

💊 Medicine: {d['medicine']}

🥗 Eat: {d['food']}
🚫 Avoid: {d['avoid']}

⚠️ Care Tips:
{d['precaution']}

⏳ Recovery time: 2–5 days

🚨 If symptoms worsen, consult doctor immediately

👉 Type 'menu' to restart
"""

# 🌾 AGRI
def format_agri(d):
    return f"""
🌾 Your crop may have *{d['disease']}*

📌 Cause: Environmental or fungal issue

🧪 Solution: {d['solution']}
🚫 Avoid: {d['avoid']}
⚠️ Care: {d['precaution']}

👉 Type 'menu'
"""

# 🐄 ANIMAL
def format_animal(d):
    return f"""
🐄 Your animal may have *{d['disease']}*

💊 Treatment: {d['treatment']}
🥗 Feed: {d['food']}
⚠️ Care: {d['precaution']}

👉 Type 'menu'
"""

@app.get("/")
def home():
    return {"status": "running"}

# 🚀 MAIN
@app.post("/whatsapp")
async def whatsapp_bot(Body: str = Form(...), From: str = Form(...)):

    msg = Body.lower().strip()
    uid = From
    state = user_state.get(uid, "start")

    # 🚨 emergency
    if check_emergency(msg):
        return Response(
            content="<Response><Message>🚨 Please visit hospital immediately</Message></Response>",
            media_type="application/xml"
        )

    # 🟢 START
    if msg in ["hi","hello","start","menu"]:
        user_state[uid] = "start"
        user_symptoms[uid] = []
        reply = main_menu()

    # 🟢 MAIN
    elif state == "start":

        if msg == "1":
            user_state[uid] = "human"
            user_symptoms[uid] = []
            reply = "🧑‍⚕️ Tell your symptoms (you can write multiple like: fever headache body pain)"

        elif msg == "2":
            user_state[uid] = "agri"
            reply = "🌾 Describe crop problem"

        elif msg == "3":
            user_state[uid] = "animal"
            reply = "🐄 Describe animal issue"

        else:
            reply = "❗ Please choose 1,2,3 or type 'menu'"

    # 👤 HUMAN FLOW (CONVERSATION)
    elif state == "human":

        user_symptoms.setdefault(uid, [])
        user_symptoms[uid].append(msg)

        # ask more
        if len(user_symptoms[uid]) < 2:
            reply = "🤔 Any other symptoms? (or type 'no')"

        elif msg == "no":
            combined = " ".join(user_symptoms[uid])

            result, score = match_disease(combined, human_db)

            if result:
                confidence = min(100, score * 30)
                reply = format_human(result, confidence)
            else:
                reply = "❗ Could not detect properly"

            user_state[uid] = "start"

        else:
            reply = "🤔 Add more symptoms or type 'no'"

    # 🌾 AGRI
    elif state == "agri":
        result, _ = match_disease(msg, agri_db)
        reply = format_agri(result) if result else "❗ Not detected"
        user_state[uid] = "start"

    # 🐄 ANIMAL
    elif state == "animal":
        result, _ = match_disease(msg, animal_db)
        reply = format_animal(result) if result else "❗ Not detected"
        user_state[uid] = "start"

    else:
        reply = main_menu()

    return Response(
        content=f"<Response><Message>{reply}</Message></Response>",
        media_type="application/xml"
    )