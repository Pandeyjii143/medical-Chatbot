import json
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
import sqlite3

app = FastAPI()

# 🗄️ DATABASE
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
conn.commit()

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

# 🚨 EMERGENCY
def check_emergency(msg):
    danger = ["chest pain","breathing","unconscious","severe"]
    return any(d in msg for d in danger)

# 📋 MENU
def main_menu():
    return """👋 Smart Assistant

1️⃣ Human Health 🧑‍⚕️
2️⃣ Agriculture 🌾
3️⃣ Animal Health 🐄

👉 Or type your problem directly
"""

# 🧠 MATCH
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

# 🧾 HUMAN RESPONSE
def format_human(d, confidence):
    return f"""🩺 Based on your symptoms, you may have *{d['disease']}*

📊 Confidence: {confidence}%

💊 Medicine: {d['medicine']}
🥗 Eat: {d['food']}
🚫 Avoid: {d['avoid']}

⚠️ Care:
{d['precaution']}

⏳ Recovery: 2–5 days

👉 Type 'menu' to restart"""

# 🌾 AGRI
def format_agri(d):
    return f"""🌾 Disease: {d['disease']}

🧪 Solution: {d['solution']}
🚫 Avoid: {d['avoid']}
⚠️ Care: {d['precaution']}

👉 menu"""

# 🐄 ANIMAL
def format_animal(d):
    return f"""🐄 Disease: {d['disease']}

💊 Treatment: {d['treatment']}
🥗 Food: {d['food']}
⚠️ Care: {d['precaution']}

👉 menu"""

@app.get("/")
def home():
    return {"status": "running"}

# 🚀 MAIN
@app.post("/whatsapp")
async def whatsapp_bot(Body: str = Form(...), From: str = Form(...)):
    
    print("🔥 MESSAGE RECEIVED:", Body)

    msg = Body.lower().strip()
    uid = From
    state = user_state.get(uid, "start")

    # 🚨 EMERGENCY
    if check_emergency(msg):
        return PlainTextResponse(
            content="""<?xml version="1.0" encoding="UTF-8"?><Response><Message>🚨 Please visit hospital immediately</Message></Response>""",
            media_type="application/xml"
        )

    # 🟢 START
    if msg in ["hi","hello","start","menu"]:
        user_state[uid] = "start"
        user_symptoms[uid] = []
        reply = main_menu()

    # 🟢 MAIN MENU
    elif state == "start":

        if msg == "1":
            user_state[uid] = "human"
            user_symptoms[uid] = []
            reply = "🧑‍⚕️ Tell your symptoms (e.g. fever headache body pain)"

        elif msg == "2":
            user_state[uid] = "agri"
            reply = "🌾 Describe crop problem"

        elif msg == "3":
            user_state[uid] = "animal"
            reply = "🐄 Describe animal issue"

        else:
            reply = "❗ Please choose 1,2,3 or type 'menu'"

    # 👤 HUMAN FLOW
    elif state == "human":

        user_symptoms.setdefault(uid, [])
        user_symptoms[uid].append(msg)

        if len(user_symptoms[uid]) < 2:
            reply = "🤔 Any other symptoms? (type 'no')"

        elif msg == "no":
            combined = " ".join(user_symptoms[uid])

            result, score = match_disease(combined, human_db)

            if result:
                confidence = min(100, score * 30)
                reply = format_human(result, confidence)

                # 💾 SAVE HISTORY
                cursor.execute(
                    "INSERT INTO history (user, symptoms, result) VALUES (?, ?, ?)",
                    (uid, combined, result["disease"])
                )
                conn.commit()

            else:
                reply = "❗ Could not detect. Try simple symptoms"

            user_state[uid] = "start"

        else:
            reply = "➕ Add more symptoms or type 'no'"

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

    # ✅ FINAL TWILIO RESPONSE (FIXED)
    return PlainTextResponse(
        content=f"""<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply}</Message></Response>""",
        media_type="application/xml"
    )