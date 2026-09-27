# Birthday Reminder Board

A dynamic, server-rendered Flask web application built and delivered through Git and an automated GitHub Actions CI/CD pipeline to Render.

---

## 📌 Project Overview

The **Birthday Reminder Board** allows users to record birthdays and track upcoming celebrations in real time. All business logic, month calculations, and sorting are executed entirely on the server side:

- **Server-Side Rendering (Jinja2)**: Server generates the dynamic HTML views upon every request.
- **"This Month" Highlights**: Automatically filters and highlights individuals celebrating their birthday in the current calendar month.
- **Sorted by Soonest Upcoming**: Computes days remaining until each person's next birthday (properly wrapping past birthdays to the following calendar year and safely handling February 29 leap years).
- **JSON API**: Exposes `/api/birthdays` returning the full dataset as JSON.
- **Health Check Endpoint**: Provides `/health` returning `{"status": "ok", "commit": "<short_sha>"}` for automated deployment verification.
- **Git Commit Tracking**: Displays the running commit SHA in the footer (read from `RENDER_GIT_COMMIT` or defaulting to `local`, truncated to 7 characters).
- **Security**: Auto-escapes user input to prevent Cross-Site Scripting (XSS).

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Language & Framework** | Python 3.12 / Flask |
| **Templating Engine** | Jinja2 |
| **WSGI Server** | Gunicorn |
| **Testing Framework** | Pytest (20 automated unit & integration tests) |
| **Linter / Code Quality** | Flake8 |
| **Version Control & CI/CD** | Git, GitHub, GitHub Actions |
| **Cloud Hosting** | Render (Web Service) |

---

## 🏗️ Architecture & CI/CD Pipeline Flow

```
+---------------+     +--------------+     +-------------------+     +------------------+     +--------------------+
|   Developer   |     | GitHub Push  |     |   GitHub Actions  |     |   GitHub Actions |     |    Render Cloud    |
| (Code in IDE) | --> | (main / PR)  | --> |     (CI Stage)    | --> |    (CD Stage)    | --> |  (Live Production) |
+---------------+     +--------------+     +-------------------+     +------------------+     +--------------------+
                                                     |                         |                        |
                                           +---------+---------+               |                +-------+-------+
                                           | - Check code style|               |                | Pull passing  |
                                           |   via flake8      |               |                | commit & run  |
                                           | - Run 20 pytest   |               |                | gunicorn app  |
                                           |   unit tests      |               |                +---------------+
                                           +-------------------+               |                        |
                                                     |                         |                        v
                                                     v (If all pass)           v (Triggers Deploy Hook) +---------------+
                                             [Build & Test Green] -------> [Deploy to Render] ------>   | Live URL with |
                                                                                                    | new Commit ID |
                                                                                                    +---------------+
```

### Pipeline Stages
1. **Lint Stage**: Executes `flake8 --max-line-length=120 --exclude=venv .` to ensure PEP 8 compliance.
2. **Test Stage**: Runs `pytest -v` executing 20 automated tests validating input handling, error responses, leap year math, and route responses.
3. **Deploy Stage (CD)**: On push to `main`, triggers Render deployment via a secure webhook hook: `curl -fsS -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}&ref=${{ github.sha }}"`.
4. **Verification**: Live site serves `/health` and the page footer renders the exact 7-character commit SHA that passed the pipeline.

---

## 📂 Project Structure

```
birthday-reminder-board/
├── .github/
│   └── workflows/
│       └── ci-cd.yml         # GitHub Actions automated CI/CD pipeline
├── templates/
│   └── index.html            # Server-rendered Jinja2 template with responsive UI
├── app.py                    # Main Flask application with business logic & routes
├── test_app.py               # Comprehensive pytest test suite (20 tests)
├── requirements.txt          # Pinned dependencies (Flask, Gunicorn, Pytest, Flake8)
├── .gitignore                # Excludes virtual environments, caches, and secrets
└── README.md                 # Project documentation and deployment guide
```

