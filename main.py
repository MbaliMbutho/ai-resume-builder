from flask import Flask, request, render_template, send_file
import cohere
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Cohere API setup
cohere_api_key = "NqCDyPmfZHiXEDiyn0Xooutz67b0XHFPoeZ8qeYy"
co = cohere.Client(cohere_api_key)

# Store resume text for PDF
generated_resume = ""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    global generated_resume
    name = request.form["name"]
    job = request.form["job"]
    email = request.form["email"]
    phone = request.form["phone"]
    summary = request.form["summary"]
    skills = request.form["skills"]
    experience = request.form["experience"]
    education = request.form["education"]

    prompt = (
        f"Create a professional resume for {name} applying as a {job}.\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n"
        f"Summary: {summary}\n"
        f"Skills: {skills}\n"
        f"Work Experience: {experience}\n"
        f"Education: {education}\n"
        "Format the resume professionally."
    )

    response = co.generate(
        model="command",
        prompt=prompt,
        max_tokens=300,
        temperature=0.7,
    )

    result = response.generations[0].text.strip()
    generated_resume = result

    return f"<pre>{result}</pre><br><a href='/download'>Download PDF</a>"

@app.route("/download")
def download_pdf():
    global generated_resume
    filename = "resume_summary.pdf"
    c = canvas.Canvas(filename)
    c.drawString(100, 800, "Resume Summary:")
    text = c.beginText(100, 780)
    for line in generated_resume.split('\n'):
        text.textLine(line)
    c.drawText(text)
    c.save()
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
