
from flask import Flask, json, jsonify, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask import Flask, render_template, request
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = 'fitmind_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'fitmind'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        age = request.form['age']
        gender = request.form['gender']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        else:
            cursor.execute('INSERT INTO users (fullname, username, password, email, age, gender) VALUES (%s, %s, %s, %s, %s, %s)', 
                           (fullname, username, password, email, age, gender))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('dashboard'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)


@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        username = session['username']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT age, gender FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            return render_template(
                'dashboard.html',
                username=username,
                age=user['age'],
                gender=user['gender']
            )
        else:
            return redirect(url_for('logout'))
    return redirect(url_for('login'))





@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/fitness', methods=['GET', 'POST'])
def fitness():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    bmi = None
    category = ""
    plan = ""
    message = ""

    if request.method == 'POST':
        try:
            height_cm = float(request.form['height'])
            weight_kg = float(request.form['weight'])
            goal = request.form['goal']

            if height_cm <= 0 or weight_kg <= 0:
                message = "Please enter valid height and weight."
            else:
                height_m = height_cm / 100
                bmi = round(weight_kg / (height_m ** 2), 2)

                if bmi < 18.5:
                    category = "Underweight"
                elif 18.5 <= bmi < 24.9:
                    category = "Normal weight"
                elif 25 <= bmi < 29.9:
                    category = "Overweight"
                else:
                    category = "Obese"

                if goal == 'lose':
                    plan = "Your goal is to lose weight. Follow a calorie deficit meal plan rich in fiber and protein. Exercise 5 days a week: 3 days of cardio (brisk walking, cycling) and 2 days of light strength training."
                elif goal == 'gain':
                    plan = "Your goal is to gain weight. Eat calorie-dense foods with plenty of protein and carbs. Include strength training 4–5 times a week (compound exercises like squats, deadlifts, and bench press)."
                elif goal == 'maintain':
                    plan = "Your goal is to maintain your weight. Maintain a balanced diet and exercise 3–4 days a week with a mix of cardio and strength routines."
                else:
                    message = "Please select a valid goal."

        except ValueError:
            message = "Please enter numeric values for height and weight."

    return render_template('fitness_plan.html', bmi=bmi, category=category, plan=plan, msg=message)

    

@app.route('/mental-health1', methods=['GET', 'POST'])
def mental_health():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    moods = []
    message = ""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if request.method == 'POST':
            mood = request.form.get('mood')
            note = request.form.get('note', '').strip()
            if not mood:
                message = "Please select your mood."
            else:
                cursor.execute(
                    "INSERT INTO mood_tracker (user_id, mood, note, date) VALUES (%s, %s, %s, NOW())",
                    (session['id'], mood, note)
                )
                mysql.connection.commit()
                message = "Mood entry recorded successfully."

        cursor.execute(
            "SELECT mood, note, DATE_FORMAT(date, '%%Y-%%m-%%d %%H:%%i') as date FROM mood_tracker WHERE user_id = %s ORDER BY date DESC",
            (session['id'],)
        )
        moods = cursor.fetchall()
    except Exception as e:
        print("Error:", e)
        message = "Something went wrong. Please try again later."

    return render_template('mental_health.html', moods=moods, msg=message)


# @app.route('/meditation')
# def meditation():
#     if 'loggedin' in session:
#         return render_template('meditation.html')
#     return redirect(url_for('login'))

# @app.route('/chatbot')
# def chatbot():
#     if 'loggedin' in session:
#         return render_template('chatbot.html')
#     return redirect(url_for('login'))

# Load model and encoders
model = joblib.load("fitness_rf_model.pkl")
encoders = {
    'Gender': joblib.load("encoder_Gender.pkl"),
    'Activity_Level': joblib.load("encoder_Activity_Level.pkl"),
    'Diet_Type': joblib.load("encoder_Diet_Type.pkl")
}
target_encoder = joblib.load("encoder_Target_Label.pkl")

