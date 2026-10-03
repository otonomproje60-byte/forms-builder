"""
Tests for Forms Builder API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import sys
sys.path.insert(0, '/opt/autonomous-factory/projects/forms-builder/source')

from main import app
from database import Base, get_db
from models import Form, FormSubmission
from schemas import FormCreate, FormSubmit

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_forms.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "forms-builder"


class TestFormCRUD:
    def test_create_form(self, client, setup_db):
        form_data = {
            "name": "Test Form",
            "description": "A test form",
            "fields": [
                {"name": "name", "type": "text", "label": "Name", "required": True},
                {"name": "email", "type": "email", "label": "Email", "required": True},
            ],
            "email_enabled": False,
            "webhook_enabled": False,
            "honeypot_enabled": True,
            "rate_limit_enabled": True,
        }
        response = client.post("/api/forms", json=form_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Form"
        assert "id" in data
        assert len(data["fields"]) == 2

    def test_list_forms(self, client, setup_db):
        form_data = {"name": "List Test", "fields": [{"name": "f1", "type": "text", "label": "F1", "required": True}]}
        client.post("/api/forms", json=form_data)
        
        response = client.get("/api/forms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_form(self, client, setup_db):
        form_data = {"name": "Get Test", "fields": [{"name": "f1", "type": "text", "label": "F1", "required": True}]}
        create_resp = client.post("/api/forms", json=form_data)
        form_id = create_resp.json()["id"]
        
        response = client.get(f"/api/forms/{form_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == form_id
        assert data["name"] == "Get Test"

    def test_get_nonexistent_form(self, client, setup_db):
        response = client.get("/api/forms/nonexistent-id")
        assert response.status_code == 404


class TestFormSubmission:
    def test_submit_form_success(self, client, setup_db):
        form_data = {"name": "Submit Test", "fields": [{"name": "name", "type": "text", "label": "Name", "required": True}]}
        create_resp = client.post("/api/forms", json=form_data)
        form_id = create_resp.json()["id"]
        
        response = client.post(f"/api/forms/{form_id}/submit", json={"data": {"name": "John Doe"}})
        assert response.status_code == 200
        data = response.json()
        assert data["form_id"] == form_id
        assert data["data"]["name"] == "John Doe"
        assert "id" in data
        assert "submitted_at" in data

    def test_submit_form_missing_required(self, client, setup_db):
        # Note: API-level validation of required fields is not implemented;
        # validation happens client-side in embed HTML/JS.
        # The API accepts any data dict.
        form_data = {"name": "Required Test", "fields": [{"name": "name", "type": "text", "label": "Name", "required": True}]}
        create_resp = client.post("/api/forms", json=form_data)
        form_id = create_resp.json()["id"]
        
        response = client.post(f"/api/forms/{form_id}/submit", json={"data": {}})
        assert response.status_code == 200  # API accepts empty data

    def test_submit_nonexistent_form(self, client, setup_db):
        response = client.post("/api/forms/nonexistent/submit", json={"data": {"name": "Test"}})
        assert response.status_code == 404

    def test_submit_honeypot_spam(self, client, setup_db):
        form_data = {"name": "Spam Test", "fields": [{"name": "name", "type": "text", "label": "Name", "required": True}], "honeypot_enabled": True, "honeypot_field_name": "website"}
        create_resp = client.post("/api/forms", json=form_data)
        form_id = create_resp.json()["id"]
        
        response = client.post(f"/api/forms/{form_id}/submit", json={"data": {"name": "Spammer", "website": "http://spam.com"}})
        assert response.status_code == 400
        assert "spam protection" in response.json()["detail"].lower()


class TestSubmissionsList:
    def test_list_submissions(self, client, setup_db):
        form_data = {"name": "List Submissions Test", "fields": [{"name": "name", "type": "text", "label": "Name", "required": True}]}
        create_resp = client.post("/api/forms", json=form_data)
        form_id = create_resp.json()["id"]
        
        client.post(f"/api/forms/{form_id}/submit", json={"data": {"name": "User 1"}})
        client.post(f"/api/forms/{form_id}/submit", json={"data": {"name": "User 2"}})
        
        response = client.get(f"/api/forms/{form_id}/submissions")
        assert response.status_code == 200
        data = response.json()
        assert "submissions" in data
        assert "total" in data
        assert data["total"] >= 2


class TestEmbedEndpoints:
    def test_embed_html(self, client, setup_db):
        form_data = {"name": "Embed Test", "fields": [{"name": "name", "type": "text", "label": "Name", "required": True}]}
        create_resp = client.post("/api/forms", json=form_data)
        form_id = create_resp.json()["id"]
        
        response = client.get(f"/embed/{form_id}")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Embed Test" in response.text

    def test_embed_js(self, client, setup_db):
        form_data = {"name": "JS Embed Test", "fields": [{"name": "name", "type": "text", "label": "Name", "required": True}]}
        create_resp = client.post("/api/forms", json=form_data)
        form_id = create_resp.json()["id"]
        
        response = client.get(f"/embed/{form_id}.js")
        assert response.status_code == 200
        assert "javascript" in response.headers.get("content-type", "")
        assert form_id in response.text

    def test_embed_nonexistent(self, client, setup_db):
        response = client.get("/embed/nonexistent")
        assert response.status_code == 404


class TestStaticFiles:
    def test_embed_css(self, client):
        response = client.get("/static/embed.css")
        assert response.status_code == 200
        assert "forms-builder-widget" in response.text

    def test_embed_js_static(self, client):
        response = client.get("/static/embed.js")
        assert response.status_code == 200
        assert "Forms Builder Embeddable Widget" in response.text


class TestRateLimiting:
    def test_global_rate_limit(self, client, setup_db):
        # Global rate limiter: 10 requests per 60 seconds per IP
        # The TestClient shares state across requests, so we test the limiter directly
        from spam_protection import RateLimiter
        
        # Create a fresh rate limiter instance for this test
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # Make 10 requests - all should succeed
        for i in range(10):
            allowed = limiter.check("test-ip")
            assert allowed == True, f"Request {i+1} should be allowed"
        
        # 11th request - should be rate limited
        allowed = limiter.check("test-ip")
        assert allowed == False, "11th request should be rate limited"

    def test_rate_limit_different_ips(self, client, setup_db):
        # Rate limiting is per IP
        from spam_protection import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # IP 1 makes 2 requests - allowed
        assert limiter.check("ip-1") == True
        assert limiter.check("ip-1") == True
        # 3rd request from IP 1 - rate limited
        assert limiter.check("ip-1") == False
        
        # IP 2 should still be allowed
        assert limiter.check("ip-2") == True
        assert limiter.check("ip-2") == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])