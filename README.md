# AI Teaching Assistant

A platform to help school teachers, especially from rural areas to automate lesson planning, quiz creation, visual aid generation, and class scheduling using agentic AI (Google Gemini). Currently supports Marathi-language content.

---

## 🌟 Features

* ✍️ Generate lessons and quizzes in Marathi using Gemini API
* 🖼️ Generate topic-related visual aids (images)
* 🗓️ Schedule daily/weekly lesson generation tasks
* ☁️ Store generated content securely on Google Cloud Storage (GCS)
* ⚙️ CLI-first interface with clean modular Python code
* 🔜 Ready for future web UI (Flask/Streamlit)

---

## 🚀 Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/ai_teaching_assistant.git
cd ai_teaching_assistant
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your environment

* Set your **Gemini API key** (Google GenAI):

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

* (Optional) Edit `config/config.yaml` to store your API key and GCS bucket name

---


## 🧱 Project Structure

```
ai_teaching_assistant/
├── ai_teaching_assistant/     # Core app modules
│   ├── cli.py                 # Command-line interface
│   ├── gemini_client.py       # Handles Gemini API calls
│   ├── gcs_client.py          # Uploads content to GCS
│   ├── scheduler.py           # Periodic jobs (APScheduler)
│   └── utils.py               # Helper functions
├── config/
│   └── config.yaml            # App configuration (API keys, bucket)
├── tests/                     # Test suite
│   ├── test_gemini_client.py
├── requirements.txt
├── README.md
├── .gitignore
└── .github/workflows/
    └── python-app.yml         # GitHub Actions for CI
```

---

##  Testing

Run unit tests (if present):

```bash
pytest tests/
```

---

## 💠 Future Roadmap

* Streamlit-based interactive web interface
* Mobile-friendly lesson viewer
* Teacher feedback integration
* Offline content cache and syncing
