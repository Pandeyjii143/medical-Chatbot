import json
from fastapi import FastAPI, Form
from fastapi.responses import Response

app = FastAPI()
user_state = {}

# 📂 LOAD JSON FILES
with open("human_diseases.json") as f:
    human_db = json.load(f)

with open("agri_diseases.json") as f:
    agri_db = json.load(f)

with open("animal_diseases.json") as f:
    animal_db = json.load(f)

# 🌐 LANGUAGE DETECTION
def detect_language(msg):
    hindi_words = ["bukhar","dard","pet","khansi","ulti","kya","kaise","dast"]
    return "hindi" if any(w in msg for w in hindi_words) else "english"

# 📋 MAIN MENU
def main_menu(lang="english"):
    if lang == "hindi":
        return """👋 स्वागत है Smart Assistant में

1️⃣ मानव स्वास्थ्य
2️⃣ कृषि 🌾
3️⃣ पशु स्वास्थ्य 🐄

👉 या सीधे अपनी समस्या लिखें
"""
    return """👋 Smart Assistant

1️⃣ Human Health
2️⃣ Agriculture 🌾
3️⃣ Animal Health 🐄

👉 Or type your problem directly
"""

# 👤 HUMAN MENU
def human_disease_menu(lang="english"):
    if lang == "hindi":
        return """👤 बीमारी चुनें:

1️⃣ बुखार
2️⃣ सर्दी
3️⃣ सिर दर्द
4️⃣ पेट दर्द
5️⃣ डायबिटीज
6️⃣ ब्लड प्रेशर
7️⃣ खुद लिखें
"""
    return """👤 Select Disease:

1️⃣ Fever
2️⃣ Cold
3️⃣ Headache
4️⃣ Stomach Pain
5️⃣ Diabetes
6️⃣ High BP
7️⃣ Custom
"""

# 🌾 AGRI MENU
def agri_menu(lang="english"):
    if lang == "hindi":
        return """🌾 समस्या चुनें:

1️⃣ पत्ते पीले
2️⃣ पत्तों पर धब्बे
3️⃣ कीट हमला
4️⃣ धीमी वृद्धि
5️⃣ खुद लिखें
"""
    return """🌾 Select Issue:

1️⃣ Yellow Leaves
2️⃣ Leaf Spots
3️⃣ Pest Attack
4️⃣ Slow Growth
5️⃣ Custom
"""

# 🐄 ANIMAL MENU
def animal_menu(lang="english"):
    if lang == "hindi":
        return """🐄 समस्या चुनें:

1️⃣ बुखार
2️⃣ खाना नहीं खा रहा
3️⃣ कमजोरी
4️⃣ संक्रमण
5️⃣ खुद लिखें
"""
    return """🐄 Select Issue:

1️⃣ Fever
2️⃣ Not Eating
3️⃣ Weakness
4️⃣ Infection
5️⃣ Custom
"""

# 🧠 MATCH FUNCTION
def match_disease(msg, db):
    msg = msg.lower()
    best_match = None
    max_score = 0

    for disease in db.values():
        score = sum(1 for k in disease["keywords"] if k in msg)
        if score > max_score:
            max_score = score
            best_match = disease

    return best_match

# 📦 FORMAT FUNCTIONS
def format_human(d, lang):
    if lang == "hindi":
        return f"""
🩺 बीमारी: {d['disease']}

📌 कारण: संक्रमण या मौसम बदलने से

💊 दवा: {d['medicine']}
🥗 क्या खाएं: {d['food']}
🚫 क्या न खाएं: {d['avoid']}
⚠️ सावधानी: {d['precaution']}

👉 2-3 दिन में ठीक न हो तो डॉक्टर दिखाएं
"""
    return f"""
🩺 Disease: {d['disease']}

📌 Reason: Infection or weather change

💊 Medicine: {d['medicine']}
🥗 Eat: {d['food']}
🚫 Avoid: {d['avoid']}
⚠️ Precaution: {d['precaution']}

👉 Visit doctor if not improved
"""

def format_agri(d):
    return f"""
🌾 Disease: {d['disease']}

🧪 Solution: {d['solution']}
🚫 Avoid: {d['avoid']}
⚠️ Precaution: {d['precaution']}
"""