---

## 🔌 API Endpoints

The Birthday Reminder Board provides the following API endpoints:

### 1. `GET /api/birthdays`
Returns all registered birthdays as a JSON list.
- **Status**: `200 OK`
- **Example command**:
  ```bash
  curl http://localhost:5000/api/birthdays
  ```
- **Example response**:
  ```json
  [
    {"name": "Alice Smith", "date": "1995-10-25"},
    {"name": "Bob Jones", "date": "1992-05-15"}
  ]
  ```

### 2. `GET /api/birthdays/<name>`
Returns a single matching birthday as JSON. Name matching is case-insensitive and trims leading/trailing whitespace.
- **Success (`200 OK`)**:
  ```bash
  curl http://localhost:5000/api/birthdays/Alice%20Smith
  ```
  Returns:
  ```json
  {"name": "Alice Smith", "date": "1995-10-25"}
  ```
- **Not Found (`404 Not Found`)**:
  When no matching birthday exists, it returns HTTP `404` with `{"error": "Birthday not found"}`:
  ```bash
  curl -i http://localhost:5000/api/birthdays/Nonexistent
  ```
  Returns:
  ```json
  {"error": "Birthday not found"}
  ```

### 3. `GET /health`
Returns the application health status and the 7-character commit ID (from `RENDER_GIT_COMMIT` or defaulting to `local`).
- **Status**: `200 OK`
- **Example command**:
  ```bash
  curl http://localhost:5000/health
  ```
- **Example response**:
  ```json
  {"status": "ok", "commit": "local"}
  ```

---

## 🚀 Running Locally

### 1. Prerequisites
- Python 3.9+ (or Python 3.12)
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone or navigate to the project directory
cd birthday-reminder-board

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

### 3. Run Quality Gates (Lint & Tests)
```bash
# Run Flake8 linter
flake8 app.py test_app.py

# Run Pytest suite
pytest -v
```

### 4. Run the Application
```bash
# Respects PORT environment variable (default: 5000)
# Note: On macOS Monterey+, port 5000 may be used by AirPlay Receiver. Use PORT=5001 if needed.
PORT=5001 python app.py
```
Open [http://localhost:5001](http://localhost:5001) in your browser.

---

## 🌐 Deploying to Render with GitHub Actions

1. **Push Code to GitHub**: Create a public repository on your personal GitHub account and push the code to `main`.
2. **Create Web Service on Render**:
   - Log into [Render](https://render.com) using your GitHub account.
   - Click **New +** -> **Web Service** -> Connect your `birthday-reminder-board` repository.
   - Configure the service:
     - **Runtime / Language**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Auto-Deploy**: Set to **No / Off** (GitHub Actions handles deployments).
     - **Health Check Path**: `/health`
3. **Configure Deploy Hook**:
   - In Render, navigate to **Settings** -> **Deploy Hook**.
   - Copy the Deploy Hook URL.
4. **Add GitHub Secret**:
   - In your GitHub repo, go to **Settings** -> **Secrets and variables** -> **Actions**.
   - Create a new repository secret:
     - **Name**: `RENDER_DEPLOY_HOOK`
     - **Secret**: Paste the copied Render deploy hook URL.
5. **Trigger Deployment**:
   - Push any commit to `main`.
   - Monitor the **Actions** tab on GitHub: tests and linter run first, and only upon success is the Render deploy triggered.

---

## 🛡️ Failure Demo (Quality Gate Proof)

To verify that the CI pipeline prevents broken code from reaching production:
1. Create a feature branch: `git checkout -b test-failure`
2. Introduce a failing test in `test_app.py` (e.g., change `assert response.status_code == 200` to `== 500`).
3. Commit and push: `git push origin test-failure`.
4. Create a Pull Request into `main`.
5. GitHub Actions will fail the `test` job with a red mark, and the `deploy` job will be skipped completely, ensuring zero downtime and preventing broken code from going live.
