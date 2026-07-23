import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_create_user():
    response = client.post(
        "/users/",
        json={"username": "alice", "email": "alice@example.com"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "alice"

def test_create_post():
    # Create user
    client.post("/users/", json={"username": "alice", "email": "alice@example.com"})

    # Create post
    response = client.post(
        "/users/1/posts/",
        json={"content": "Hello world"}
    )
    assert response.status_code == 201
    assert response.json()["content"] == "Hello world"
    assert response.json()["user_id"] == 1

def test_follow_user_and_get_feed():
    # Create users
    client.post("/users/", json={"username": "alice", "email": "alice@example.com"}) # id 1
    client.post("/users/", json={"username": "bob", "email": "bob@example.com"})     # id 2

    # Alice posts
    client.post("/users/1/posts/", json={"content": "Alice post 1"})

    # Bob follows Alice
    follow_response = client.post("/users/2/follow/", json={"followee_id": 1})
    assert follow_response.status_code == 201

    # Bob gets feed
    feed_response = client.get("/users/2/feed/")
    assert feed_response.status_code == 200
    feed = feed_response.json()
    assert len(feed) == 1
    assert feed[0]["content"] == "Alice post 1"
    assert feed[0]["user_id"] == 1
