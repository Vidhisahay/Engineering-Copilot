def test_login_success(client):
    response = client.post(
        "/login",
        json={"username": "admin", "password": "password"},
    )

    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_login_invalid_credentials(client):
    response = client.post(
        "/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.get_json()["msg"] == "Invalid username or password"


def test_chat_without_jwt(client):
    response = client.post("/get", data={"msg": "hello"})

    assert response.status_code == 401


def test_chat_with_valid_jwt(client, auth_headers):
    response = client.post("/get", data={"msg": "hello"}, headers=auth_headers)

    assert response.status_code == 200
    assert "Mock response to: hello" in response.get_data(as_text=True)


def test_chat_with_invalid_jwt(client):
    response = client.post(
        "/get",
        data={"msg": "hello"},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 422
