# forms-builder
FastAPI-based lightweight form endpoint/builder

## Development
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker
```bash
docker compose up -d
```

## API Endpoints
- `POST /api/forms` - Create a new form
- `GET /api/forms/{form_id}` - Get form details
- `POST /api/forms/{form_id}/submit` - Submit form data
- `GET /api/forms/{form_id}/submissions` - List submissions (admin)
- `GET /healthz` - Health check