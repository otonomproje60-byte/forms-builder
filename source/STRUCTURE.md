# Forms Builder - FastAPI Application

## Project Structure
```
source/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings/configuration
│   ├── database.py          # SQLite + SQLAlchemy setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── form.py          # Form model
│   │   ├── submission.py    # Submission model
│   │   └── field.py         # Field model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── form.py          # Pydantic schemas for forms
│   │   ├── submission.py    # Pydantic schemas for submissions
│   │   └── field.py         # Pydantic schemas for fields
│   ├── api/
│   │   ├── __init__.py
│   │   ├── forms.py         # Form endpoints
│   │   ├── submissions.py   # Submission endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email.py         # Email notification service
│   │   ├── webhook.py       # Webhook notification service
│   │   └── spam.py          # Spam protection service
│   └── utils/
│       ├── __init__.py
│       └── embed.py         # Embeddable JS snippet generator
├── requirements.txt
└── Dockerfile
```