"""
Endpoint constants. Keeping paths here (instead of scattered string
literals in test files) means a URL change is a one-line fix.

We use https://reqres.in - a free, public "hosted REST-API for testing
and prototyping" - so this repo runs with zero credentials.
"""


class UsersEndpoints:
    LIST_USERS = "/users"
    SINGLE_USER = "/users/{id}"
    CREATE_USER = "/users"
    UPDATE_USER = "/users/{id}"
    DELETE_USER = "/users/{id}"


class AuthEndpoints:
    REGISTER = "/register"
    LOGIN = "/login"
