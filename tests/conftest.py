import os

os.environ["SKIP_APP_INIT"] = "1"

import pytest
from unittest.mock import MagicMock

from app import create_app


@pytest.fixture
def mock_rag_chain():
    chain = MagicMock()
    chain.invoke.side_effect = lambda payload: {
        "answer": f"Mock response to: {payload['input']}"
    }
    return chain


@pytest.fixture
def app(mock_rag_chain):
    return create_app(
        config_overrides={
            "TESTING": True,
            "JWT_SECRET_KEY": "test-jwt-secret",
            "SECRET_KEY": "test-flask-secret",
            "AUTH_USERNAME": "admin",
            "AUTH_PASSWORD": "password",
            "CHAT_RATE_LIMIT": "20 per minute",
        },
        rag_chain=mock_rag_chain,
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/login",
        json={"username": "admin", "password": "password"},
    )
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def strict_rate_limit_app(mock_rag_chain):
    return create_app(
        config_overrides={
            "TESTING": True,
            "JWT_SECRET_KEY": "test-jwt-secret",
            "SECRET_KEY": "test-flask-secret",
            "AUTH_USERNAME": "admin",
            "AUTH_PASSWORD": "password",
            "CHAT_RATE_LIMIT": "2 per minute",
        },
        rag_chain=mock_rag_chain,
    )
