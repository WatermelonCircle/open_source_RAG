"""
Test Basic FastAPI Application

This test verifies that our FastAPI application starts correctly and responds 
to basic requests. We test:
1. Health check endpoint returns correct status
2. Root endpoint returns HTML content
3. Application can be imported without errors

Why this test is important:
- Ensures FastAPI is configured correctly
- Verifies basic routing works
- Confirms the app can start without import errors
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint returns 200 and correct status"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    print("✅ Health check endpoint working correctly")

def test_root_endpoint():
    """Test the root endpoint returns HTML content"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "RAG Document Chat" in response.text
    assert "Upload Documents" in response.text
    print("✅ Root endpoint serving HTML correctly")

def test_app_title():
    """Test that FastAPI app has correct title"""
    assert app.title == "RAG Webapp"
    assert app.description == "Upload PDFs and chat with documents"
    print("✅ FastAPI app configured with correct metadata")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])