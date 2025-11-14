"""
Script para copiar preferencias de TravelerType a usuarios existentes
que ya tienen traveler_type_id asignado pero preferences = null
"""
from database import SessionLocal
from models.traveler_test.traveler_type import TravelerType
from models.user import User

def update_existing_users_preferences():
    """Copia preferencias del TravelerType a usuarios que ya tienen tipo asignado"""
    db = SessionLocal()
    
    try:
        # Buscar usuarios que tienen traveler_type_id pero preferences = null
        users_to_update = db.query(User).filter(
            User.traveler_type_id.is_not(None),
            User.preferences.is_(None),
            User.deleted_at.is_(None)
        ).all()
        
        print(f"Encontrados {len(users_to_update)} usuarios para actualizar")
        print("="*60)
        
        updated_count = 0
        skipped_count = 0
        
        for user in users_to_update:
            # Obtener el TravelerType del usuario
            traveler_type = db.query(TravelerType).filter(
                TravelerType.id == user.traveler_type_id
            ).first()
            
            if traveler_type and traveler_type.preferences:
                # Copiar las preferencias
                user.preferences = traveler_type.preferences
                print(f"✓ Actualizando usuario: {user.email}")
                print(f"  TravelerType: {traveler_type.name}")
                print(f"  Preferences: {traveler_type.preferences}")
                updated_count += 1
            else:
                print(f"⚠ Saltando usuario {user.email} (TravelerType sin preferencias)")
                skipped_count += 1
        
        # Guardar cambios
        db.commit()
        
        print("="*60)
        print(f"\n✅ Proceso completado:")
        print(f"  - {updated_count} usuarios actualizados")
        print(f"  - {skipped_count} usuarios saltados")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando actualización de preferencias de usuarios existentes...")
    print()
    update_existing_users_preferences()
