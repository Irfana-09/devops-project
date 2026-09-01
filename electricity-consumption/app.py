from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
import re
import smtplib
import random
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from werkzeug.utils import secure_filename
from email.message import EmailMessage

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALERT_THRESHOLD = 2000  # ₹ threshold for sending alerts

# If tesseract is not in your PATH, uncomment and set the path:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def smart_suggestions(appliances, monthly_bill):
    tips = []

    if monthly_bill > 2000:
        tips.append("⚠ Reduce AC usage")
        tips.append("💡 Switch to LED bulbs")
        tips.append("🔌 Turn off standby devices")
    elif monthly_bill > 1000:
        tips.append("💡 Limit high power appliances usage")
        tips.append("🔌 Unplug unused devices")
    else:
        tips.append("✅ Your usage is efficient")
        tips.append("💡 Keep monitoring usage")

    # appliance-based suggestion (IMPORTANT UPGRADE)
    if appliances:
        max_app = max(appliances, key=lambda x: x[2])
        tips.append(f"⚡ {max_app[1]} is consuming most power")

    return tips

def get_dashboard_alert(monthly_bill):
    if monthly_bill > ALERT_THRESHOLD:
        return "🚨 High Electricity Usage Detected!"
    elif monthly_bill > 1000:
        return "⚠ Moderate Usage"
    return "✅ Usage Normal"
# ---------------- Database Initialization ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        phone TEXT,
        budget REAL DEFAULT 0,
        profile_pic TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS appliances(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        power REAL,
        hours REAL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        units REAL,
        amount REAL,
        reading REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
  
    conn.commit()
    
    # Check if columns exist in users table
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    if 'budget' not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN budget REAL DEFAULT 0")
        conn.commit()
    if 'profile_pic' not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
        conn.commit()
        
    conn.close()

init_db()

# ---------------- Email Alert ----------------
def send_alert_email(to_email, amount, budget=None):
    try:
        msg = EmailMessage()
        if budget and budget > 0:
            content = f"⚠️ Alert! Your electricity bill (₹{amount:.2f}) has exceeded your monthly budget of ₹{budget:.2f}."
        else:
            content = f"⚠️ Alert! Your electricity bill is high: ₹{amount:.2f}"
            
        msg.set_content(content)
        msg['Subject'] = "Electricity Bill Alert"
        msg['From'] = "azmatchand9581@gmail.com"  
        msg['To'] = to_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("azmatchand9581@gmail.com", "wqjgmudiojmtlwhr")  # App password
            smtp.send_message(msg)
        print(f"Alert email sent to {to_email}!")
    except Exception as e:
        print("Email sending failed:", e)

# ---------------- Login ----------------
@app.route("/", methods=["GET", "POST"])
def welcome():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            return redirect(f"/dashboard/{user[0]}")
        else:
            return "Invalid username or password"
    return render_template("welcome.html")

# ---------------- Register ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        phone = request.form["phone"]
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username,password,email,phone) VALUES (?,?,?,?)",
                        (username,password,email,phone))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists"
        conn.close()
        return redirect(url_for('welcome', skip_lang='true'))
    return render_template("register.html")

