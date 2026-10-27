# AI Support Operations Copilot

An AI-powered customer support platform built with Python, Django REST Framework, Streamlit, Groq, and ChromaDB. The application helps support teams manage tickets, analyze customer issues, retrieve relevant knowledge, and generate customer-ready response drafts.

## Live Application

- **Streamlit Dashboard:** https://ai-support-operations-dashboard.onrender.com
- **Django REST API:** https://ai-support-operations-copilot.onrender.com
- **GitHub Repository:** https://github.com/Priyanshugitnegi/ai-support-operations-copilot

*The services are hosted separately. Availability may depend on the hosting platform's status.*

## Overview

Customer support teams spend time reviewing tickets, identifying the underlying issue, determining urgency, searching support documentation, and drafting responses.

The AI Support Operations Copilot streamlines these workflows through an authenticated dashboard connected to a Django REST API. It combines ticket management, AI-assisted analysis, structured output validation, and knowledge retrieval to help support teams work more efficiently.

## Features

### Authentication and Access Control
- User registration, login, and logout.
- Token-based authentication using Django REST Framework.
- User-specific ticket access.
- Ticket creation associated with the authenticated user.
- Analysis history restricted to tickets belonging to the authenticated user.

### Ticket Management
- Create and view support tickets.
- Update ticket status and priority.
- View ticket metrics and recent activity.
- Organize ticket information through a Streamlit dashboard.

### AI-Powered Workflows
- Summarize customer support issues.
- Identify ticket categories and priority levels.
- Generate recommended actions for support agents.
- Generate customer reply drafts for review.
- Validate structured AI outputs with Pydantic.

### Knowledge Retrieval
- Use ChromaDB for vector storage and semantic search.
- Retrieve relevant support knowledge to ground supported AI workflows.
- Manage support knowledge articles through Django Admin.
- Store ticket analyses for later review.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Django | Backend framework |
| Django REST Framework | REST API and authentication |
| Streamlit | Interactive support dashboard |
| Groq API | Large language model integration |
| ChromaDB | Vector storage and semantic retrieval |
| Pydantic | Structured data validation |
| PostgreSQL / Neon | Production database |
| SQLite | Local development database when configured |
| Requests | Dashboard-to-backend HTTP communication |
| Render | Application hosting |
| Git and GitHub | Version control |

## Architecture

```text
                 Support Agent
                       |
                       v
              Streamlit Dashboard
                       |
             Token-authenticated HTTP
                       |
                       v
             Django REST Framework
                       |
          +------------+------------+
          |            |            |
          v            v            v
     Authentication  Ticket       AI Workflows
                     Management       |
                                      v
                                  Groq API
                                      |
                           Structured AI Results
                                      |
                                      v
                              Analysis Storage

             Knowledge Retrieval
                       |
                       v
                    ChromaDB

             Persistent Application Data
                       |
                       v
                PostgreSQL / Neon
```

## Application Workflow

1. A user registers or signs in to the dashboard.
2. The dashboard sends authenticated requests to the Django REST API.
3. Django verifies the authentication token and restricts ticket access to the current user.
4. The user creates tickets, updates ticket details, or reviews existing tickets.
5. When requested, the AI workflow analyzes a ticket and returns structured insights.
6. The customer reply workflow generates a draft for the user to review.
7. Ticket data and supported analysis history are stored for subsequent access.

## API Endpoints

The backend exposes the following routes. Authentication endpoints are available under `/api/auth/`, while ticket resources use the `/api/` namespace.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register/` | Register an account |
| POST | `/api/auth/login/` | Authenticate a user |
| POST | `/api/auth/logout/` | Log out the authenticated user |
| GET | `/api/tickets/` | List the authenticated user's tickets |
| POST | `/api/tickets/` | Create a ticket |
| PATCH | `/api/tickets/{id}/` | Update ticket fields |
| POST | `/api/tickets/{id}/analyze/` | Analyze a ticket |
| POST | `/api/tickets/{id}/generate-reply/` | Generate a customer reply |
| GET | `/api/ticket-analyses/` | View accessible analysis history |
| GET | `/api/ticket-analyses/{id}/` | Retrieve an individual analysis |

The API requires authentication for protected resources. Available actions and response fields depend on the configured permissions and serializers.

## Local Development Setup

### Prerequisites

- Python 3.12
- Git
- A Groq API key
- A virtual environment

### 1. Clone the repository

```bash
git clone https://github.com/Priyanshugitnegi/ai-support-operations-copilot.git
cd ai-support-operations-copilot
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv venv312
.\venv312\Scripts\Activate.ps1
```

### 3. Install dependencies

If the repository contains `requirements.txt`, install the pinned project dependencies:

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root, beside `manage.py`. Use the variable names expected by the current application configuration.

At minimum, the backend settings require a Django secret key, and the AI integration requires a Groq API key.

Example development configuration:

```dotenv
DJANGO_SECRET_KEY=replace_with_a_local_secret
DJANGO_DEBUG=True
GROQ_API_KEY=replace_with_your_groq_api_key
```

Configure any additional database, allowed-host, or dashboard API variables required by your local setup.

**Never commit `.env` files, secret keys, API tokens, or database credentials.**

### 5. Apply migrations

```powershell
python manage.py migrate
```

### 6. Create an administrator account

```powershell
python manage.py createsuperuser
```

### 7. Start the backend

```powershell
python manage.py runserver
```

The backend will normally be available at `http://127.0.0.1:8000/`.

Django Admin is available at `http://127.0.0.1:8000/admin/`.

### 8. Start the Streamlit dashboard

Open a second terminal, activate the virtual environment, and run:

```powershell
python -m streamlit run streamlit_app.py
```

Open the local dashboard URL displayed in the terminal, normally `http://localhost:8501`.

Ensure `DJANGO_API_URL` points to the local backend API when running locally. Configure the dashboard's API token and other required variables according to the application settings.

## Testing

Run the Django test suite:

```powershell
python manage.py test
```

Check the Streamlit application's Python syntax:

```powershell
python -m py_compile streamlit_app.py
```

The latest recorded local verification completed with **9 Django tests passing** and no Python syntax errors in `streamlit_app.py`.

## Deployment

The application uses separate hosted services for the Django backend and Streamlit dashboard.

- Configure environment variables in the hosting platform rather than committing secrets.
- Set `DJANGO_DEBUG=False` in production.
- Configure production allowed hosts and HTTPS security settings.
- Use the production database configuration and apply Django migrations during deployment.
- Configure the dashboard to use the deployed backend URL.
- Confirm both services are healthy after deployment.

## Security Considerations

- Protected API endpoints use token authentication.
- Ticket querysets are restricted to the authenticated user.
- Ticket creation associates the ticket with its owner.
- Analysis history is filtered according to ticket ownership.
- Keep API keys, Django secrets, and service tokens out of source control.
- Review AI-generated customer responses before sending them.
- Verify permissions and production configuration whenever new endpoints are added.

## Future Improvements

- Role-based access for support agents, team leads, and administrators.
- Ticket assignment and SLA escalation.
- Advanced search, filtering, and pagination.
- AI output evaluation and regression testing.
- Monitoring for API latency, errors, and AI usage.
- Expanded analytics for ticket resolution and support performance.
- More comprehensive integration tests and automated deployment checks.

## Author

**Priyanshu Negi**

Python Backend Development | Django REST Framework | Generative AI

- GitHub: https://github.com/Priyanshugitnegi

---

*Built to explore the practical integration of backend APIs, authentication, AI-powered workflows, semantic retrieval, and interactive dashboards.*
