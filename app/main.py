from fastapi import FastAPI

app = FastAPI(title="LNKGRD")

@app.get("/health")
def health():
    return {"status": "ok"}