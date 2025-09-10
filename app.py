from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# Absolute path for uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ------------------- Database Connection -------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # change to your MySQL username
        password="Aman@7550", # change to your MySQL password
        database="user_profile"  # ensure your DB name is correct
    )

# ------------------- Routes -------------------

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get form data
    name = request.form["name"]
    email = request.form["email"]
    age = request.form["age"]
    gender = request.form["gender"]
    college = request.form["college"]
    cgpa = request.form["cgpa"]
    skills = request.form["skills"]
    bio = request.form["bio"]

    # Handle resume upload
    resume = request.files["resume"]
    resume_filename = resume.filename
    resume.save(os.path.join(app.config["UPLOAD_FOLDER"], resume_filename))

    # Save record in DB
    cursor.execute("""
        INSERT INTO profiles 
        (name, email, age, gender, college, cgpa, skills, bio, resume_path) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (name, email, age, gender, college, cgpa, skills, bio, resume_filename))
    conn.commit()
    cursor.close()
    conn.close()

    return render_template("success.html")

# ------------------- Admin Dashboard -------------------
@app.route("/admin")
def admin():
    search_query = request.args.get("search", "")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search_query:
        cursor.execute("""
            SELECT * FROM profiles
            WHERE name LIKE %s OR email LIKE %s OR college LIKE %s OR skills LIKE %s
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM profiles")

    profiles = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin.html", profiles=profiles, search_query=search_query)

# ------------------- Resume Serving -------------------
@app.route("/resume/<path:filename>")
def get_resume(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

# ------------------- Delete Selected -------------------
@app.route("/delete_selected", methods=["POST"])
def delete_selected():
    profile_id = request.form.get("profile_id")
    if profile_id:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get resume file path before deleting
        cursor.execute("SELECT resume_path FROM profiles WHERE id = %s", (profile_id,))
        result = cursor.fetchone()

        if result and result["resume_path"]:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], result["resume_path"])
            if os.path.exists(file_path):
                os.remove(file_path)

        # Delete from DB
        cursor.execute("DELETE FROM profiles WHERE id = %s", (profile_id,))
        conn.commit()
        cursor.close()
        conn.close()

        flash("✅ Selected profile deleted successfully.", "danger")

    return redirect(url_for("admin"))

# ------------------- Delete All -------------------
@app.route("/delete_all", methods=["POST"])
def delete_all():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete all DB records
    cursor.execute("DELETE FROM profiles")
    conn.commit()
    cursor.close()
    conn.close()

    # Clear the uploads folder
    for f in os.listdir(app.config["UPLOAD_FOLDER"]):
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], f)
        if os.path.isfile(file_path):
            os.remove(file_path)

    flash("⚠️ All data deleted successfully.", "danger")
    return redirect(url_for("admin"))

# ------------------- Edit Profile -------------------
@app.route("/edit/<int:profile_id>", methods=["GET", "POST"])
def edit_profile(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        # Get updated form data
        name = request.form["name"]
        email = request.form["email"]
        age = request.form["age"]
        gender = request.form["gender"]
        college = request.form["college"]
        cgpa = request.form["cgpa"]
        skills = request.form["skills"]
        bio = request.form["bio"]

        # Handle new resume if uploaded
        resume = request.files.get("resume")
        if resume and resume.filename != "":
            resume_filename = resume.filename
            resume.save(os.path.join(app.config["UPLOAD_FOLDER"], resume_filename))
            cursor.execute("""
                UPDATE profiles 
                SET name=%s, email=%s, age=%s, gender=%s, college=%s, cgpa=%s, skills=%s, bio=%s, resume_path=%s
                WHERE id=%s
            """, (name, email, age, gender, college, cgpa, skills, bio, resume_filename, profile_id))
        else:
            cursor.execute("""
                UPDATE profiles 
                SET name=%s, email=%s, age=%s, gender=%s, college=%s, cgpa=%s, skills=%s, bio=%s
                WHERE id=%s
            """, (name, email, age, gender, college, cgpa, skills, bio, profile_id))

        conn.commit()
        cursor.close()
        conn.close()
        return render_template("success.html")

    # GET request → load profile data
    cursor.execute("SELECT * FROM profiles WHERE id = %s", (profile_id,))
    profile = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("edit.html", profile=profile)

# ------------------- Run App -------------------
if __name__ == "__main__":
    app.run(debug=True)
