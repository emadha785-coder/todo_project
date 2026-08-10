import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db

DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

TestingSession = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base.metadata.create_all(bind=engine)
def override_get_db():
    try:
        db = TestingSession()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_createUser():
    response = client.post(
        "/users", json={"email": "testing@gmail.com", "password": "12345"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testing@gmail.com"
    assert "id" in data
    assert "password" not in data


def test_create_duplicate_user():
    client.post("/users", json={"email":"duplicate@gmail.com", "password": "12345"})
    response = client.post("/users", json={"email":"duplicate@gmail.com", "password": "12345"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Email Already Registered!"


def test_login_success():
    client.post("/users", json={"email": "login_test@gmail.com", "password": "secret_pass"})

    response = client.post(
        "/login",
        data={"username": "login_test@gmail.com","password": "secret_pass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_task():
    client.post("/users", json={"email": "login_test@gmail.com", "password": "secret_pass"})
    response =client.post(
        "/login", data={"username":"login_test@gmail.com", "password": "secret_pass" }
    )
    assert response.status_code == 200
    tas_res = client.post("/tasks", json={"title": "Testing", "description":"updating", "is_completed": False},
                          headers={"Authorization":f"Bearer {response.json()["access_token"]}"})
    assert tas_res.status_code == 201
