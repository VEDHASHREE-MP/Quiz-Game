import random
import json
from html import unescape
import requests
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

# ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "replace-me-with-a-random-secret-key"  # session storage
LEADERBOARD_FILE = "leaderboard.json"
# ───────────────────────────────────────────────────────────────


# ░█▀▀░█▀█░█▀█░█░█░█▀▀░█░█
# ░█▀▀░█░█░█░█░█░█░█░█░█▀█
# ░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀▀░▀░▀
def get_questions(category: str, level: str, amount: int = 5) -> list[dict]:
    """Fetch & clean questions from the Open Trivia DB API."""
    category_map = {
        "science": 17,      # Science & Nature
        "history": 23,      # History
        "technology": 18,   # Computers
        "sports": 21,       # Sports
    }
    url = (
        "https://opentdb.com/api.php?"
        f"amount={amount}"
        f"&category={category_map.get(category, 9)}"
        f"&difficulty={level}"
        "&type=multiple"
    )

    api = requests.get(url, timeout=10).json()

    cleaned = []
    for raw in api.get("results", []):
        correct = unescape(raw["correct_answer"])
        options = [unescape(a) for a in raw["incorrect_answers"]] + [correct]
        random.shuffle(options)

        cleaned.append(
            {
                "question":       unescape(raw["question"]),
                "correct_answer": correct,
                "options":        options,
            }
        )
    return cleaned


# ░█░█░█▀█░█▀█
@app.route("/", methods=["GET", "POST"])
def home():
    """Step 1 – ask for the user’s name."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            return render_template("index.html", error="Please enter your name.")
        session["username"] = username  # Don't clear session!
        return redirect(url_for("quiz_setup"))

    return render_template("index.html")


# ░█▀█░█░█░█▀▄   choose category + difficulty
@app.route("/quiz_setup", methods=["GET", "POST"])
def quiz_setup():
    if "username" not in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        category = request.form["category"]
        level    = request.form["level"]
        return redirect(url_for("start_quiz", category=category, level=level))

    return render_template("quiz_setup.html")


# ░█▀█░█░█░█▀█   initialise a new quiz run
@app.route("/quiz/<category>/<level>")
def start_quiz(category, level):
    if "username" not in session:
        return redirect(url_for("home"))

    questions = get_questions(category, level)

    session["questions"]        = questions           # entire quiz
    session["selected_answers"] = [None] * len(questions)
    session["current_question"] = 0
    session["category"]         = category
    session["level"]            = level

    return redirect(url_for("question_page"))


# ░█▀█░█▀█░█▀▄   show ONE question
@app.route("/question")
def question_page():
    if "questions" not in session:
        return redirect(url_for("home"))

    idx       = session["current_question"]
    questions = session["questions"]

    if idx >= len(questions):                     # finished
        return redirect(url_for("submit_quiz"))

    return render_template(
        "quiz.html",
        question = questions[idx],
        index    = idx + 1,
        total    = len(questions),
        category = session["category"],
        level    = session["level"],
        selected = session["selected_answers"][idx],
    )


# ░█▀█░█▀█░▀█▀░█▀█   → NEXT
@app.route("/next_question", methods=["POST"])
def next_question():
    if "questions" not in session:
        return redirect(url_for("home"))

    idx      = session["current_question"]
    selected = request.form.get("selected_answer")
    if selected:
        session["selected_answers"][idx] = selected

    session["current_question"] = idx + 1
    return redirect(url_for("question_page"))


# ░█▀█░█░█░░█░░█▀▀   → PREVIOUS
@app.route("/prev_question", methods=["POST"])
def prev_question():
    if "questions" not in session:
        return redirect(url_for("home"))

    idx      = session["current_question"]
    selected = request.form.get("selected_answer")
    if selected:
        session["selected_answers"][idx] = selected

    session["current_question"] = max(0, idx - 1)
    return redirect(url_for("question_page"))


# ░█░█░▀▄▀░█▀▀░█▀▀   final summary
@app.route("/submit_quiz", methods=["GET"])
def submit_quiz():
    if "questions" not in session:
        return redirect(url_for("home"))

    username  = session["username"]
    questions = session["questions"]
    selected  = session["selected_answers"]

    score   = sum(1 for q, sel in zip(questions, selected) if sel == q["correct_answer"])
    summary = [
        {
            "question":        q["question"],
            "correct_answer":  q["correct_answer"],
            "selected_answer": sel if sel else "No Answer",
            "is_correct":      sel == q["correct_answer"]
        }
        for q, sel in zip(questions, selected)
    ]

    # Save score to persistent leaderboard
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            leaderboard = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leaderboard = []

    leaderboard.append({"username": username, "score": score})

    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, indent=4)

    # Instead of redirecting directly, render submit.html first
    return render_template("submit.html", username=username, score=score, questions=summary)
    
# ░█▀█░█░█░█▀█   leaderboard page
@app.route("/leaderboard")
def leaderboard():
    """Display the leaderboard."""
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            scores = json.load(f)
    except FileNotFoundError:
        scores = []

    scores = sorted(scores, key=lambda x: x["score"], reverse=True)

    return render_template("leaderboard.html", scores=scores)


# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)