def format_animal(d):
    return f"""
🐄 Disease: {d['disease']}

💊 Treatment: {d['treatment']}
🥗 Food: {d['food']}
⚠️ Precaution: {d['precaution']}
"""

# 🚀 MAIN ENDPOINT
@app.post("/whatsapp")
async def whatsapp_bot(Body: str = Form(...), From: str = Form(...)):

    msg = Body.lower().strip()
    uid = From
    state = user_state.get(uid, "start")
    lang = detect_language(msg)

    # 🟢 START
    if msg in ["hi","hello","start","menu"]:
        user_state[uid] = "start"
        reply = main_menu(lang)

    # ❗ INVALID INPUT
    elif state == "start" and msg not in ["1","2","3"]:
        reply = (
            "❗ Please type 'hi' or choose 1,2,3"
            if lang=="english"
            else "❗ कृपया 'hi' लिखें या 1,2,3 चुनें"
        )

    # 🟢 MAIN STATE
    elif state == "start":

        if msg == "1":
            user_state[uid] = "human_menu"
            reply = human_disease_menu(lang)

        elif msg == "2":
            user_state[uid] = "agri_menu"
            reply = agri_menu(lang)

        elif msg == "3":
            user_state[uid] = "animal_menu"
            reply = animal_menu(lang)

    # 👤 HUMAN MENU
    elif state == "human_menu":

        mapping = {
            "1": "fever",
            "2": "cold",
            "3": "headache",
            "4": "stomach",
            "5": "diabetes",
            "6": "bp"
        }

        if msg in mapping:
            result = human_db.get(mapping[msg])
            reply = format_human(result, lang) if result else "❗ Data not found"
            user_state[uid] = "start"
            reply += "\n\n👉 menu"

        elif msg == "7":
            user_state[uid] = "human"
            reply = "✍️ Type symptoms" if lang=="english" else "✍️ लक्षण लिखें"

        else:
            reply = "❗ Select 1-7" if lang=="english" else "❗ 1-7 चुनें"

    # 🌾 AGRI MENU
    elif state == "agri_menu":

        mapping = {
            "1": "yellow_leaves",
            "2": "leaf_spot",
            "3": "pest_attack",
            "4": "growth"
        }

        if msg in mapping:
            result = agri_db.get(mapping[msg])
            reply = format_agri(result) if result else "❗ Data not found"
            user_state[uid] = "start"
            reply += "\n\n👉 menu"

        elif msg == "5":
            user_state[uid] = "agri"
            reply = "✍️ Describe problem"

        else:
            reply = "❗ Select 1-5"

    # 🐄 ANIMAL MENU
    elif state == "animal_menu":

        mapping = {
            "1": "animal_fever",
            "2": "digestive_issue",
            "3": "weakness",
            "4": "infection"
        }

        if msg in mapping:
            result = animal_db.get(mapping[msg])
            reply = format_animal(result) if result else "❗ Data not found"
            user_state[uid] = "start"
            reply += "\n\n👉 menu"

        elif msg == "5":
            user_state[uid] = "animal"
            reply = "✍️ Describe problem"

        else:
            reply = "❗ Select 1-5"

    # 👤 HUMAN INPUT
    elif state == "human":
        result = match_disease(msg, human_db)
        reply = format_human(result, lang) if result else "❗ Try simple symptoms"
        user_state[uid] = "start"
        reply += "\n\n👉 menu"

    # 🌾 AGRI INPUT
    elif state == "agri":
        result = match_disease(msg, agri_db)
        reply = format_agri(result) if result else "❗ Not detected"
        user_state[uid] = "start"
        reply += "\n\n👉 menu"

    # 🐄 ANIMAL INPUT
    elif state == "animal":
        result = match_disease(msg, animal_db)
        reply = format_animal(result) if result else "❗ Not detected"
        user_state[uid] = "start"
        reply += "\n\n👉 menu"

    else:
        reply = main_menu(lang)

    return Response(
        content=f"<Response><Message>{reply}</Message></Response>",
        media_type="application/xml"
    )