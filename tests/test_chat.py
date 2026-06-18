def test_rate_limit_blocks_excess_requests(strict_rate_limit_app, mock_rag_chain):
    client = strict_rate_limit_app.test_client()
    login_response = client.post(
        "/login",
        json={"username": "admin", "password": "password"},
    )
    headers = {"Authorization": f"Bearer {login_response.get_json()['access_token']}"}

    first = client.post("/get", data={"msg": "first"}, headers=headers)
    second = client.post("/get", data={"msg": "second"}, headers=headers)
    third = client.post("/get", data={"msg": "third"}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert mock_rag_chain.invoke.call_count == 2


def test_conversation_memory_persists_within_session(client, auth_headers, mock_rag_chain):
    first = client.post(
        "/get",
        data={"msg": "My name is Alice"},
        headers=auth_headers,
    )
    second = client.post(
        "/get",
        data={"msg": "What is my name?"},
        headers=auth_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    first_input = mock_rag_chain.invoke.call_args_list[0][0][0]["input"]
    second_input = mock_rag_chain.invoke.call_args_list[1][0][0]["input"]

    assert first_input == "My name is Alice"
    assert "My name is Alice" in second_input
    assert "What is my name?" in second_input

    with client.session_transaction() as flask_session:
        assert len(flask_session["chat_history"]) == 2
        assert flask_session["chat_history"][0]["user"] == "My name is Alice"
        assert flask_session["chat_history"][1]["user"] == "What is my name?"
