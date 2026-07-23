from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="News Feed System API")

@app.post("/users/", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/users/{user_id}/follow/", status_code=201)
def follow_user(user_id: int, follow: schemas.FollowCreate, db: Session = Depends(get_db)):
    if user_id == follow.followee_id:
        raise HTTPException(status_code=400, detail="Users cannot follow themselves")

    existing_follow = db.query(models.Follow).filter(
        models.Follow.follower_id == user_id,
        models.Follow.followee_id == follow.followee_id
    ).first()

    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")

    db_follow = models.Follow(follower_id=user_id, followee_id=follow.followee_id)
    db.add(db_follow)
    db.commit()
    return {"message": "Successfully followed user"}

@app.post("/users/{user_id}/posts/", response_model=schemas.PostResponse, status_code=201)
def create_post(user_id: int, post: schemas.PostCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_post = models.Post(content=post.content, user_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/users/{user_id}/feed/", response_model=List[schemas.PostResponse])
def get_feed(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    # Simple Pull Model for Feed Generation
    following = db.query(models.Follow.followee_id).filter(models.Follow.follower_id == user_id).subquery()

    posts = db.query(models.Post).filter(
        models.Post.user_id.in_(following)
    ).order_by(models.Post.created_at.desc()).limit(limit).all()

    return posts
