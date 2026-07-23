from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import time
import uuid

app = FastAPI(title="News Feed API")

# Simulated Databases (In-Memory for demonstration)
# In reality, this would be PostgreSQL/Cassandra/Redis
users_db: Dict[str, dict] = {}
followers_db: Dict[str, List[str]] = {} # user_id -> list of follower_ids
following_db: Dict[str, List[str]] = {} # user_id -> list of following_ids
posts_db: Dict[str, dict] = {}
feed_cache: Dict[str, List[str]] = {} # user_id -> list of post_ids (fanout-on-write cache)
celebrity_outbox: Dict[str, List[str]] = {} # user_id (celebrity) -> list of post_ids

CELEBRITY_FOLLOWER_THRESHOLD = 1000

# Models
class UserCreate(BaseModel):
    username: str

class PostCreate(BaseModel):
    user_id: str
    content: str
    media_urls: Optional[List[str]] = []

class PostResponse(BaseModel):
    post_id: str
    user_id: str
    content: str
    created_at: float
    media_urls: List[str]

# --- Helper Functions ---
def is_celebrity(user_id: str) -> bool:
    """Determine if a user is a celebrity based on follower count."""
    followers = followers_db.get(user_id, [])
    return len(followers) >= CELEBRITY_FOLLOWER_THRESHOLD

def fanout_post(post_id: str, author_id: str):
    """Simulates the background worker consuming Kafka event."""
    if is_celebrity(author_id):
        # Fanout-on-read for celebrities
        if author_id not in celebrity_outbox:
            celebrity_outbox[author_id] = []
        celebrity_outbox[author_id].append(post_id)
        # Keep only recent posts for performance
        celebrity_outbox[author_id] = celebrity_outbox[author_id][-100:]
    else:
        # Fanout-on-write for regular users
        followers = followers_db.get(author_id, [])
        for follower_id in followers:
            if follower_id not in feed_cache:
                feed_cache[follower_id] = []
            feed_cache[follower_id].append(post_id)
            # Keep cache size bounded
            feed_cache[follower_id] = feed_cache[follower_id][-100:]

# --- Endpoints ---

@app.post("/users", status_code=201)
def create_user(user: UserCreate):
    user_id = str(uuid.uuid4())
    users_db[user_id] = {"user_id": user_id, "username": user.username}
    followers_db[user_id] = []
    following_db[user_id] = []
    feed_cache[user_id] = []
    return users_db[user_id]

@app.post("/users/{user_id}/follow/{target_id}")
def follow_user(user_id: str, target_id: str):
    if user_id not in users_db or target_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    if target_id not in following_db[user_id]:
        following_db[user_id].append(target_id)
        followers_db[target_id].append(user_id)
    return {"message": "Successfully followed user"}

@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate):
    if post.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    post_id = str(uuid.uuid4())
    new_post = {
        "post_id": post_id,
        "user_id": post.user_id,
        "content": post.content,
        "created_at": time.time(),
        "media_urls": post.media_urls
    }
    posts_db[post_id] = new_post

    # Trigger Fanout Process (simulating async task)
    fanout_post(post_id, post.user_id)

    return new_post

@app.get("/feed/{user_id}", response_model=List[PostResponse])
def get_feed(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    feed_post_ids = feed_cache.get(user_id, []).copy()

    # Hybrid Step: Pull posts from followed celebrities
    for following_id in following_db.get(user_id, []):
        if is_celebrity(following_id):
            recent_celeb_posts = celebrity_outbox.get(following_id, [])
            feed_post_ids.extend(recent_celeb_posts)

    # Resolve post IDs to actual post objects
    feed_posts = []
    for pid in feed_post_ids:
        post = posts_db.get(pid)
        if post:
            feed_posts.append(post)

    # Sort by created_at (reverse chronological order)
    feed_posts.sort(key=lambda x: x["created_at"], reverse=True)

    return feed_posts
