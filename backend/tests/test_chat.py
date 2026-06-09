from unittest.mock import AsyncMock, patch


def test_chat_requires_auth(client):
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_chat_missing_message_field(auth_client):
    response = auth_client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_successful_ai_response(auth_client):
    mock_result = {
        "reply": "Photosynthesis is the process by which plants convert light into energy.",
        "sources": [],
        "highlighted_node_ids": [],
        "status": "done",
        "error": None,
    }
    with patch("apis.routers.chat._chat_graph") as mock_graph:
        mock_graph.ainvoke = AsyncMock(return_value=mock_result)
        response = auth_client.post("/chat", json={"message": "What is photosynthesis?"})

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == mock_result["reply"]
    assert "sources" in data
    assert "highlighted_node_ids" in data


def test_chat_failed_ai_response_error_status(auth_client):
    mock_result = {
        "status": "error",
        "reply": None,
        "sources": [],
        "highlighted_node_ids": [],
        "error": "Something went wrong",
    }
    with patch("apis.routers.chat._chat_graph") as mock_graph:
        mock_graph.ainvoke = AsyncMock(return_value=mock_result)
        response = auth_client.post("/chat", json={"message": "test"})

    assert response.status_code == 500


def test_chat_failed_ai_response_exception(auth_client):
    with patch("apis.routers.chat._chat_graph") as mock_graph:
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("AI service unavailable"))
        response = auth_client.post("/chat", json={"message": "test"})

    assert response.status_code == 500
