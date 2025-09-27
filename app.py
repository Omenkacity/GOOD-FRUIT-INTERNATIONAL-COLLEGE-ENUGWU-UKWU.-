from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# --- Utility: calculate grade + remark ---
def calculate_result(ca, exam):
    total = ca + exam
    if total >= 70:
        grade, remark = "A", "Excellent"
    elif total >= 60:
        grade, remark = "B", "Very Good"
    elif total >= 50:
        grade, remark = "C", "Good"
    elif total >= 45:
        grade, remark = "D", "Fair"
    elif total >= 40:
        grade, remark = "E", "Pass"
    else:
        grade, remark = "F", "Fail"
    return total, grade, remark

# --- DB Init ---
def init_db():
    conn = sqlite3.connect("school.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, class TEXT, photo TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject_id INTEGER,
        ca INTEGER, exam INTEGER, total INTEGER,
        grade TEXT, remark TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    )""")
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/students", methods=["GET","POST"])
def students():
    conn = sqlite3.connect("school.db")
    c = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        class_name = request.form["class"]
        c.execute("INSERT INTO students(name,class) VALUES(?,?)", (name,class_name))
        conn.commit()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()
    return render_template("students.html", students=students)

@app.route("/subjects", methods=["GET","POST"])
def subjects():
    conn = sqlite3.connect("school.db")
    c = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        c.execute("INSERT INTO subjects(name) VALUES(?)", (name,))
        conn.commit()
    c.execute("SELECT * FROM subjects")
    subjects = c.fetchall()
    conn.close()
    return render_template("subjects.html", subjects=subjects)

@app.route("/results", methods=["GET","POST"])
def results():
    conn = sqlite3.connect("school.db")
    c = conn.cursor()
    if request.method == "POST":
        student_id = request.form["student_id"]
        subject_id = request.form["subject_id"]
        ca = int(request.form["ca"])
        exam = int(request.form["exam"])
        total, grade, remark = calculate_result(ca, exam)
        c.execute("""INSERT INTO results(student_id,subject_id,ca,exam,total,grade,remark)
                     VALUES(?,?,?,?,?,?,?)""", (student_id,subject_id,ca,exam,total,grade,remark))
        conn.commit()
    c.execute("""SELECT results.id, students.name, subjects.name,
                        results.ca, results.exam, results.total,
                        results.grade, results.remark
                 FROM results
                 JOIN students ON results.student_id=students.id
                 JOIN subjects ON results.subject_id=subjects.id""")
    results = c.fetchall()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    c.execute("SELECT * FROM subjects")
    subjects = c.fetchall()
    conn.close()
    return render_template("results.html", results=results, students=students, subjects=subjects)

# --- Reports Route (Merged here) ---
@app.route("/reports", methods=["GET"])
def reports():
    student_id = request.args.get("student")
    class_name = request.args.get("class")

    conn = sqlite3.connect("school.db")
    c = conn.cursor()

    query = """SELECT results.id, students.name, students.class, subjects.name,
                      results.ca, results.exam, results.total, results.grade, results.remark
               FROM results
               JOIN students ON results.student_id = students.id
               JOIN subjects ON results.subject_id = subjects.id
               WHERE 1=1"""
    params = []

    if student_id:
        query += " AND students.id=?"
        params.append(student_id)
    if class_name:
        query += " AND students.class=?"
        params.append(class_name)

    c.execute(query, params)
    reports = c.fetchall()

    scores = [r[6] for r in reports]
    summary = {
        "total_students": len(set([r[1] for r in reports])),
        "average": sum(scores) / len(scores) if scores else 0,
        "highest": max(scores) if scores else 0,
        "lowest": min(scores) if scores else 0,
    }

    conn.close()
    return render_template("reports.html", reports=reports, summary=summary)

# --- Error Codes Page (Section 7 later) ---
@app.route("/errors")
def errors():
    return render_template("errors.html")

if __name__ == "__main__":
    app.run(debug=True)
