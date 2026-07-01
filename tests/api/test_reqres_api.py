"""
API automation tests against the free public reqres.in sandbox API.

Demonstrates: Web/API automation, REST assertions, and negative testing -
CV bullets "Web & API Automation" and "REST API, Postman".
"""
import pytest

from src.api_automation.endpoints import UsersEndpoints


@pytest.mark.api
class TestUsersAPI:

    def test_list_users_returns_200_and_data(self, api_client):
        response = api_client.get(UsersEndpoints.LIST_USERS, params={"page": 2})
        assert response.status_code == 200
        assert "data" in response.json
        assert isinstance(response.json["data"], list)
        assert len(response.json["data"]) > 0

    def test_single_user_schema(self, api_client):
        response = api_client.get(UsersEndpoints.SINGLE_USER.format(id=2))
        assert response.status_code == 200
        user = response.json["data"]
        for field in ("id", "email", "first_name", "last_name"):
            assert field in user, f"Missing field '{field}' in user payload"

    def test_get_nonexistent_user_returns_404(self, api_client):
        response = api_client.get(UsersEndpoints.SINGLE_USER.format(id=999))
        assert response.status_code == 404

    def test_create_user(self, api_client):
        payload = {"name": "Hemant QA Bot", "job": "Principal SDET"}
        response = api_client.post(UsersEndpoints.CREATE_USER, json=payload)
        assert response.status_code == 201
        assert response.json["name"] == payload["name"]
        assert "id" in response.json
        assert "createdAt" in response.json

    def test_update_user(self, api_client):
        payload = {"job": "Lead Tech (QTE)"}
        response = api_client.put(UsersEndpoints.UPDATE_USER.format(id=2), json=payload)
        assert response.status_code == 200
        assert response.json["job"] == payload["job"]

    def test_delete_user(self, api_client):
        response = api_client.delete(UsersEndpoints.DELETE_USER.format(id=2))
        assert response.status_code == 204

    def test_response_time_within_sla(self, api_client):
        response = api_client.get(UsersEndpoints.LIST_USERS)
        assert response.elapsed_ms < 3000, f"API too slow: {response.elapsed_ms:.0f}ms"