# Mapping recommendation based on predicted class
plans = {
    "lose_Underweight": (
        "Yoga and light stretching",
        "High protein and calorie surplus with healthy fats",
        "https://youtu.be/CIxNJbit9BA?si=nDpoaTTSRXD4Naed",  # 30-min Gentle Yoga (Yoga With Adriene)
        "https://images.pexels.com/photos/1640770/pexels-photo-1640770.jpeg"  # Avocado toast with eggs
    ),
    "lose_Normal": (
        "30 mins cardio + 3x/week HIIT",
        "Calorie deficit with lean protein, veggies, whole grains",
        "https://youtu.be/-hSma-BRzoo?si=VAB9rTbEkqyz3quE",  # 30-min HIIT by Heather Robertson
        "https://images.pexels.com/photos/2097090/pexels-photo-2097090.jpeg"  # Grilled chicken with veggies
    ),
    "lose_Overweight": (
        "Daily brisk walk + cycling",
        "Low-carb, high-protein meals and portion control",
        "https://www.youtube.com/embed/3sEeVJEXTfY",  # 1-Mile Walk at Home
        "https://images.pexels.com/photos/1092730/pexels-photo-1092730.jpeg"  # Salmon with asparagus
    ),
    "lose_Obese": (
        "Low-impact aerobic + swimming",
        "Strict calorie control with fiber-rich meals",
        "https://www.youtube.com/embed/HwES4OSc9H8",  # Seated Aerobics for Beginners
        "https://images.pexels.com/photos/1211887/pexels-photo-1211887.jpeg"  # High-fiber bowl
    ),
    "gain_Underweight": (
        "Strength training 4x/week",
        "High calorie diet with protein shakes and nuts",
        "https://www.youtube.com/embed/ZrNXcyoy8-w",  # Beginner Strength Training
        "https://images.pexels.com/photos/842571/pexels-photo-842571.jpeg"  # Protein shake with nuts
    ),
    "gain_Normal": (
        "Weightlifting + core workouts",
        "Balanced protein-carb-fat with frequent meals",
        "https://www.youtube.com/embed/b7uDhHZ5qps",  # Full Body Dumbbell Workout
        "https://images.pexels.com/photos/629437/pexels-photo-629437.jpeg"  # Meal prep containers
    ),
    "gain_Overweight": (
        "Targeted resistance + low cardio",
        "Protein-rich but controlled portions",
        "https://www.youtube.com/embed/2tM1LFFxeKg",  # Resistance Band Workout
        "https://images.pexels.com/photos/1279330/pexels-photo-1279330.jpeg"  # Grilled chicken meal
    ),
    "gain_Obese": (
        "Supervised strength + low cardio",
        "Lean proteins and complex carbs in moderation",
        "https://www.youtube.com/embed/2wNoTsxlmDI",  # Chair Exercises
        "https://images.pexels.com/photos/1351238/pexels-photo-1351238.jpeg"  # Quinoa and vegetables
    ),
    "maintain_Underweight": (
        "Core exercises and flexibility",
        "Nutritious high-calorie meals",
        "https://www.youtube.com/embed/4pKly2JojMw",  # 10-min Core
        "https://images.pexels.com/photos/718742/pexels-photo-718742.jpeg"  # Nutrient bowl
    ),
    "maintain_Normal": (
        "3x/week full body workout",
        "Balanced diet with all macros",
        "https://youtu.be/MOrRRvSGIQc?si=ZxQRnlpJb2HGgG7a",  # Full Body Maintenance
        "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg"  # Balanced plate
    ),
    "maintain_Overweight": (
        "Low-intensity cardio",
        "Portion control with complex carbs",
        "https://www.youtube.com/embed/3SpPraOLJl4",  # Low Impact Cardio
        "https://images.pexels.com/photos/1099680/pexels-photo-1099680.jpeg"  # Portioned meal
    ),
    "maintain_Obese": (
        "Daily walking + water intake",
        "Vegetable-heavy with portion tracking",
        "https://www.youtube.com/embed/k_SoCdUlBvM",  # Beginner Walking Workout
        "https://images.pexels.com/photos/257816/pexels-photo-257816.jpeg"  # Vegetable assortment
    )
}


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    try:
        age = int(request.form['age'])
        gender = encoders['Gender'].transform([request.form['gender']])[0]
        height_cm = float(request.form['height_cm'])
        weight_kg = float(request.form['weight_kg'])
        bmi = weight_kg / ((height_cm / 100) ** 2)
        activity = encoders['Activity_Level'].transform([request.form['activity']])[0]
        diet = encoders['Diet_Type'].transform([request.form['diet']])[0]

        features = np.array([[age, gender, height_cm, weight_kg, bmi, activity, diet]])
        prediction = model.predict(features)
        label = target_encoder.inverse_transform(prediction)[0]

        exercise_plan, diet_plan, video_url, image_url  = plans.get(
            label,
            ("General fitness advice", "Balanced healthy eating", "", "")
        )

        return render_template(
            'fitness_form.html',
            prediction_text=f"Recommended Plan Category: {label}",
            bmi=round(bmi, 2),
            exercise_plan=exercise_plan,
            diet_plan=diet_plan,
            video_url=video_url,
            image_url =image_url 
        )
    except Exception as e:
        return render_template('fitness_form.html')

    
    # ===========================Mental Health Tracker================================================
# Load model and encoders
model1 = joblib.load("mental_rf_model.pkl")
le_gender = joblib.load("encoder_gender.pkl")
le_status = joblib.load("encoder_status.pkl")

# Treatment suggestions
treatments = {
    "Normal": "Maintain a healthy routine, regular exercise, and a balanced diet. Engage in social activities and self-care practices.",
    "Mild": "Practice mindfulness, journaling, regular exercise, and short-term counseling or therapy if needed.",
    "Moderate": "Seek support from a mental health professional. Consider cognitive-behavioral therapy (CBT) and guided meditation.",
    "Severe": "Consult a psychiatrist for evaluation. Combine psychotherapy (CBT, DBT) with medication as prescribed. Ensure strong family support and regular monitoring."
}

