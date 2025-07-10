import pytest
from fastapi.testclient import TestClient
from datetime import datetime

def test_create_document(client):
    response = client.post(
        "/documents/",
        json={
            "title": "Test Document",
            "content": "Test content",
            "file_path": "/test/path",
            "file_type": "txt"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["content"] == "Test content"
    assert "id" in data

def test_get_document(client):
    # First create a document
    create_response = client.post(
        "/documents/",
        json={
            "title": "Test Document",
            "content": "Test content",
            "file_path": "/test/path",
            "file_type": "txt"
        }
    )
    doc_id = create_response.json()["id"]

    # Then get it
    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["id"] == doc_id

def test_get_documents_with_search(client):
    # Create multiple documents
    client.post(
        "/documents/",
        json={
            "title": "Python Guide",
            "content": "Python programming content",
            "file_path": "/test/path1",
            "file_type": "txt"
        }
    )
    client.post(
        "/documents/",
        json={
            "title": "Java Guide",
            "content": "Java programming content",
            "file_path": "/test/path2",
            "file_type": "txt"
        }
    )

    # Search for Python documents
    response = client.get("/documents/?search=Python")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Python Guide"

def test_update_document(client):
    # First create a document
    create_response = client.post(
        "/documents/",
        json={
            "title": "Test Document",
            "content": "Test content",
            "file_path": "/test/path",
            "file_type": "txt"
        }
    )
    doc_id = create_response.json()["id"]

    # Update it
    response = client.put(
        f"/documents/{doc_id}",
        json={
            "title": "Updated Document",
            "content": "Updated content"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Document"
    assert data["content"] == "Updated content"

def test_delete_document(client):
    # First create a document
    create_response = client.post(
        "/documents/",
        json={
            "title": "Test Document",
            "content": "Test content",
            "file_path": "/test/path",
            "file_type": "txt"
        }
    )
    doc_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/documents/{doc_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/documents/{doc_id}")
    assert get_response.status_code == 404 