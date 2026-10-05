import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-locally")


# Database file location. Default: project folder.
# Hosting e alada folder lagle DATABASE_PATH environment variable set korun.
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "hospihelp.db"))


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            patient TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    db.commit()
    db.close()


# Import er shomoy-i table toiri hobe (gunicorn / WSGI e __main__ chole na)
init_db()


DOCTORS = [
    {
        "id": 1,
        "name": "Dr. Ayesha Rahman",
        "specialization": "Cardiologist",
        "hospital": "Dhaka Medical College Hospital",
        "location": "Motijheel, Dhaka",
        "distance": "2.4 km",
        "rating": "4.8",
        "reviews": 124,
        "experience": "10+ Years",
        "image": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=300"
    },
    {
        "id": 2,
        "name": "Dr. Rahman Siddique",
        "specialization": "General Physician",
        "hospital": "Dhaka Medical College Hospital",
        "location": "Dhaka",
        "distance": "2.4 km",
        "rating": "4.7",
        "reviews": 236,
        "experience": "8+ Years",
        "image": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=300"
    },
    {
        "id": 3,
        "name": "Dr. Farhana Akter",
        "specialization": "General Physician",
        "hospital": "Popular Diagnostic Center",
        "location": "Dhanmondi, Dhaka",
        "distance": "3.1 km",
        "rating": "4.6",
        "reviews": 189,
        "experience": "7+ Years",
        "image": "https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=300"
    },
    {
        "id": 4,
        "name": "Dr. Tanvir Hasan",
        "specialization": "Orthopedic",
        "hospital": "United Hospital",
        "location": "Gulshan, Dhaka",
        "distance": "4.8 km",
        "rating": "4.5",
        "reviews": 132,
        "experience": "9+ Years",
        "image": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=300"
    }
]

HOSPITALS = [
    {"name": "Dhaka Medical College Hospital", "location": "Motijheel, Dhaka", "distance": "2.4 km", "type": "Government"},
    {"name": "United Hospital", "location": "Gulshan, Dhaka", "distance": "4.8 km", "type": "Private"},
    {"name": "Square Hospital", "location": "Dhanmondi, Dhaka", "distance": "5.2 km", "type": "Private"},
    {"name": "Popular Diagnostic Center", "location": "Shantinagar, Dhaka", "distance": "3.1 km", "type": "Diagnostic Center"}
]

SPECIALISTS = {
    "chest pain": "Cardiologist",
    "heart": "Cardiologist",
    "skin rash": "Dermatologist",
    "rash": "Dermatologist",
    "eye pain": "Ophthalmologist",
    "eye": "Ophthalmologist",
    "tooth pain": "Dentist",
    "tooth": "Dentist",
    "fever": "General Physician",
    "cough": "General Physician",
    "broken hand": "Orthopedic",
    "hand pain": "Orthopedic",
    "bone": "Orthopedic"
}


@app.route("/")
def home():
    return render_template("index.html", hospitals=HOSPITALS, doctors=DOCTORS[:2])


@app.route("/find-specialist", methods=["GET", "POST"])
def find_specialist():
    symptom = request.form.get("symptom", "").strip().lower() if request.method == "POST" else ""
    specialist = "General Physician"

    for keyword, value in SPECIALISTS.items():
        if keyword in symptom:
            specialist = value
            break

    results = [d for d in DOCTORS if d["specialization"] == specialist]
    if not results:
        results = DOCTORS

    return render_template(
        "specialists.html",
        doctors=results,
        specialist=specialist,
        symptom=symptom
    )


@app.route("/hospitals")
def hospitals():
    return render_template("hospitals.html", hospitals=HOSPITALS)


@app.route("/doctor/<int:doctor_id>")
def doctor(doctor_id):
    selected = next((d for d in DOCTORS if d["id"] == doctor_id), None)
    if not selected:
        return "Doctor not found", 404
    return render_template("doctor.html", doctor=selected)


@app.route("/appointment/<int:doctor_id>", methods=["GET", "POST"])
def appointment(doctor_id):
    if "user" not in session:
        session["next_url"] = url_for("appointment", doctor_id=doctor_id)
        return redirect(url_for("login"))

    selected = next((d for d in DOCTORS if d["id"] == doctor_id), None)
    if not selected:
        return "Doctor not found", 404

    if request.method == "POST":
        patient = request.form.get("patient", "").strip()
        date = request.form.get("date", "")
        time = request.form.get("time", "")

        db = get_db()
        db.execute(
            "INSERT INTO appointments (user_id, doctor_id, patient, date, time) VALUES (?, ?, ?, ?, ?)",
            (session["user"]["id"], doctor_id, patient, date, time)
        )
        db.commit()
        db.close()

        return redirect(url_for("my_appointments"))

    return render_template("appointment.html", doctor=selected)


@app.route("/my-appointments")
def my_appointments():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()

    rows = db.execute("""
        SELECT *
        FROM appointments
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user"]["id"],)).fetchall()

    db.close()

    appointments = []

    for row in rows:
        item = dict(row)

        doc = next(
            (d for d in DOCTORS if d["id"] == item["doctor_id"]),
            None
        )

        item["doctor_name"] = doc["name"] if doc else "Doctor"

        appointments.append(item)

    return render_template(
        "my_appointments.html",
        appointments=appointments
    )


@app.route("/blood-finder")
def blood_finder():
    return render_template("blood_finder.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }

            next_url = session.pop("next_url", None)
            return redirect(next_url or url_for("home"))

        error = "Invalid email or password."

    return render_template("login.html", error=error)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            error = "Please fill in all fields."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password))
                )
                db.commit()

                user = db.execute(
                    "SELECT * FROM users WHERE email = ?", (email,)
                ).fetchone()
                db.close()

                session["user"] = {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"]
                }

                next_url = session.pop("next_url", None)
                return redirect(next_url or url_for("home"))

            except sqlite3.IntegrityError:
                db.close()
                error = "An account with this email already exists."

    return render_template("signup.html", error=error)


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("profile.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/menu")
def menu():
    return render_template("menu.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