@app.route("/mentalhealth", methods=['GET', 'POST'])
def mentalhealth():
    try:
        age = int(request.form["age"])
        gender = le_gender.transform([request.form["gender"]])[0]
        phq9 = int(request.form["phq9"])
        gad7 = int(request.form["gad7"])
        depression = int(request.form["dass21_depression"])
        anxiety = int(request.form["dass21_anxiety"])
        stress = int(request.form["dass21_stress"])
        mood = int(request.form["mood_score"])

        features = np.array([[age, gender, phq9, gad7, depression, anxiety, stress, mood]])
        prediction = model1.predict(features)
        status = le_status.inverse_transform(prediction)[0]

        suggestion = treatments.get(status, "Consult a professional for personalized advice.")

        return render_template("mental_form.html", result=f"Predicted Mental Health Status: {status}", suggestion=suggestion)
    except Exception as e:
        return render_template("mental_form.html")

# ===================================================================

# Load model and encoders
meditation_model = joblib.load("meditation_rf_model.pkl")
le_gender = joblib.load("encoder_gender_meditation.pkl")
le_meditation = joblib.load("encoder_prev_meditation.pkl")
le_label = joblib.load("encoder_wellness_label.pkl")

# Suggestions and content mapping
content = {
    "Good": {
        "suggestion": "Maintain your routine with balanced sleep, regular breaks from screen time, and occasional meditation.",
        "video": "https://www.youtube.com/embed/inpok4MKVLM",
        "breathing": [
            "Belly breathing: Place your hand on your belly and breathe slowly.",
            "Try 3-minute mindful breathing sessions during breaks."
        ],
        "tips": [
            "Sleep 7–8 hours each night.",
            "Take 10-minute nature walks.",
            "Maintain a gratitude journal."
        ]
    },
    "Moderate": {
        "suggestion": "Reduce screen time, improve sleep habits, and begin regular guided meditation or journaling.",
        "video": "https://www.youtube.com/embed/ZToicYcHIOU",
        "breathing": [
            "Box breathing: Inhale 4s, hold 4s, exhale 4s, hold 4s.",
            "Try morning breathing exercises for energy."
        ],
        "tips": [
            "Do 15-minute yoga daily.",
            "Turn off devices 1 hour before bed.",
            "Use guided meditation apps like Headspace or Calm."
        ]
    },
    "Poor": {
        "suggestion": "Consult a wellness coach or therapist. Focus on improving daily habits and building strong routines.",
        "video": "https://www.youtube.com/embed/MIr3RsUWrdo",
        "breathing": [
            "4-7-8 Technique: Inhale 4s, hold 7s, exhale 8s.",
            "Breathe deeply when feeling overwhelmed."
        ],
        "tips": [
            "Avoid caffeine after noon.",
            "Create a calming bedtime routine.",
            "Engage in social support and connection."
        ]
    }
}


@app.route("/meditation", methods=['GET', 'POST'])
def meditation():
    try:
        age = int(request.form["age"])
        gender = le_gender.transform([request.form["gender"]])[0]
        sleep = float(request.form["sleep_hours"])
        screen = float(request.form["screen_time"])
        work_stress = int(request.form["work_stress"])
        family_stress = int(request.form["family_stress"])
        mindfulness = int(request.form["mindfulness_score"])
        prev_meditation = le_meditation.transform([request.form["prev_meditation"]])[0]

        features = np.array([[age, gender, sleep, screen, work_stress, family_stress, mindfulness, prev_meditation]])
        pred = meditation_model.predict(features)
        level = le_label.inverse_transform(pred)[0]

        plan = content.get(level, {})

        return render_template("meditation_form.html",
                               result=f"Predicted Wellness Level: {level}",
                               suggestion=plan.get("suggestion"),
                               video=plan.get("video"),
                               breathing=plan.get("breathing"),
                               tips=plan.get("tips"))
    except Exception as e:
        return render_template("meditation_form.html")


# Load ML components
chatbotmodel = joblib.load("chatbot_model.pkl")
vectorizer = joblib.load("chatbot_vectorizer.pkl")
label_encoder = joblib.load("chatbot_label_encoder.pkl")


@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    message = data.get("message", "").lower()

    # Predict tag using trained model
    x_input = vectorizer.transform([message])
    y_pred = chatbotmodel.predict(x_input)
    tag = label_encoder.inverse_transform(y_pred)[0]

    # Load intents JSON properly
    with open("chatbot_intents.json") as f:
        intents = json.load(f)

    # Match tag and return response
    for intent in intents["intents"]:
        if intent["tag"] == tag:
            reply = intent["responses"][0]
            break
    else:
        reply = "Sorry, I didn't understand that. Try asking something else."

    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
