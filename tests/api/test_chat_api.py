"""Tests for chat API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from enterprise_ai.main import app

client = TestClient(app)


def test_chat_query_endpoint():
    """Test chat query payload acceptance and response structure."""
    fake_query_id = uuid.uuid4()
    mock_result = {
        "query_id": str(fake_query_id),
        "question": "What is the total revenue in fiscal year 2023?",
        "answer": "Total revenue was $100M.",
        "citations": {"sources": []},
        "latency_ms": 120.5,
    }

    with patch(
        "enterprise_ai.services.chat_service.ChatService.execute_query",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        payload = {
            "question": "What is the total revenue in fiscal year 2023?",
            "llm_provider": "ollama",
        }
        response = client.post("/api/v1/chat/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["question"] == payload["question"]
        assert data["data"]["query_id"] == str(fake_query_id)
        assert data["data"]["answer"] == "Total revenue was $100M."
