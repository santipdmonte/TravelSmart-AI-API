from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from services.traveler_classifier_services import TravelerClassifierService, TravelerType
from fastapi.responses import HTMLResponse

# Crear router para las rutas del clasificador de viajeros
travel_classifier_router = APIRouter(prefix="/traveler-classifier", tags=["Traveler Classifier"])

# Instancia del servicio
classifier_service = TravelerClassifierService()

# Modelos Pydantic para request/response
class ClassifyRequest(BaseModel):
    answers: Dict[str, str]

class ProfileResponse(BaseModel):
    type: str
    name: str
    emoji: str
    description: str
    percentage: float

class ClassificationResponse(BaseModel):
    primary_profile: ProfileResponse
    secondary_profile: Optional[ProfileResponse] = None
    detailed_scores: Dict[str, float]

class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    message: str
    error: Optional[str] = None

@travel_classifier_router.get("/", response_class=HTMLResponse)
def traveler_classifier_page():
    with open("traveler_classifier/traveler_classifier_template.html", encoding="utf-8") as f:
        return f.read()

@travel_classifier_router.get("/questions")
async def get_questions():
    """
    Endpoint para obtener todas las preguntas del cuestionario.
    
    Returns:
        JSON con las preguntas y sus opciones de respuesta
    """
    try:
        questions = classifier_service.get_questions()
        return ApiResponse(
            success=True,
            data=questions,
            message="Preguntas obtenidas exitosamente"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "message": "Error al obtener las preguntas"
            }
        )

@travel_classifier_router.post("/classify")
async def classify_traveler(request: ClassifyRequest):
    """
    Endpoint para clasificar un viajero basado en sus respuestas.
    
    Args:
        request: Objeto con las respuestas del usuario
        
    Returns:
        JSON con la clasificación del viajero
    """
    try:        
        answers = request.answers
        
        # Validar que se respondan todas las preguntas
        required_questions = ['question_1', 'question_2', 'question_3', 'question_4', 'question_5']
        missing_questions = [q for q in required_questions if q not in answers]
        
        if missing_questions:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"Faltan respuestas para: {', '.join(missing_questions)}",
                    "message": "Todas las preguntas deben ser respondidas"
                }
            )
        
        # Clasificar al viajero
        result = classifier_service.classify_traveler(answers)
        
        # Preparar respuesta
        response_data = ClassificationResponse(
            primary_profile=ProfileResponse(
                type=result.primary_profile.type.value,
                name=result.primary_profile.name,
                emoji=result.primary_profile.emoji,
                description=result.primary_profile.description,
                percentage=result.primary_profile.percentage
            ),
            secondary_profile=ProfileResponse(
                type=result.secondary_profile.type.value,
                name=result.secondary_profile.name,
                emoji=result.secondary_profile.emoji,
                description=result.secondary_profile.description,
                percentage=result.secondary_profile.percentage
            ) if result.secondary_profile else None,
            detailed_scores={
                traveler_type.value: round(score, 1) 
                for traveler_type, score in result.scores.items()
            }
        )
        
        return ApiResponse(
            success=True,
            data=response_data.dict(),
            message="Clasificación realizada exitosamente"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e),
                "message": "Error en la clasificación"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "message": "Error interno del servidor"
            }
        )

@travel_classifier_router.get("/profiles")
async def get_traveler_profiles():
    """
    Endpoint para obtener todos los perfiles de viajero disponibles.
    
    Returns:
        JSON con todos los perfiles y sus descripciones
    """
    try:
        profiles = classifier_service.get_traveler_profiles()
        
        # Formatear respuesta
        formatted_profiles = {}
        for traveler_type, profile_data in profiles.items():
            formatted_profiles[traveler_type.value] = {
                "name": profile_data["name"],
                "emoji": profile_data["emoji"],
                "description": profile_data["description"]
            }
        
        return ApiResponse(
            success=True,
            data=formatted_profiles,
            message="Perfiles obtenidos exitosamente"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "message": "Error al obtener los perfiles"
            }
        )

@travel_classifier_router.get("/test")
async def test_classifier():
    """
    Endpoint de prueba para verificar que el clasificador funciona correctamente.
    
    Returns:
        JSON con un ejemplo de clasificación
    """
    try:
        # Respuestas de ejemplo (perfil aventurero)
        test_answers = {
            "question_1": "adventure",
            "question_2": "outdoor", 
            "question_3": "epic_photo",
            "question_4": "nature",
            "question_5": "flexible"
        }
        
        result = classifier_service.classify_traveler(test_answers)
        
        test_data = {
            "test_answers": test_answers,
            "classification": {
                "primary_profile": {
                    "type": result.primary_profile.type.value,
                    "name": result.primary_profile.name,
                    "emoji": result.primary_profile.emoji,
                    "percentage": result.primary_profile.percentage
                },
                "secondary_profile": {
                    "type": result.secondary_profile.type.value,
                    "name": result.secondary_profile.name,
                    "emoji": result.secondary_profile.emoji,
                    "percentage": result.secondary_profile.percentage
                } if result.secondary_profile else None
            }
        }
        
        return ApiResponse(
            success=True,
            data=test_data,
            message="Prueba del clasificador exitosa"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "message": "Error en la prueba del clasificador"
            }
        )

@travel_classifier_router.get("/profile/{profile_type}")
async def get_profile_details(profile_type: str):
    """
    Endpoint para obtener los detalles de un perfil específico.
    
    Args:
        profile_type: Tipo de perfil de viajero
        
    Returns:
        JSON con los detalles del perfil
    """
    try:
        # Validar que el tipo de perfil existe
        try:
            traveler_type = TravelerType(profile_type)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": f"Perfil '{profile_type}' no encontrado",
                    "message": "Tipo de perfil no válido"
                }
            )
        
        profiles = classifier_service.get_traveler_profiles()
        profile_data = profiles[traveler_type]
        
        response_data = {
            "type": traveler_type.value,
            "name": profile_data["name"],
            "emoji": profile_data["emoji"],
            "description": profile_data["description"]
        }
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Perfil obtenido exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "message": "Error al obtener el perfil"
            }
        )
