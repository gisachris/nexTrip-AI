from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from nextrip_ai.core.dependencies import get_db, get_current_user
from nextrip_ai.core.security import hash_password, verify_password, create_access_token
from nextrip_ai.models.user import User
from nextrip_ai.api.routes.auth.authSchema import LoginRequest, TokenResponse
from nextrip_ai.api.routes.auth.userSchema import UserCreate, UserResponse

authRouter = APIRouter()

@authRouter.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def registerUser(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="Email or username already exists")
    user = User(email=payload.email, username=payload.username, password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@authRouter.post("/auth/login", response_model=TokenResponse)
def loginUser(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.username).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@authRouter.get("/users/me", response_model=UserResponse)
def getUser(current_user: User = Depends(get_current_user)):
    return current_user
