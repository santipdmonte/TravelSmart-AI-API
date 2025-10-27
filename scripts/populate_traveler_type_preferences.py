"""
Script para poblar las preferencias de cada TravelerType
Ejecutar una sola vez después de agregar la columna preferences
"""
from database import SessionLocal
from models.traveler_test.traveler_type import TravelerType

# Definir las preferencias por defecto para cada tipo de viajero
TRAVELER_TYPE_PREFERENCES = {
    "Aventurero": {
        "budget": "intermedio",
        "travel_pace": "activo",
        "city_view": "off_beaten",
        "travel_styles": ["adventurous", "adrenaline"],
        "food_preferences": []
    },
    "Explorador Cultural": {
        "budget": "intermedio",
        "travel_pace": "equilibrado",
        "city_view": "touristy",
        "travel_styles": ["cultural"],
        "food_preferences": []
    },
    "Viajero Relajado": {
        "budget": "confort",
        "travel_pace": "relax",
        "city_view": "local",
        "travel_styles": ["relaxing"],
        "food_preferences": []
    },
    "Gourmet": {
        "budget": "confort",
        "travel_pace": "equilibrado",
        "city_view": "local",
        "travel_styles": ["gastronomic", "cultural"],
        "food_preferences": ["fine_dining"]
    },
    "Social y Nocturno": {
        "budget": "intermedio",
        "travel_pace": "activo",
        "city_view": "touristy",
        "travel_styles": ["festive"],
        "food_preferences": []
    },
    "Romántico": {
        "budget": "confort",
        "travel_pace": "relax",
        "city_view": "off_beaten",
        "travel_styles": ["romantic", "relaxing"],
        "food_preferences": ["fine_dining"]
    }
}

def populate_traveler_type_preferences():
    """Actualiza las preferencias de cada TravelerType"""
    db = SessionLocal()
    
    try:
        # Obtener todos los TravelerTypes activos
        traveler_types = db.query(TravelerType).filter(
            TravelerType.deleted_at.is_(None)
        ).all()
        
        print(f"Encontrados {len(traveler_types)} TravelerTypes")
        print("="*60)
        
        updated_count = 0
        skipped_count = 0
        
        for tt in traveler_types:
            if tt.name in TRAVELER_TYPE_PREFERENCES:
                # Actualizar las preferencias
                preferences = TRAVELER_TYPE_PREFERENCES[tt.name]
                tt.preferences = preferences
                print(f"✓ Actualizando '{tt.name}':")
                print(f"  Preferences: {preferences}")
                updated_count += 1
            else:
                print(f"⚠ Saltando '{tt.name}' (no hay preferencias definidas)")
                skipped_count += 1
        
        # Guardar cambios
        db.commit()
        
        print("="*60)
        print(f"\n✅ Proceso completado:")
        print(f"  - {updated_count} TravelerTypes actualizados")
        print(f"  - {skipped_count} TravelerTypes saltados")
        
        # Verificar cambios
        print("\n" + "="*60)
        print("Verificación:")
        for tt in traveler_types:
            db.refresh(tt)
            print(f"  - {tt.name}: {tt.preferences}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando población de preferencias de TravelerTypes...")
    print()
    populate_traveler_type_preferences()
