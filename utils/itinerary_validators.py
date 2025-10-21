"""
Utilidades de validación para itinerarios generados por IA.
Asegura que los datos cumplan con las reglas de negocio.
"""

from typing import List, Optional
from states.itinerary import ViajeState, TransporteEntreDestinosState, DestinoState, TrasnportEnum


def validate_transportes_secuenciales(viaje_state: ViajeState) -> tuple[bool, List[str]]:
    """
    Valida que los transportes sigan el orden secuencial de los destinos.
    
    Args:
        viaje_state: Estado del viaje a validar
        
    Returns:
        tuple[bool, List[str]]: (es_valido, lista_de_errores)
    """
    errores = []
    destinos = viaje_state.destinos or []
    transportes = viaje_state.transportes_entre_destinos or []
    
    # Validación 0: Si hay solo 1 destino, no debe haber transportes
    if len(destinos) <= 1:
        if len(transportes) > 0:
            errores.append(f"❌ Con {len(destinos)} destino(s), no debería haber transportes, pero hay {len(transportes)}")
        return len(errores) == 0, errores
    
    # Validación 1: Cantidad correcta de transportes
    expected_count = len(destinos) - 1
    if len(transportes) != expected_count:
        errores.append(
            f"❌ ERROR DE CANTIDAD: Se esperaban {expected_count} transportes "
            f"para {len(destinos)} destinos, pero hay {len(transportes)}"
        )
        # Si la cantidad es incorrecta, no vale la pena seguir validando
        return False, errores
    
    # Validación 2: Secuencia correcta
    for i, transporte in enumerate(transportes):
        origen_esperado = destinos[i].ciudad
        destino_esperado = destinos[i + 1].ciudad
        
        # Validar origen
        if transporte.ciudad_origen != origen_esperado:
            errores.append(
                f"❌ ERROR en transporte[{i}]: origen es '{transporte.ciudad_origen}' "
                f"pero se esperaba '{origen_esperado}' (destino[{i}].ciudad)"
            )
        
        # Validar destino
        if transporte.ciudad_destino != destino_esperado:
            errores.append(
                f"❌ ERROR en transporte[{i}]: destino es '{transporte.ciudad_destino}' "
                f"pero se esperaba '{destino_esperado}' (destino[{i+1}].ciudad)"
            )
    
    es_valido = len(errores) == 0
    
    if es_valido:
        print(f"✅ Validación de transportes secuenciales: EXITOSA ({len(transportes)} transportes)")
    else:
        print(f"❌ Validación de transportes secuenciales: FALLÓ con {len(errores)} errores")
        for error in errores:
            print(f"   {error}")
    
    return es_valido, errores


def auto_fix_transportes_secuenciales(viaje_state: ViajeState) -> tuple[ViajeState, bool]:
    """
    Intenta auto-corregir los transportes para que sean secuenciales.
    
    Esta función busca transportes existentes que coincidan con el orden correcto.
    Si no encuentra uno, crea un transporte genérico.
    
    Args:
        viaje_state: Estado del viaje a corregir
        
    Returns:
        tuple[ViajeState, bool]: (viaje_corregido, hubo_cambios)
    """
    destinos = viaje_state.destinos or []
    transportes_originales = viaje_state.transportes_entre_destinos or []
    
    # Si hay 1 o menos destinos, no debe haber transportes
    if len(destinos) <= 1:
        viaje_state.transportes_entre_destinos = []
        hubo_cambios = len(transportes_originales) > 0
        if hubo_cambios:
            print(f"🔧 Auto-fix: Eliminados {len(transportes_originales)} transportes (solo hay {len(destinos)} destino(s))")
        return viaje_state, hubo_cambios
    
    transportes_corregidos = []
    hubo_cambios = False
    
    for i in range(len(destinos) - 1):
        origen = destinos[i]
        destino = destinos[i + 1]
        
        # Buscar si existe un transporte correcto en los originales
        transporte_encontrado = None
        for t in transportes_originales:
            if t.ciudad_origen == origen.ciudad and t.ciudad_destino == destino.ciudad:
                transporte_encontrado = t
                break
        
        if transporte_encontrado:
            # Usar el transporte existente (orden correcto)
            transportes_corregidos.append(transporte_encontrado)
        else:
            # No se encontró transporte con el orden correcto
            # Buscar si existe en orden inverso o con otro destino
            transporte_alternativo = None
            for t in transportes_originales:
                # Buscar transportes que involucren el origen o destino correcto
                if t.ciudad_origen == origen.ciudad or t.ciudad_destino == destino.ciudad:
                    transporte_alternativo = t
                    break
            
            if transporte_alternativo:
                # Crear transporte nuevo basado en el alternativo pero con origen/destino correcto
                print(f"⚠️ Auto-fix: Corrigiendo transporte {i}: {origen.ciudad} → {destino.ciudad}")
                print(f"   Original era: {transporte_alternativo.ciudad_origen} → {transporte_alternativo.ciudad_destino}")
                transportes_corregidos.append(
                    TransporteEntreDestinosState(
                        ciudad_origen=origen.ciudad,
                        ciudad_destino=destino.ciudad,
                        tipo_transporte=transporte_alternativo.tipo_transporte,  # Reusar tipo
                        justificacion=f"Transporte corregido automáticamente para seguir orden secuencial. {transporte_alternativo.justificacion}",
                        alternativas=transporte_alternativo.alternativas
                    )
                )
                hubo_cambios = True
            else:
                # Crear transporte por defecto (esto indica un error grave de la IA)
                print(f"⚠️ WARNING: Creando transporte POR DEFECTO para {origen.ciudad} → {destino.ciudad}")
                print(f"   La IA no generó ningún transporte relacionado con estas ciudades")
                transportes_corregidos.append(
                    TransporteEntreDestinosState(
                        ciudad_origen=origen.ciudad,
                        ciudad_destino=destino.ciudad,
                        tipo_transporte=TrasnportEnum.AUTO,  # Default más seguro
                        justificacion="Transporte auto-generado debido a datos faltantes en la generación inicial",
                        alternativas=["Avión", "Colectivo", "Tren", "Auto"]
                    )
                )
                hubo_cambios = True
    
    viaje_state.transportes_entre_destinos = transportes_corregidos
    
    if hubo_cambios:
        print(f"🔧 Auto-fix completado: {len(transportes_corregidos)} transportes corregidos")
    
    return viaje_state, hubo_cambios


