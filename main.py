from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from state import ViajeStateInput
from trip_planner_graph.trip_planner_graph import graph
import uvicorn

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    with open("itinerario.html", encoding="utf-8") as f:
        return f.read()

@app.post("/itinerario")
def generar_itinerario(input_state: ViajeStateInput):
    result = graph.invoke(input_state)
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
