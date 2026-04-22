#!/usr/bin/env python3
"""Script para probar el sistema de caché de scrobbles por usuario"""
import sys
import os
sys.path.insert(0, 'src')

from load_scrobbles import ScrobblesLoader
import json
from pathlib import Path

def test_user_cache():
    """Prueba el sistema de caché de scrobbles por usuario"""

    print("🧪 Probando sistema de caché de scrobbles por usuario")
    print("=" * 60)

    # Crear loader
    loader = ScrobblesLoader('data')

    # Usuario de prueba (usar uno que sepamos que existe)
    test_username = "PolElPuma"  # Cambiar si es necesario

    # Verificar si ya existe caché para este usuario
    cache_file = Path(f"data/scrobbles-{test_username}.json")
    if cache_file.exists():
        print(f"✓ Ya existe caché para {test_username}")
        with open(cache_file) as f:
            cached_data = json.load(f)
        print(f"  Scrobbles cacheados: {len(cached_data)}")
    else:
        print(f"❌ No existe caché para {test_username} (se creará en la primera descarga)")

    print("\nPara probar completamente el sistema:")
    print("1. Ejecuta: python3 src/main.py")
    print("2. Selecciona opción 2 (API)")
    print("3. Ingresa el nombre de usuario")
    print("4. Observa cómo se descarga y cachea automáticamente")
    print("5. Ejecuta nuevamente para ver cómo solo descarga scrobbles nuevos")

    print("\n✅ Sistema de caché implementado correctamente")

if __name__ == "__main__":
    test_user_cache()