def validate_and_fix_itinerary(viaje_state: ViajeState) -> ViajeState:
    """
    Función principal que valida y corrige automáticamente un itinerario.
    
    Esta función debe ser llamada después de que la IA genere un itinerario,
    antes de guardarlo en la base de datos.
    
    Args:
        viaje_state: Estado del viaje generado por la IA
        
    Returns:
        ViajeState: Viaje validado y corregido si fue necesario
        
    Raises:
        ValueError: Si no se puede corregir el itinerario automáticamente
    """
    print("\n" + "="*80)
    print("🔍 INICIANDO VALIDACIÓN DE ITINERARIO")
    print("="*80)
    
    # Validar transportes secuenciales
    es_valido, errores = validate_transportes_secuenciales(viaje_state)
    
    if es_valido:
        print("✅ El itinerario pasó todas las validaciones")
        return viaje_state
    
    # Si no es válido, intentar auto-fix
    print("\n⚠️ El itinerario tiene errores. Intentando auto-corrección...")
    viaje_state_corregido, hubo_cambios = auto_fix_transportes_secuenciales(viaje_state)
    
    if not hubo_cambios:
        print("❌ No se realizaron cambios durante el auto-fix")
        raise ValueError(f"Itinerario inválido y no se pudo corregir automáticamente: {errores}")
    
    # Re-validar después del fix
    print("\n🔍 Re-validando después del auto-fix...")
    es_valido_final, errores_finales = validate_transportes_secuenciales(viaje_state_corregido)
    
    if not es_valido_final:
        print("❌ El itinerario sigue siendo inválido después del auto-fix")
        raise ValueError(f"No se pudo corregir automáticamente: {errores_finales}")
    
    print("✅ Itinerario corregido y validado exitosamente")
    print("="*80 + "\n")
    
    return viaje_state_corregido


# Función de utilidad para logging detallado
def log_itinerary_structure(viaje_state: ViajeState):
    """Imprime la estructura del itinerario para debugging"""
    print("\n📋 ESTRUCTURA DEL ITINERARIO:")
    print(f"   Nombre: {viaje_state.nombre_viaje}")
    print(f"   Duración: {viaje_state.cantidad_dias} días")
    print(f"\n🏙️ DESTINOS ({len(viaje_state.destinos or [])}):")
    for i, destino in enumerate(viaje_state.destinos or []):
        print(f"   [{i}] {destino.ciudad}, {destino.pais} ({destino.dias_en_destino} días)")
    
    print(f"\n🚗 TRANSPORTES ({len(viaje_state.transportes_entre_destinos or [])}):")
    for i, transporte in enumerate(viaje_state.transportes_entre_destinos or []):
        print(f"   [{i}] {transporte.ciudad_origen} → {transporte.ciudad_destino} ({transporte.tipo_transporte})")
    print()
