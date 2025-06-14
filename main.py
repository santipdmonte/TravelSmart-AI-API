from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from state import ViajeState, ViajeStateInput, ViajeStateModify
# from accommodation_graph.state import AlojamientoStateInput
# from accommodation_graph.accommodation_graph import accommodation_graph
from trip_planner_graph.main_itinerary_graph import main_itinerary_graph
from trip_planner_graph.modify_itinerary_graph import modify_itinerary_graph
import uvicorn
import json

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    with open("itinerario.html", encoding="utf-8") as f:
        return f.read()

@app.post("/itinerario")
def generar_itinerario(input_state: ViajeStateInput):

    config = {
        "configurable": {
            "thread_id": "1"  
        }
    }

    result = main_itinerary_graph.invoke(input_state) #, config=config)

    return result

    # with open("itinerario_result.json", encoding="utf-8") as f:
    #     data = json.load(f)
    # return data

# print(result)

@app.post("/modificar_itinerario")
def modificar_itinerario(prompt: str):

    config = {
        "configurable": {
            "thread_id": "1"  
        }
    }


    try:
        with open("itinerario_turquia_12.json", encoding="utf-8") as f:
            data = json.load(f)

        state = ViajeStateModify(
            itinerario_actual=ViajeState(**data),
            prompt=prompt
        )
        
    except Exception as e:
        print(f"Error loading itinerary result: {e}")
        return {"error": str(e)}

    result = modify_itinerary_graph.invoke(input = state) #, config=config)

    return result



from trip_planner_graph.HIL_graph import graph
from langgraph.types import Command

@app.post("/initialize_graph")
def initialize_graph(thread_id: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    initial_input = {
        "itinerary": "False", 
        "user_feedback": "False"
    }

    state = graph.invoke(initial_input, config=config)

    return state


@app.post("/user_feedback")
def user_feedback(thread_id: str, user_feedback: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    graph.invoke(
        Command(resume=user_feedback),
        config=config
    )

    return graph.get_state(config)

@app.get("/get_state")
def get_state(thread_id: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    return graph.get_state(config)





# @app.post("/accommodation")
# def generar_accommodation(): #input_state: AlojamientoStateInput):

#     with open("destino_result.json", encoding="utf-8") as f:
#         data = json.load(f)

#     input_state = AlojamientoStateInput (
#         destino=data,
#         fecha_inicio="2025-05-01",
#         cantidad_adultos=2,
#         cantidad_ninos=0
#     )

#     result = accommodation_graph.invoke(input_state)
#     return result


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
