import uvicorn

def start():
    uvicorn.run("nextrip_ai.main:app", host="0.0.0.0", port=8000, reload=True)
