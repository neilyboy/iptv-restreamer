from datetime import timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import engine, get_db
from stream_manager import stream_manager

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IPTV Re-Streaming API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication endpoints
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

# Stream endpoints
@app.post("/streams/", response_model=schemas.Stream)
def create_stream(
    stream: schemas.StreamCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_stream = models.Stream(**stream.dict())
    db.add(db_stream)
    db.commit()
    db.refresh(db_stream)
    return db_stream

@app.get("/streams/", response_model=List[schemas.Stream])
def read_streams(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    streams = db.query(models.Stream).offset(skip).limit(limit).all()
    return streams

@app.get("/streams/{stream_id}", response_model=schemas.Stream)
def read_stream(
    stream_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if db_stream is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    return db_stream

@app.put("/streams/{stream_id}", response_model=schemas.Stream)
def update_stream(
    stream_id: int, 
    stream: schemas.StreamUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if db_stream is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    update_data = stream.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_stream, key, value)
    
    db.commit()
    db.refresh(db_stream)
    return db_stream

@app.delete("/streams/{stream_id}")
def delete_stream(
    stream_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if db_stream is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Stop the stream if it's running
    if db_stream.status == "running":
        stream_manager.stop_stream(db, stream_id)
    
    db.delete(db_stream)
    db.commit()
    return {"detail": "Stream deleted"}

@app.post("/streams/{stream_id}/start")
def start_stream(
    stream_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    try:
        db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
        if db_stream is None:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        success = stream_manager.start_stream(db, stream_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start stream")
        
        return {"detail": "Stream started"}
    except Exception as e:
        import traceback
        error_details = f"Error starting stream: {str(e)}\n{traceback.format_exc()}"
        print(error_details)  # Print to console for debugging
        raise HTTPException(status_code=500, detail=f"Failed to start stream: {str(e)}")

@app.post("/streams/{stream_id}/stop")
def stop_stream(
    stream_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if db_stream is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    success = stream_manager.stop_stream(db, stream_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop stream")
    
    return {"detail": "Stream stopped"}

@app.post("/streams/{stream_id}/restart")
def restart_stream(
    stream_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if db_stream is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    success = stream_manager.restart_stream(db, stream_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to restart stream")
    
    return {"detail": "Stream restarted"}

@app.get("/streams/{stream_id}/status")
def get_stream_status(
    stream_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if db_stream is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    status = stream_manager.check_stream_status(db, stream_id)
    return status

@app.get("/streams/{stream_id}/logs", response_model=List[schemas.StreamLog])
def get_stream_logs(
    stream_id: int, 
    limit: Optional[int] = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if db_stream is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    logs = db.query(models.StreamLog).filter(
        models.StreamLog.stream_id == stream_id
    ).order_by(models.StreamLog.timestamp.desc()).limit(limit).all()
    
    return logs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
