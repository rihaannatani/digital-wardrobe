from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Digital Wardrobe")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>Digital Wardrobe</h1><p>Running.</p>"
