
from flask import Flask, render_template, request, redirect, session
from db import Base, engine, SessionLocal
from ai import analyze_resume
import models
import PyPDF2
import docx
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Create database tables
Base.metadata.create_all(bind=engine)


# HOME
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")

    return redirect("/login")


# SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():

    db = SessionLocal()

    try:
        if request.method == "POST":

            email = request.form.get("email")
            password = request.form.get("password")

            if not email or not password:
                return "Email and password are required"

            existing_user = db.query(models.User).filter_by(
                email=email
            ).first()

            if existing_user:
                return "User already exists"

            user = models.User(
                email=email,
                password=password
            )

            db.add(user)
            db.commit()

            return redirect("/login")

        return render_template("signup.html")

    finally:
        db.close()


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    db = SessionLocal()

    try:
        if request.method == "POST":

            email = request.form.get("email")
            password = request.form.get("password")

            user = db.query(models.User).filter_by(
                email=email,
                password=password
            ).first()

            if user:
                session["user"] = user.email
                return redirect("/dashboard")

            return "Invalid credentials"

        return render_template("login.html")

    finally:
        db.close()


# DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user" not in session:
        return redirect("/login")

    result = None
    resume_text = ""
    user_goal = ""

    if request.method == "POST":

        user_goal = request.form.get("role", "").strip()
        resume_text = request.form.get("resume", "").strip()

        file = request.files.get("file")

        # FILE HANDLING
        if file and file.filename:

            filename = file.filename.lower()

            try:

                if filename.endswith(".pdf"):

                    pdf_reader = PyPDF2.PdfReader(file)

                    text = ""

                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""

                    resume_text = text.strip()

                elif filename.endswith(".docx"):

                    doc = docx.Document(file)

                    text = ""

                    for para in doc.paragraphs:
                        text += para.text + "\n"

                    resume_text = text.strip()

                else:
                    result = {
                        "error": "Please upload a PDF or DOCX file."
                    }

            except Exception as e:

                result = {
                    "error": f"File reading error: {str(e)}"
                }

        # CHECK INPUT
        if result is None:

            if not resume_text:
                result = {
                    "error": "Please upload a resume or enter resume text."
                }

            elif not user_goal:
                result = {
                    "error": "Please select your career goal."
                }

            else:

                try:

                    # AI RESUME ANALYSIS
                    result = analyze_resume(
                        resume_text,
                        user_goal
                    )

                    # SAVE REPORT TO DATABASE
                    db = SessionLocal()

                    try:

                        user = db.query(models.User).filter_by(
                            email=session["user"]
                        ).first()

                        if user:

                            report = models.Report(
                                user_id=user.id,
                                resume_text=resume_text,
                                result=json.dumps(result)
                            )

                            db.add(report)
                            db.commit()

                    finally:
                        db.close()

                except Exception as e:

                    result = {
                        "error": f"AI or database error: {str(e)}"
                    }

    return render_template(
        "dashboard.html",
        user=session["user"],
        result=result
    )


# HISTORY
@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        user = db.query(models.User).filter_by(
            email=session["user"]
        ).first()

        if not user:
            return redirect("/login")

        # Get all reports of logged-in user
        reports = db.query(models.Report).filter_by(
            user_id=user.id
        ).all()

        parsed_reports = []

        for r in reports:

            try:
                parsed_result = json.loads(r.results)

            except (json.JSONDecodeError, TypeError):
                parsed_result = {}

            parsed_reports.append({
                "resume": r.resume_text,
                "result": parsed_result
            })

        return render_template(
            "history.html",
            reports=parsed_reports
        )

    finally:
        db.close()


# LOGOUT
@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")


# RUN APPLICATION
if __name__ == "__main__":
    app.run(debug=True)
