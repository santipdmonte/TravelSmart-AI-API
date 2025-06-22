from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from routes.travel_classifier_routes import travel_classifier_router
from routes.document_analyzer_router import document_analyzer_router
from routes.itinerary_routes import itinerary_router

import uvicorn

app = FastAPI()

# Incluir rutas
app.include_router(travel_classifier_router)
app.include_router(document_analyzer_router)
app.include_router(itinerary_router)

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", encoding="utf-8") as f:
        return f.read()

# --- BLOQUE DE CÓDIGO PARA DEPURACIÓN ---
# print("--- RUTAS REGISTRADAS EN LA API DE IA ---")
# or route in app.routes:
#    if hasattr(route, "methods"):
#         print(f"Path: {route.path}, Methods: {route.methods}")
# print("---------------------------------------")
# --- FIN DEL BLOQUE DE DEPURACIÓN ---

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
