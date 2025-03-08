from flask import Flask, render_template, request, redirect, url_for, session
import random
import os

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # Required for session management

# Function to extract MCQs from a TXT file
def extract_mcqs(file_path):
    questions = []
    current_question = None
    options = []
    correct_answer = None

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()  # Read all lines

        for line in lines:
            text = line.strip()  # Remove spaces and newlines

            # Ignore empty lines
            if not text:
                continue

            # Detect new question (starts with "Q" and has ":" or ".")
            if text.startswith("Q") and (":" in text or "." in text):
                if current_question and options:  # Save previous question before starting a new one
                    questions.append({"question": current_question, "options": options, "correct": correct_answer})
                current_question = text  # Store new question
                options = []
                correct_answer = None  # Reset for next question

            # Detect answer choices (start with "!")
            elif text.startswith("!") and current_question:
                option_text = text.lstrip("!").strip()  # Remove "!" and extra spaces
                if "✅" in option_text:
                    correct_answer = option_text.replace("✅", "").strip()  # Store correct answer
                options.append(option_text.replace("✅", "").strip())  # Always remove ✅ from display

        # Add last question if present
        if current_question and options:
            questions.append({"question": current_question, "options": options, "correct": correct_answer})

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"Error reading the file: {e}")
        return []

    return questions

# Load questions from the file
input_file = "mcq_questions.txt"
questions = extract_mcqs(input_file)
if not questions:
    print("No questions found. Please check the file and its format.")
random.shuffle(questions)

# Initialize session variables
def init_session():
    if "current_question_index" not in session:
        session["current_question_index"] = 0
    if "correct_count" not in session:
        session["correct_count"] = 0
    if "wrong_count" not in session:
        session["wrong_count"] = 0
    if "feedback" not in session:
        session["feedback"] = None

# Home page - Display the current question
@app.route("/")
def home():
    init_session()  # Ensure session is initialized
    if session["current_question_index"] < len(questions):
        q = questions[session["current_question_index"]]
        return render_template(
            "quiz.html",
            question=q,
            questions_left=len(questions) - session["current_question_index"],
            correct_count=session["correct_count"],
            wrong_count=session["wrong_count"],
            feedback=session["feedback"]
        )
    else:
        return redirect(url_for("completed"))

# Check the user's answer
@app.route("/check", methods=["POST"])
def check():
    init_session()  # Ensure session is initialized
    selected_answer = request.form.get("answer")
    correct_answer = questions[session["current_question_index"]]["correct"]

    if selected_answer == correct_answer:
        session["correct_count"] += 1
        session["feedback"] = {"type": "correct", "message": "✅ Correct! Well done!"}
        return redirect(url_for("show_correct_answer"))  # Redirect to the correct answer page
    else:
        session["wrong_count"] += 1
        session["feedback"] = {"type": "wrong", "message": "❌ That's not the right answer. Try again!"}
        return redirect(url_for("home"))

# Show the correct answer
@app.route("/correct")
def show_correct_answer():
    init_session()  # Ensure session is initialized
    q = questions[session["current_question_index"]]
    return render_template("correct_answer.html", question=q, correct_answer=q["correct"])

# Move to the next question
@app.route("/next")
def next_question():
    init_session()  # Ensure session is initialized
    session["current_question_index"] += 1
    session["feedback"] = None  # Clear feedback
    return redirect(url_for("home"))

# Quiz completed page
@app.route("/completed")
def completed():
    correct_count = session["correct_count"]
    wrong_count = session["wrong_count"]
    session.clear()  # Reset session
    return render_template("completed.html", correct_count=correct_count, wrong_count=wrong_count)

# Reset the quiz
@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("home"))

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
