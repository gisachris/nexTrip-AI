from fastapi import APIRouter

authRouter = APIRouter()

@authRouter.post("/auth/register")
def registerUser():
    pass

@authRouter.post("/auth/login")
def loginUser():
    pass

@authRouter.get("/users/me")
def getUser():
    pass