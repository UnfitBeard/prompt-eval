# 🧠 Prompt-Eval — AI-Powered Prompt Evaluation Platform

This project is a full-stack application that allows users to **evaluate, score, and manage prompt templates** for various domains such as software engineering, education, and content writing.
It integrates three major components:

- 🌐 **Frontend:** Angular (19) — Modern UI for users and admins.
- 🛠 **Backend:** Node.js + Express — Authentication, API endpoints, and business logic.
- 🤖 **AI Model:** Python + scikit-learn — Machine learning scoring engine (served separately).

---

## 📁 Project Structure

```
.
├── AI_model/                # Python scoring model and artifacts
│   ├── scoring_artifacts/   # Trained model, metadata & inference script
│   ├── requirements.txt     # Python dependencies
│   ├── DOCKERFILE           # Optional containerization for model
│   └── my_venv/             # Python virtual environment (local)
│
├── backend/                 # Node.js + Express REST API
│   ├── src/
│   │   ├── Controllers/
│   │   │   ├── Auth/        # Login & registration logic
│   │   │   └── Prompts/    # Template & evaluation endpoints
│   │   ├── Models/         # Mongoose schemas
│   │   ├── Routes/         # Express route definitions
│   │   └── Utils/          # Helper functions (e.g. JWT)
│   ├── .env                # Environment variables
│   ├── package.json
│   └── server.ts           # Entry point
│
└── promptEval/              # Angular Frontend (v19)
    ├── src/app/Components/  # UI components (login, dashboard, templates, etc.)
    ├── src/app/Guards/     # Auth guards for routes
    ├── src/app/Services/   # HTTP services for API & AI calls
    ├── angular.json
    ├── package.json
    └── README.md
```

---

## ⚡ 1. Frontend — Angular

### 🧭 Features

- 🔐 Authentication (Login/Register)
- 🧰 Admin dashboard to manage templates
- 📝 Template library with filters, ratings, and copy-to-clipboard
- 🔎 Full-text search and filtering by difficulty, rating, and domain

### ▶️ Run Frontend

```bash
cd promptEval
npm install
npm start     # Runs on http://localhost:4200
```

---

## 🛠 2. Backend — Node.js + Express

### 🧭 Features

- 🌍 RESTful APIs for authentication, templates, and evaluation
- 🍪 Secure cookies with JWT for login sessions
- 🌐 CORS configuration for Angular frontend
- 📡 Connects to MongoDB Atlas for persistent storage

### ▶️ Run Backend

```bash
cd backend
npm install
npm run dev   # Runs on http://localhost:10000
```

### ⚙️ Required `.env` (backend/.env)

```env
PORT=10000
MONGO_URI=<your_mongodb_atlas_uri>
JWT_SECRET=<your_secret_key>
```

> Make sure your IP is whitelisted in MongoDB Atlas.

---

## 🤖 3. AI Model — Python (scikit-learn)

The AI model scores prompts based on clarity, context, relevance, specificity, and creativity.
It uses a pre-trained Ridge Regressor to generate a composite score between 0 and 10.

### 📂 Key Files

- `scoring_artifacts/infer_ridge.py` — Loads the model & performs inference
- `scoring_artifacts/regressor.joblib` — Serialized trained model
- `scoring_artifacts/meta.json` — Metadata used during inference

### ▶️ Run Model

```bash
cd AI_model
python3 -m venv my_venv
source my_venv/bin/activate
pip install -r requirements.txt

# Run the Flask or FastAPI model server (not shown, but typically)
python scoring_artifacts/infer_ridge.py
```

---

## 🔗 Integration Flow

1. 🧑‍💻 User logs in through Angular frontend.
2. 🌐 Angular calls backend API at `http://localhost:10000/api/v1/...`.
3. 🧠 When evaluating a prompt, backend forwards the text to the Python model endpoint (e.g., `http://localhost:5000/evaluate`).
4. 📊 Model returns a JSON score, which backend processes and returns to frontend.
5. 🧾 Frontend displays scores and updates templates dynamically.

---

## 🐳 Optional — Dockerize AI Model

The `AI_model/DOCKERFILE` can be used to containerize the Python scoring service:

```bash
cd AI_model
docker build -t prompt-eval-model .
docker run -p 5000:5000 prompt-eval-model
```

---

## 🚀 Deployment Notes

- Frontend can be deployed on **Vercel** or **Netlify**.
- Backend can be deployed on **Render**, **Railway**, or **Azure App Service**.
- Python model can be deployed on **Render**, **AWS Lambda**, or **Docker + VM**.
- Ensure proper **CORS** configuration between deployed URLs.
- Use environment variables for API keys and secrets.

---

## 📝 TODO / Future Work

- ✅ Fix Angular clipboard copy functionality
- 🔄 Improve error handling for Gemini API errors
- 🧠 Add fine-tuning options for the scoring model
- 📈 Add analytics dashboard for prompt performance
- 🌐 Add multi-user role support

---

## 👨‍💻 Authors

- **George Njunge** — Full-stack Developer & AI Engineer

---

## 📄 License

MIT License © 2025 Prompt-Eval Project
    