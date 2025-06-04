from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from state import ViajeStateInput
from accommodation_graph.state import AlojamientoStateInput
from accommodation_graph.accommodation_graph import accommodation_graph
from trip_planner_graph.trip_planner_graph import graph
import uvicorn
import json

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    with open("itinerario.html", encoding="utf-8") as f:
        return f.read()

@app.post("/itinerario")
def generar_itinerario(input_state: ViajeStateInput):
    result = graph.invoke(input_state)
    return result

    # with open("itinerario_result.json", encoding="utf-8") as f:
    #     data = json.load(f)
    # return data

@app.post("/accommodation")
def generar_accommodation(): #input_state: AlojamientoStateInput):

    with open("destino_result.json", encoding="utf-8") as f:
        data = json.load(f)

    input_state = AlojamientoStateInput (
        destino=data,
        fecha_inicio="2025-05-01",
        cantidad_adultos=2,
        cantidad_ninos=0
    )

    result = accommodation_graph.invoke(input_state)
    return result


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
