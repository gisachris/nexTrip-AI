import uvicorn

def start():
    uvicorn.run("nextrip_ai.run:start", reload=True);