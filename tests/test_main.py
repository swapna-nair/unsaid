from fastapi.testclient import TestClient
from src.main import app, users_db, followers_db, following_db, posts_db, feed_cache, celebrity_outbox, CELEBRITY_FOLLOWER_THRESHOLD

client = TestClient(app)

def setup_function():
    # Clear DB before each test
    users_db.clear()
    followers_db.clear()
    following_db.clear()
    posts_db.clear()
    feed_cache.clear()
    celebrity_outbox.clear()

def test_create_user():
    response = client.post("/users", json={"username": "alice"})
    assert response.status_code == 201
    assert "user_id" in response.json()
    assert response.json()["username"] == "alice"

def test_follow_user():
    res1 = client.post("/users", json={"username": "alice"})
    user1_id = res1.json()["user_id"]

    res2 = client.post("/users", json={"username": "bob"})
    user2_id = res2.json()["user_id"]

    res = client.post(f"/users/{user1_id}/follow/{user2_id}")
    assert res.status_code == 200

    assert user2_id in following_db[user1_id]
    assert user1_id in followers_db[user2_id]

def test_fanout_on_write_regular_user():
    res1 = client.post("/users", json={"username": "alice"})
    alice_id = res1.json()["user_id"]

    res2 = client.post("/users", json={"username": "bob"})
    bob_id = res2.json()["user_id"]

    client.post(f"/users/{alice_id}/follow/{bob_id}")

    # Bob (regular user) creates a post
    post_res = client.post("/posts", json={"user_id": bob_id, "content": "Hello Alice!"})
    assert post_res.status_code == 201
    post_id = post_res.json()["post_id"]

    # Check Alice's feed cache directly (should be pushed)
    assert post_id in feed_cache[alice_id]

    # Fetch feed via API
    feed_res = client.get(f"/feed/{alice_id}")
    assert feed_res.status_code == 200
    assert len(feed_res.json()) == 1
    assert feed_res.json()[0]["post_id"] == post_id

def test_fanout_on_read_celebrity():
    res1 = client.post("/users", json={"username": "alice"})
    alice_id = res1.json()["user_id"]

    res2 = client.post("/users", json={"username": "celeb"})
    celeb_id = res2.json()["user_id"]

    client.post(f"/users/{alice_id}/follow/{celeb_id}")

    # Force Celeb to be a celebrity
    followers_db[celeb_id] = ["dummy_id"] * CELEBRITY_FOLLOWER_THRESHOLD

    # Celeb creates a post
    post_res = client.post("/posts", json={"user_id": celeb_id, "content": "Hello World!"})
    assert post_res.status_code == 201
    post_id = post_res.json()["post_id"]

    # Check Alice's feed cache directly (should NOT be pushed)
    assert post_id not in feed_cache.get(alice_id, [])

    # Check celebrity outbox
    assert post_id in celebrity_outbox[celeb_id]

    # Fetch feed via API (should pull on read)
    feed_res = client.get(f"/feed/{alice_id}")
    assert feed_res.status_code == 200
    assert len(feed_res.json()) == 1
    assert feed_res.json()[0]["post_id"] == post_id
