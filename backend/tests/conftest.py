import sys
import os
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_client():
    with TestClient(app) as c:
        email = f"test_{uuid4().hex[:8]}@test.com"
        resp = c.post("/auth/register", json={
            "name": "Test User",
            "email": email,
            "password": "Password123!"
        })
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        yield c
