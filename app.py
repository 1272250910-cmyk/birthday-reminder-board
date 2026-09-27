from datetime import date, datetime
import os
import re

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

# In-memory list of dicts: {"name": str, "date": "YYYY-MM-DD"}
birthdays = []


def calculate_days_until(b_date: date, today: date) -> int:
    """Calculate days until the next birthday, wrapping to next year

    if it has already passed this year. Safely handles Feb 29.
    """
    try:
        bday_this_year = b_date.replace(year=today.year)
    except ValueError:
        bday_this_year = date(today.year, 2, 28)

    if bday_this_year < today:
        try:
            bday_next_year = b_date.replace(year=today.year + 1)
        except ValueError:
            bday_next_year = date(today.year + 1, 2, 28)
        return (bday_next_year - today).days

    return (bday_this_year - today).days


def get_short_commit_id() -> str:
    """Read running commit ID from RENDER_GIT_COMMIT env var (default: 'local')

    truncated to 7 characters.
    """
    return os.environ.get("RENDER_GIT_COMMIT", "local")[:7]


@app.route("/", methods=["GET"])
def index():
    today = date.today()
    all_birthdays = []
    this_month_birthdays = []

    for item in birthdays:
        b_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
        days_until = calculate_days_until(b_date, today)
        is_this_month = (b_date.month == today.month)

        record = {
            "name": item["name"],
            "date": item["date"],
            "days_until": days_until,
            "is_this_month": is_this_month,
        }
        all_birthdays.append(record)
        if is_this_month:
            this_month_birthdays.append(record)

    # Sort by soonest upcoming birthday (days_until ascending)
    all_birthdays.sort(key=lambda x: (x["days_until"], x["name"].lower()))
    this_month_birthdays.sort(
        key=lambda x: (x["days_until"], x["name"].lower())
    )

    return render_template(
        "index.html",
        all_birthdays=all_birthdays,
        this_month_birthdays=this_month_birthdays,
        current_month_name=today.strftime("%B"),
        commit_id=get_short_commit_id(),
    )


@app.route("/add", methods=["POST"])
def add_birthday():
    name = request.form.get("name", "")
    date_str = request.form.get("date", "")

    stripped_name = name.strip() if name else ""
    if not stripped_name:
        return "Error: Name cannot be empty.", 400

    stripped_date = date_str.strip() if date_str else ""
    if not stripped_date:
        return "Error: Date cannot be empty.", 400

    # Validate strict YYYY-MM-DD format
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", stripped_date):
        return "Error: Date must be in YYYY-MM-DD format.", 400

    try:
        datetime.strptime(stripped_date, "%Y-%m-%d").date()
    except ValueError:
        return "Error: Date is not a valid calendar date.", 400

    birthdays.append({"name": stripped_name, "date": stripped_date})
    return redirect(url_for("index"))


@app.route("/api/birthdays", methods=["GET"])
def api_birthdays():
    return jsonify(birthdays)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "commit": get_short_commit_id()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
