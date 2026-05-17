from fastapi import APIRouter

authRouter = APIRouter(
    prefix="auth",
    tags=["authentication"]
)

@authRouter.post("/register")
def registerUser():
    pass

@authRouter.post("/login")
def loginUser():
    pass

@authRouter.get("/users/me")
def getUser():
    pass