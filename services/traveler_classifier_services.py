from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class TravelerType(Enum):
    ADVENTURER = "adventurer"
    WELLNESS = "wellness"
    CULTURAL = "cultural"
    GASTRONOMIC = "gastronomic"
    URBANITE = "urbanite"
    FAMILY = "family"

@dataclass
class TravelerProfile:
    type: TravelerType
    name: str
    emoji: str
    description: str
    percentage: float

@dataclass
class ClassificationResult:
    primary_profile: TravelerProfile
    secondary_profile: Optional[TravelerProfile] = None
    scores: Optional[Dict[TravelerType, float]] = None

class TravelerClassifierService:
    
    def __init__(self):
        self.traveler_profiles = {
            TravelerType.ADVENTURER: {
                "name": "El Aventurero",
                "emoji": "🏞",
                "description": "Busca adrenalina, experiencias únicas al aire libre y desafíos físicos."
            },
            TravelerType.WELLNESS: {
                "name": "El Viajero Wellness", 
                "emoji": "🧘‍♀️",
                "description": "Busca desconexión, relajación y reconexión consigo mismo."
            },
            TravelerType.CULTURAL: {
                "name": "El Explorador Cultural",
                "emoji": "🏛",
                "description": "Ama aprender sobre nuevas culturas, historia y arte."
            },
            TravelerType.GASTRONOMIC: {
                "name": "El Viajero Gastronómico",
                "emoji": "🍷",
                "description": "El viaje es una excusa para comer bien y explorar sabores."
            },
            TravelerType.URBANITE: {
                "name": "El Urbanita Cosmopolita",
                "emoji": "🛍",
                "description": "Disfruta del ritmo vibrante de las ciudades y la vida moderna."
            },
            TravelerType.FAMILY: {
                "name": "El Viajero Familiar",
                "emoji": "👨‍👩‍👧‍👦",
                "description": "Viaja en grupo familiar, buscando seguridad y comodidad."
            }
        }
        
        # Sistema de scoring: cada respuesta otorga puntos a diferentes perfiles
        self.scoring_matrix = {
            # Pregunta 1: ¿Qué te emociona más de un viaje?
            "question_1": {
                "adventure": {TravelerType.ADVENTURER: 10, TravelerType.FAMILY: 2},
                "wellness": {TravelerType.WELLNESS: 10, TravelerType.FAMILY: 3},
                "culture": {TravelerType.CULTURAL: 10, TravelerType.URBANITE: 2},
                "gastronomy": {TravelerType.GASTRONOMIC: 10, TravelerType.CULTURAL: 3, TravelerType.URBANITE: 2}
            },
            
            # Pregunta 2: ¿Cómo preferís pasar un día libre en tu viaje?
            "question_2": {
                "outdoor": {TravelerType.ADVENTURER: 10, TravelerType.WELLNESS: 2},
                "relaxing": {TravelerType.WELLNESS: 10, TravelerType.FAMILY: 4},
                "local_immersion": {TravelerType.CULTURAL: 10, TravelerType.GASTRONOMIC: 3},
                "city_life": {TravelerType.URBANITE: 10, TravelerType.GASTRONOMIC: 2}
            },
            
            # Pregunta 3: ¿Qué recuerdo de viaje te haría más feliz?
            "question_3": {
                "epic_photo": {TravelerType.ADVENTURER: 10, TravelerType.URBANITE: 2},
                "self_discovery": {TravelerType.WELLNESS: 10, TravelerType.CULTURAL: 2},
                "learning": {TravelerType.CULTURAL: 10, TravelerType.WELLNESS: 2},
                "dining": {TravelerType.GASTRONOMIC: 10, TravelerType.URBANITE: 3}
            },
            
            # Pregunta 4: ¿Cuál es tu entorno ideal para hospedarte?
            "question_4": {
                "nature": {TravelerType.ADVENTURER: 10, TravelerType.WELLNESS: 3},
                "serene": {TravelerType.WELLNESS: 10, TravelerType.FAMILY: 2},
                "authentic": {TravelerType.CULTURAL: 10, TravelerType.GASTRONOMIC: 4},
                "modern": {TravelerType.URBANITE: 10, TravelerType.FAMILY: 2}
            },
            
            # Pregunta 5: ¿Cómo te gusta moverte en tus viajes?
            "question_5": {
                "flexible": {TravelerType.ADVENTURER: 10, TravelerType.CULTURAL: 2},
                "peaceful": {TravelerType.WELLNESS: 10, TravelerType.FAMILY: 5},
                "organized": {TravelerType.CULTURAL: 10, TravelerType.FAMILY: 4},
                "social": {TravelerType.URBANITE: 10, TravelerType.GASTRONOMIC: 3}
            }
        }

    def classify_traveler(self, answers: Dict[str, str]) -> ClassificationResult:
        """
        Clasifica al viajero basado en sus respuestas.
        
        Args:
            answers: Dict con las respuestas del usuario
                    {"question_1": "adventure", "question_2": "outdoor", ...}
        
        Returns:
            ClassificationResult con el perfil principal y secundario
        """
        scores = {traveler_type: 0 for traveler_type in TravelerType}
        
        # Calcular puntuación para cada respuesta
        for question, answer in answers.items():
            if question in self.scoring_matrix and answer in self.scoring_matrix[question]:
                answer_scores = self.scoring_matrix[question][answer]
                for traveler_type, points in answer_scores.items():
                    scores[traveler_type] += points
        
        # Convertir a porcentajes
        total_score = sum(scores.values())
        if total_score == 0:
            raise ValueError("No se pudo calcular la clasificación")
        
        percentages = {
            traveler_type: (score / total_score) * 100 
            for traveler_type, score in scores.items()
        }
        
        # Ordenar por puntuación
        sorted_types = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
        
        # Crear perfiles
        primary_type, primary_percentage = sorted_types[0]
        primary_profile = TravelerProfile(
            type=primary_type,
            name=self.traveler_profiles[primary_type]["name"],
            emoji=self.traveler_profiles[primary_type]["emoji"],
            description=self.traveler_profiles[primary_type]["description"],
            percentage=round(primary_percentage, 1)
        )
        
        secondary_profile = None
        if len(sorted_types) > 1 and sorted_types[1][1] >= 15:  # Solo si tiene al menos 15%
            secondary_type, secondary_percentage = sorted_types[1]
            secondary_profile = TravelerProfile(
                type=secondary_type,
                name=self.traveler_profiles[secondary_type]["name"],
                emoji=self.traveler_profiles[secondary_type]["emoji"],
                description=self.traveler_profiles[secondary_type]["description"],
                percentage=round(secondary_percentage, 1)
            )
        
        return ClassificationResult(
            primary_profile=primary_profile,
            secondary_profile=secondary_profile,
            scores=percentages
        )
    
    def get_questions(self) -> List[Dict]:
        """
        Retorna las preguntas del cuestionario con sus opciones.
        """
        return [
            {
                "id": "question_1",
                "text": "¿Qué te emociona más de un viaje?",
                "options": [
                    {"value": "adventure", "emoji": "🏔️", "title": "Aventura pura", "description": "Adrenalina, desafíos, naturaleza salvaje"},
                    {"value": "wellness", "emoji": "🧘‍♀️", "title": "Desconexión total", "description": "Relax, bienestar, paz interior"},
                    {"value": "culture", "emoji": "🏛️", "title": "Descubrir culturas", "description": "Historia, arte, tradiciones locales"},
                    {"value": "gastronomy", "emoji": "🍷", "title": "Sabores únicos", "description": "Gastronomía, vinos, experiencias culinarias"}
                ]
            },
            {
                "id": "question_2", 
                "text": "¿Cómo preferís pasar un día libre en tu viaje?",
                "options": [
                    {"value": "outdoor", "emoji": "🥾", "title": "Explorando al aire libre", "description": "Senderismo, deportes, naturaleza"},
                    {"value": "relaxing", "emoji": "🛀", "title": "Relajándome completamente", "description": "Spa, lectura, contemplación"},
                    {"value": "local_immersion", "emoji": "🎭", "title": "Sumergiéndome en lo local", "description": "Museos, barrios, eventos culturales"},
                    {"value": "city_life", "emoji": "🏙️", "title": "Viviendo la ciudad", "description": "Compras, bares, vida nocturna"}
                ]
            },
            {
                "id": "question_3",
                "text": "¿Qué recuerdo de viaje te haría más feliz?",
                "options": [
                    {"value": "epic_photo", "emoji": "📸", "title": "Una foto épica en la cima", "description": "Logro personal, paisaje increíble"},
                    {"value": "self_discovery", "emoji": "🧘", "title": "Haberte encontrado contigo mismo", "description": "Paz mental, renovación"},
                    {"value": "learning", "emoji": "🎨", "title": "Haber aprendido algo nuevo", "description": "Conocimiento, perspectiva cultural"},
                    {"value": "dining", "emoji": "🍽️", "title": "Una cena inolvidable", "description": "Sabores, ambiente, experiencia gastronómica"}
                ]
            },
            {
                "id": "question_4",
                "text": "¿Cuál es tu entorno ideal para hospedarte?",
                "options": [
                    {"value": "nature", "emoji": "⛺️", "title": "En medio de la naturaleza", "description": "Camping, cabañas, ecolodges"},
                    {"value": "serene", "emoji": "🌿", "title": "Tranquilo y sereno", "description": "Spa resort, hotel boutique, retiro"},
                    {"value": "authentic", "emoji": "🏛️", "title": "Céntrico y auténtico", "description": "Hotel histórico, B&B local, centro cultural"},
                    {"value": "modern", "emoji": "🏙️", "title": "Moderno y conectado", "description": "Hotel urbano, rooftop, vida nocturna cerca"}
                ]
            },
            {
                "id": "question_5",
                "text": "¿Cómo te gusta moverte en tus viajes?",
                "options": [
                    {"value": "flexible", "emoji": "🎒", "title": "Libre y flexible", "description": "Sin horarios fijos, siguiendo mi instinto"},
                    {"value": "peaceful", "emoji": "🧘‍♂️", "title": "Tranquilo y pausado", "description": "Sin prisa, disfrutando cada momento"},
                    {"value": "organized", "emoji": "📚", "title": "Organizado pero curioso", "description": "Plan básico con tiempo para explorar"},
                    {"value": "social", "emoji": "🍸", "title": "Social y dinámico", "description": "Conociendo gente, eventos, experiencias compartidas"}
                ]
            }
        ]
    
    def get_traveler_profiles(self) -> Dict:
        """
        Retorna todos los perfiles de viajero disponibles.
        """
        return self.traveler_profiles
