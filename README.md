# AI Support Operations Copilot

An AI-powered support operations system that analyzes customer support tickets, retrieves relevant knowledge articles using Retrieval-Augmented Generation (RAG), and recommends actionable next steps for support teams.

## Overview

Support teams often spend significant time categorizing tickets, identifying customer issues, searching internal documentation, and deciding what action to take next.

The AI Support Operations Copilot helps streamline this workflow by combining a Django REST API, a Large Language Model (LLM), and semantic search over a knowledge base.

## Features

- **AI Ticket Analysis:** Generate ticket summaries, identify customer issues, and recommend next steps.
- **Ticket Classification:** Suggest ticket categories and priority levels.
- **Retrieval-Augmented Generation (RAG):** Retrieve relevant support articles from a knowledge base to ground AI-generated recommendations.
- **Semantic Search:** Use ChromaDB to find relevant articles based on meaning rather than exact keyword matches.
- **Knowledge Base Management:** Create and manage support articles through Django Admin.
- **Analysis History:** Store ticket analyses for later review.
- **Structured AI Outputs:** Validate AI-generated results using Pydantic.
- **Automated Tests:** Test core ticket-analysis and knowledge-retrieval behavior.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Django | Backend framework |
| Django REST Framework | REST API |
| Groq API | LLM-powered ticket analysis |
| ChromaDB | Vector storage and semantic retrieval |
| Pydantic | Structured output validation |
| SQLite | Development database |
| Streamlit | Planned Python-based user interface |

## Architecture

1. A support ticket is submitted through the API.
2. The application searches the knowledge base for relevant support articles.
3. Retrieved context is provided to the LLM alongside the ticket details.
4. The LLM generates a structured ticket analysis.
5. Pydantic validates the response.
6. The analysis is saved in the database for future review.

```text
Support Ticket
     |
     v
Django REST API
     |
     v
Knowledge Retrieval -----> ChromaDB
     |                       |
     <---- Relevant Articles
     |
     v
Groq LLM
     |
     v
Pydantic Validation
     |
     v
Saved Ticket Analysis
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/tickets/` | List tickets |
| POST | `/api/tickets/` | Create a ticket |
| POST | `/api/tickets/{id}/analyze/` | Analyze a ticket |
| GET | `/api/ticket-analyses/` | View analysis history |
| GET | `/api/ticket-analyses/{id}/` | Retrieve an individual analysis |

## Getting Started

### Prerequisites

- Python 3.12
- Git
- A Groq API key

### 1. Clone the repository

```bash
git clone https://github.com/Priyanshugitnegi/ai-support-operations-copilot.git
cd ai-support-operations-copilot
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv venv312
.\venv312\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install Django djangorestframework groq pydantic python-dotenv chromadb
```

### 4. Configure environment variables

Create a `.env` file in the project root, beside `manage.py`:

```env
DJANGO_SECRET_KEY=replace_with_a_local_secret_key
DJANGO_DEBUG=True
GROQ_API_KEY=replace_with_your_groq_api_key
```

Use your own secret values. Never commit `.env` or expose API keys.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

### 7. Start the backend

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/admin/` to manage knowledge articles and `http://127.0.0.1:8000/api/tickets/` to access the ticket API.

## Testing

Run the automated test suite:

```bash
python manage.py test
```

The current test suite covers knowledge article retrieval and core ticket-analysis behavior using mocked external services.

## Current Status

The backend MVP includes ticket management, LLM-powered analysis, knowledge-base retrieval, persistent vector storage, analysis history, and automated tests.

The Streamlit dashboard, production authentication, deployment hardening, and additional operational analytics are planned improvements.

## Security Notes

- API keys and Django secrets belong in environment variables.
- The development database and vector store are local artifacts and are not committed.
- Configure authentication and permissions before exposing the API publicly.
- Set `DJANGO_DEBUG=False` and configure production security settings before deployment.
- Review AI-generated recommendations before taking customer-facing actions.

## Future Improvements

- Streamlit support operations dashboard.
- Ticket escalation rules and operational analytics.
- More comprehensive integration tests.
- Improved evaluation of retrieval quality and AI output consistency.
- Production deployment with appropriate authentication and monitoring.

## Author

**Priyanshu Negi**

GitHub: https://github.com/Priyanshugitnegi
