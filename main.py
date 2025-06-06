from flask import Flask, render_template, request, make_response
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import cohere

app = Flask(__name__)

# Initialize Cohere client
COHERE_API_KEY = "NqCDyPmfZHiXEDiyn0Xooutz67b0XHFPoeZ8qeYy"
co = cohere.Client(COHERE_API_KEY)

generated_data = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    global generated_data
    data = request.form.to_dict()

    prompt = (
        f"Create a professional resume for {data.get('name')} applying as a {data.get('job')}.\n"
        f"Email: {data.get('email')}\n"
        f"Phone: {data.get('phone')}\n"
        f"Summary: {data.get('summary')}\n"
        f"Skills: {data.get('skills')}\n"
        f"Work Experience: {data.get('experience')}\n"
        f"Education: {data.get('education')}\n"
        f"Certifications: {data.get('certifications', '')}\n"
        "Format the resume professionally with clear section headings: Summary, Skills, Work Experience, Education, Certifications. "
        "Always include each section heading, even if the section is empty."
    )

    response = co.generate(
        model="command",
        prompt=prompt,
        max_tokens=1500,
        temperature=0.7
    )
    resume_text = response.generations[0].text.strip()

    # Remove unwanted starting phrases if present
    unwanted_phrase_1 = f"Here is a sample resume for {data.get('name')}, formatted with the section headings you"
    unwanted_phrase_2 = f"Here is a sample resume for {data.get('name')} applying for"

    if resume_text.startswith(unwanted_phrase_1):
        resume_text = resume_text[len(unwanted_phrase_1):].strip()
    elif resume_text.startswith(unwanted_phrase_2):
        resume_text = resume_text[len(unwanted_phrase_2):].strip()

    generated_data = {
        "resume": resume_text,
        **data
    }

    return render_template("result.html", hide_buttons=False, resume=resume_text, **data)


def wrap_text(text, max_width, pdf_canvas, font_name, font_size):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        width = pdf_canvas.stringWidth(test_line, font_name, font_size)

        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


@app.route("/download")
def download_pdf():
    global generated_data

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Fonts
    heading_font = "Helvetica-Bold"
    body_font = "Helvetica"
    heading_font_size = 14
    body_font_size = 10

    margin = 50
    max_width = width - 2 * margin
    x = margin
    y = height - margin

    line_height = body_font_size + 4
    section_spacing = 20

    # Draw border rectangle around page content
    pdf.setLineWidth(2)
    pdf.rect(margin / 2, margin / 2, width - margin, height - margin)

    def draw_heading(text):
        nonlocal y
        if y - section_spacing < margin:
            pdf.showPage()
            y = height - margin
            # Redraw border on new page
            pdf.setLineWidth(2)
            pdf.rect(margin / 2, margin / 2, width - margin, height - margin)
        pdf.setFont(heading_font, heading_font_size)
        pdf.drawString(x, y, text)
        y -= section_spacing
        pdf.setFont(body_font, body_font_size)

    def draw_paragraph(text):
        nonlocal y
        lines = wrap_text(text, max_width, pdf, body_font, body_font_size)
        paragraph_height = len(lines) * line_height + section_spacing // 2

        if y - paragraph_height < margin:
            pdf.showPage()
            y = height - margin
            # Redraw border on new page
            pdf.setLineWidth(2)
            pdf.rect(margin / 2, margin / 2, width - margin, height - margin)

        for line in lines:
            pdf.drawString(x, y, line)
            y -= line_height

        y -= section_spacing // 2

    # Draw Name
    pdf.setFont(heading_font, heading_font_size + 4)
    pdf.drawString(x, y, generated_data.get("name", ""))
    y -= section_spacing

    # Draw Contact Info - only phone number, no email duplication
    pdf.setFont(body_font, body_font_size)
    phone = generated_data.get("phone", "")
    pdf.drawString(x, y, f"Phone: {phone}")
    y -= section_spacing

    # Draw the resume content
    resume_lines = generated_data.get("resume", "").split("\n")
    for line in resume_lines:
        line = line.strip()
        if not line:
            continue  # skip empty lines

        # Heuristic for headings: ends with ":" or all uppercase with few words
        if line.endswith(":") or (line.isupper() and len(line.split()) <= 3):
            draw_heading(line)
        else:
            draw_paragraph(line)

    pdf.save()

    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=resume.pdf'
    return response


if __name__ == "__main__":
    app.run(debug=True)