# ---------------- Dashboard ----------------
@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # User info
    cur.execute("SELECT username, email, phone, profile_pic FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()
    username, email, phone, profile_pic = user if user else ("User","", "", None)

    # Appliances
    cur.execute("SELECT id, name, (power*hours/1000.0) as units, power, hours FROM appliances WHERE user_id=?", (user_id,))
    
    appliances = cur.fetchall()

    # All bills
    cur.execute("SELECT units, amount, timestamp FROM bills WHERE user_id=? ORDER BY id DESC", (user_id,))
    bills = cur.fetchall()

    # ✅ NEW: Latest bill (IMPORTANT)
    cur.execute("SELECT units, amount FROM bills WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
    #latest_bill = cur.fetchone()
   # 🔥 TOTAL USAGE (IMPORTANT FIX)
    cur.execute("""
        SELECT SUM(power*hours/1000.0)
        FROM appliances
        WHERE user_id=?
    """, (user_id,))
    daily_units = cur.fetchone()[0] or 0
    RATE=5
    monthly_units=daily_units*30
    monthly_bill=monthly_units*RATE
    

    # 💡 SMART SUGGESTIONS (ADD HERE)
    suggestions = smart_suggestions(appliances, monthly_bill)

    
   

    conn.close()

    return render_template("dashboard.html",
        user_id=user_id,
        username=username,
        appliances=appliances,
        bills=bills,
        phone=phone,
        email=email,
        profile_pic=profile_pic,
        suggestions=suggestions
        
        #latest_bill=latest_bill   # ✅ PASS THIS
    )
# ---------------- Upload Page ----------------



# ---------------- Manual Page ----------------
@app.route("/manual-page/<int:user_id>")
def manual_page(user_id):
    # Fetch latest total reading to use as previous reading
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT reading FROM bills WHERE user_id=? AND reading IS NOT NULL ORDER BY id DESC LIMIT 1", (user_id,))
    latest_reading = cur.fetchone()
    previous_reading = latest_reading[0] if latest_reading else 0.0
    conn.close()

    return render_template("manual_page.html",
                           user_id=user_id,
                           previous_reading=previous_reading,
                           units=None,
                           amount=None)
# ---------------- Add Appliance ----------------
@app.route("/appliance", methods=["POST"])
def add_appliance():
    user_id = int(request.form["user_id"])
    name = request.form["name"]
    power = float(request.form["power"])
    hours = float(request.form["hours"])
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO appliances (user_id,name,power,hours) VALUES (?,?,?,?)",
                (user_id, name, power, hours))
    conn.commit()
    conn.close()
    return redirect(f"/dashboard/{user_id}")

# ---------------- Generate Bill from Appliances ----------------
@app.route("/bill/<int:user_id>")
def generate_bill(user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT SUM(power*hours/1000.0) FROM appliances WHERE user_id=?", (user_id,))
    total_units = cur.fetchone()[0] or 0
    amount = total_units * 5
    cur.execute("INSERT INTO bills (user_id, units, amount) VALUES (?,?,?)",
                (user_id, total_units, amount))
    # Email alert if high
    cur.execute("SELECT email, budget FROM users WHERE id=?", (user_id,))
    user_data = cur.fetchone()
    email = user_data[0]
    budget = user_data[1] or 0
    
    threshold = budget if budget > 0 else ALERT_THRESHOLD
    if amount >= threshold:
        send_alert_email(email, amount, budget)
    conn.commit()
    conn.close()
    return redirect(f"/dashboard/{user_id}")

# ---------------- Upload Page ----------------
@app.route("/upload-page/<int:user_id>")
def upload_page(user_id):
    return render_template("upload_page.html", user_id=user_id)

# ---------------- Upload Meter Photo ----------------
@app.route("/upload-meter", methods=["POST"])
def upload_meter():
    if 'meter_photo' not in request.files:
        return "No file uploaded"
    
    file = request.files['meter_photo']
    user_id = request.form.get('user_id')
    
    if file.filename == '':
        return "No selected file"
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        current_reading = 0.0
        potential_readings = []
        
        # Preprocessing & OCR
        try:
            img = Image.open(file_path)
            
            # Crop to center area (where digits usually are) to reduce noise
            w, h = img.size
            left, top, right, bottom = w * 0.1, h * 0.2, w * 0.9, h * 0.7
            img_cropped = img.crop((left, top, right, bottom))
            
            variations = []
            variations.append(img_cropped)
            
            gray = ImageOps.grayscale(img_cropped)
            variations.append(ImageEnhance.Contrast(gray).enhance(4.0))
            
            inverted = ImageOps.invert(gray)
            variations.append(ImageEnhance.Contrast(inverted).enhance(4.0))
            
            for threshold in [100, 128, 150, 180]:
                variations.append(gray.point(lambda p: 255 if p > threshold else 0))
                variations.append(inverted.point(lambda p: 255 if p > threshold else 0))
            
            all_text = ""
            configs = [
                '--psm 7 -c tessedit_char_whitelist=0123456789.',
                '--psm 6 -c tessedit_char_whitelist=0123456789.',
                '--psm 11 -c tessedit_char_whitelist=0123456789.',
                '--oem 3 --psm 7 digits'
            ]
            
            for v_img in variations:
                v_img = v_img.resize((v_img.width * 2, v_img.height * 2), Image.Resampling.LANCZOS)
                v_img = v_img.filter(ImageFilter.SHARPEN)
                for config in configs:
                    text = pytesseract.image_to_string(v_img, config=config).strip()
                    if text:
                        all_text += " " + text
            
            cleaned = re.sub(r'\s+', '', all_text)
            all_nums = re.findall(r'\d{3,7}(?:\.\d{1,2})?', cleaned)
            
            if all_nums:
                # Filter out years and collect all unique readings
                readings = [float(n) for n in all_nums if not (2020 <= float(n) <= 2030)]
                if readings:
                    from collections import Counter
                    counts = Counter(readings)
                    # If we have a clear winner (appearing more than once)
                    if counts.most_common(1)[0][1] > 1:
                        current_reading = counts.most_common(1)[0][0]
                    else:
                        # Otherwise, take the first one found but mark it as potential
                        current_reading = 0.0 
                    
                    # Store up to 3 most common/first readings as suggestions
                    potential_readings = [str(r[0]) for r in counts.most_common(3)]
            
        except Exception as e:
            print("OCR process failed:", e)
            current_reading = 0.0
            
        # Fetch previous reading from database
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT reading FROM bills WHERE user_id=? AND reading IS NOT NULL ORDER BY id DESC LIMIT 1", (user_id,))
        latest_reading = cur.fetchone()
        previous_reading = latest_reading[0] if latest_reading else 0.0
        conn.close()

        # Calculation for display
        amount = max(0, (current_reading - previous_reading) * 5)
        
        return render_template("upload_page.html", 
                               user_id=user_id, 
                               current_reading=current_reading,
                               potential_readings=potential_readings,
                               previous_reading=previous_reading,
                               amount=amount, 
                               scanned=True)

# ---------------- Confirm and Save Bill ----------------
@app.route("/confirm-bill", methods=["POST"])
def confirm_bill():
    user_id = int(request.form["user_id"])
    units = float(request.form["units"])
    reading = float(request.form.get("current_reading", 0)) # Should be passed from frontend
    amount = units * 5
    
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    
    cur.execute("INSERT INTO bills (user_id, units, amount, reading) VALUES (?,?,?,?)",
                (user_id, units, amount, reading))
    
    # Email alert
    cur.execute("SELECT email, budget FROM users WHERE id=?", (user_id,))
    user_data = cur.fetchone()
    email = user_data[0]
    budget = user_data[1] or 0
    
    threshold = budget if budget > 0 else ALERT_THRESHOLD
    if amount >= threshold:
        send_alert_email(email, amount, budget)
        
    conn.commit()
    conn.close()
    
    return redirect(f"/dashboard/{user_id}")



# ---------------- Manual Entry ----------------
@app.route("/manual-entry", methods=["POST"])
def manual_entry():
    user_id = int(request.form["user_id"])
    previous = float(request.form["previous"])
    current = float(request.form["current"])

    # Calculate units
    units = current - previous

    # Safety check
    if units < 0:
        return "❌ Current reading must be greater than previous reading"

    amount = units * 5

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("INSERT INTO bills (user_id, units, amount, reading) VALUES (?,?,?,?)",
                (user_id, units, amount, current))

    # Email alert
    cur.execute("SELECT email, budget FROM users WHERE id=?", (user_id,))
    user_data = cur.fetchone()
    email = user_data[0]
    budget = user_data[1] or 0
    
    threshold = budget if budget > 0 else ALERT_THRESHOLD
    if amount >= threshold:
        send_alert_email(email, amount, budget)

    conn.commit()
    conn.close()

    return render_template("manual_page.html",
                           user_id=user_id,
                           units=units,
                           amount=amount)
    

# ---------------- Prediction from Appliances ----------------
@app.route("/predict/<int:user_id>")
def predict(user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT SUM(power * hours / 1000.0)
        FROM appliances
        WHERE user_id=?
    """, (user_id,))

    daily_units = cur.fetchone()[0] or 0

    # ✅ FIXED LOGIC
    weekly_units = daily_units * 7
    monthly_units = daily_units * 30

    RATE = 5

    weekly_bill = weekly_units * RATE
    monthly_bill = monthly_units * RATE

    cur.execute("SELECT email, budget FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()
    email = user[0] if user else None
    budget = user[1] if user else 0

    threshold = budget if budget > 0 else ALERT_THRESHOLD
    if email and monthly_bill >= threshold:
        send_alert_email(email, monthly_bill, budget)

    conn.close()

    return jsonify({
        "weekly_units": round(weekly_units, 2),
        "monthly_units": round(monthly_units, 2),
        "weekly_bill": round(weekly_bill, 2),
        "monthly_bill": round(monthly_bill, 2)
    })

@app.route("/edit-appliance", methods=["POST"])
def edit_appliance():
    appliance_id = int(request.form["appliance_id"])
    user_id = int(request.form["user_id"])
    name = request.form["name"]
    power = float(request.form["power"])
    hours = float(request.form["hours"])
    
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE appliances SET name=?, power=?, hours=? WHERE id=?", 
                (name, power, hours, appliance_id))
    conn.commit()
    conn.close()
    
    return redirect(f"/dashboard/{user_id}")

@app.route("/delete-appliance/<int:appliance_id>/<int:user_id>")
def delete_appliance(appliance_id, user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM appliances WHERE id=?", (appliance_id,))

    conn.commit()
    conn.close()

    return redirect(f"/dashboard/{user_id}")

# ---------------- Graph Data ----------------
@app.route("/get-data/<int:user_id>")
def get_data(user_id):

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔮 Predicted bill
    cur.execute("""
        SELECT SUM(power*hours/1000.0)
        FROM appliances
        WHERE user_id=?
    """, (user_id,))
    daily_units = cur.fetchone()[0] or 0

    monthly_units = daily_units * 30
    predicted_bill = monthly_units * 5


    # 📜 Last 12 bills
    cur.execute("""
        SELECT amount, timestamp FROM bills
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 12
    """, (user_id,))

    history = cur.fetchall()
    history_list = [row[0] for row in history]
    # Format history with month names and year
    formatted_history = []
    import datetime
    for row in history:
        try:
            # SQLite default timestamp format is YYYY-MM-DD HH:MM:SS
            date_obj = datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            month_num = date_obj.month
            year = date_obj.year
        except:
            month_num = 1
            year = 2026
        formatted_history.append({"amount": row[0], "month_num": month_num, "year": year})

    # User info
    cur.execute("SELECT budget FROM users WHERE id=?", (user_id,))
    budget = cur.fetchone()[0] or 0

    # 📊 Actual bill
    actual_bill = history_list[0] if len(history_list) > 0 else 0
    prev_bill = history_list[1] if len(history_list) > 1 else 0
    
    # 📉 Percentage change
    percentage_change = 0
    if prev_bill > 0:
        percentage_change = ((actual_bill - prev_bill) / prev_bill) * 100

    # 🌍 Carbon Footprint (Approx 0.85 kg CO2 per unit)
    cur.execute("SELECT units FROM bills WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
    latest_units_row = cur.fetchone()
    latest_units = latest_units_row[0] if latest_units_row else 0
    carbon_footprint = (latest_units * 0.85)

    # ⚠️ Budget Alert
    budget_warning = False
    if budget > 0 and actual_bill > budget:
        budget_warning = True

    # ⚡ Appliances data (Cost breakdown)
    cur.execute("""
        SELECT id, name, (power*hours/1000.0) as units, power, hours
        FROM appliances
        WHERE user_id=?
    """, (user_id,))

    appliances = cur.fetchall()
    appliance_breakdown = []
    for app in appliances:
        cost = app[2] * 30 * 5 # Monthly cost
        appliance_breakdown.append({
            "id": app[0],
            "name": app[1],
            "units": app[2],
            "power": app[3],
            "hours": app[4],
            "cost": round(cost, 2)
        })

    conn.close()

    return jsonify({
        "predicted": round(predicted_bill, 2),
        "actual": round(actual_bill, 2),
        "history": history_list,
        "formatted_history": formatted_history,
        "appliances": appliance_breakdown,
        "percentage_change": round(percentage_change, 2),
        "budget": budget,
        "carbon_footprint": round(carbon_footprint, 2),
        "budget_warning": budget_warning
    })

@app.route("/clear-history/<int:user_id>")
def clear_history(user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM bills WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(f"/dashboard/{user_id}")


@app.route("/update-budget", methods=["POST"])
def update_budget():
    user_id = int(request.form["user_id"])
    budget = float(request.form["budget"])
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET budget=? WHERE id=?", (budget, user_id))
    conn.commit()
    conn.close()
    return redirect(f"/dashboard/{user_id}")

# ---------------- Update Profile ----------------
@app.route("/update-profile", methods=["POST"])
def update_profile_view():
    user_id = request.form.get("user_id")
    username = request.form.get("username")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    profile_pic = request.files.get("profile_pic")
    
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    
    # Update text fields
    if password:
        cur.execute("UPDATE users SET username=?, email=?, phone=?, password=? WHERE id=?", 
                    (username, email, phone, password, user_id))
    else:
        cur.execute("UPDATE users SET username=?, email=?, phone=? WHERE id=?", 
                    (username, email, phone, user_id))
    
    # Handle profile picture upload
    if profile_pic and profile_pic.filename != '':
        filename = secure_filename(f"profile_{user_id}_{profile_pic.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile_pic.save(file_path)
        cur.execute("UPDATE users SET profile_pic=? WHERE id=?", (filename, user_id))
        
    conn.commit()
    conn.close()
    
    return redirect(url_for("dashboard", user_id=user_id))

# ---------------- Suggestions ----------------
@app.route("/suggestions/<int:user_id>")
def suggestions(user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    
    # Get all appliances
    cur.execute("SELECT name, (power*hours/1000.0) as units, power, hours FROM appliances WHERE user_id=?", (user_id,))
    appliances = cur.fetchall()
    daily_units = sum(a[1] for a in appliances)
    predicted_bill = daily_units * 30 * 5
    
    # Get latest 2 bills for trend analysis
    cur.execute("SELECT amount, timestamp FROM bills WHERE user_id=? ORDER BY id DESC LIMIT 2", (user_id,))
    bill_history = cur.fetchall()
    actual_bill = bill_history[0][0] if len(bill_history) > 0 else 0
    prev_bill = bill_history[1][0] if len(bill_history) > 1 else 0
    
    # 1. Main Status & Efficiency Score
    status = []
    status_color = "#00ffc3"
    smart_actions = []
    
    if actual_bill > 0 and predicted_bill > 0:
        efficiency = (predicted_bill / actual_bill) * 100
        if efficiency > 100: efficiency = 100 # Predicted more than actual is good
        
        if actual_bill > predicted_bill * 1.2:
            status.append({
                "key": "usage_leak_alert",
                "params": {"actual": f"{actual_bill:.2f}", "predicted": f"{predicted_bill:.2f}"}
            })
            status_color = "#ff4d4d"
        elif actual_bill < predicted_bill * 0.9:
            status.append({"key": "great_job_alert"})
            status_color = "#2ecc71"
        else:
            status.append({"key": "usage_stable_alert"})

    # 2. Trend Analysis
    if prev_bill > 0:
        diff = actual_bill - prev_bill
        perc = (diff / prev_bill) * 100
        if diff > 0:
            status.append({
                "key": "bill_increased_alert",
                "params": {"perc": f"{perc:.1f}"}
            })
            # Add a specific recommendation for increasing bills
            smart_actions.append({"key": "smart_action_increase"})
        else:
            status.append({
                "key": "bill_decreased_alert",
                "params": {"perc": f"{abs(perc):.1f}"}
            })
            smart_actions.append({"key": "smart_action_decrease"})

    # 3. Dynamic Savings Opportunities
    savings_tips = []
    if appliances:
        top_app = max(appliances, key=lambda x: x[1])
        app_name = top_app[0].upper()
        # Calculate savings if used 1 hour less
        hourly_cost = (top_app[2] / 1000.0) * 5
        monthly_savings = hourly_cost * 30
        savings_tips.append({
            "title_key": "savings_opportunity_title",
            "desc_key": "savings_opportunity_desc",
            "params": {"appliance": app_name, "amount": f"{monthly_savings:.2f}"}
        })

    # 4. Appliance-Specific Smart Advice
    app_names = [a[0].lower() for a in appliances]
    
    if any(x in ' '.join(app_names) for x in ['ac', 'air conditioner', 'cooler']):
        smart_actions.append({"key": "smart_action_ac"})
    if any(x in ' '.join(app_names) for x in ['fridge', 'refrigerator']):
        smart_actions.append({"key": "smart_action_fridge"})
    if any(x in ' '.join(app_names) for x in ['geyser', 'heater', 'water heater']):
        smart_actions.append({"key": "smart_action_geyser"})
    if any(x in ' '.join(app_names) for x in ['washing machine', 'dryer']):
        smart_actions.append({"key": "smart_action_washing"})
    if any(x in ' '.join(app_names) for x in ['bulb', 'led', 'light']):
        smart_actions.append({"key": "smart_action_led"})
    if any(x in ' '.join(app_names) for x in ['fan', 'ceiling fan']):
        smart_actions.append({"key": "smart_action_fan"})
    if any(x in ' '.join(app_names) for x in ['tv', 'television']):
        smart_actions.append({"key": "smart_action_tv"})
    
    if not smart_actions:
        smart_actions.append({"key": "smart_action_general"})

    # 5. General Pro Tips (Randomized for variety)
    tip_keys = [
        "tip_phantom",
        "tip_ac_clean",
        "tip_sunlight",
        "tip_washing",
        "tip_sleep_mode"
    ]
    import random
    random_tips = random.sample(tip_keys, 3)
    
    conn.close()
    return jsonify({
        "status_list": status,
        "status_color": status_color,
        "savings_tips": savings_tips,
        "smart_actions": smart_actions,
        "general_tips": random_tips
    })

# ---------------- Run ----------------
if __name__ == "__main__":
    app.run(debug=True)