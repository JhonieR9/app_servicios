from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
# PÁGINA PRINCIPAL - SOLO FORMULARIO
# ============================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # Redirigir directamente al formulario de registro
    return RedirectResponse(url="/trabajador/registro", status_code=302)

@app.get("/inicio", response_class=HTMLResponse)
def mostrar_solo_formulario(request: Request):
    """Página alternativa que solo muestra acceso al formulario"""
    return templates.TemplateResponse("solo_formulario.html", {"request": request})

# Bloquear acceso a rutas de clientes (opcional)
@app.get("/cliente/{path:path}")
def bloquear_clientes(path: str):
    """Redirige cualquier ruta de cliente al formulario"""
    return RedirectResponse(url="/trabajador/registro", status_code=302)

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "TalentHub API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
