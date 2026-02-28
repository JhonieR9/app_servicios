from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers import clientes, trabajadores

app = FastAPI(title="TalentHub API", version="1.0.0")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Incluir routers
app.include_router(clientes.router)
app.include_router(trabajadores.router)

# ============================================
# PÁGINA PRINCIPAL
# ============================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "TalentHub API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
