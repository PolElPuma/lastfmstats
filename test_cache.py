#!/usr/bin/env python3
from src.load_scrobbles import ScrobblesAnalyzer
import time
import json
from pathlib import Path

# Primera llamada (desde API si no está en caché)
print("🔹 Primera consulta...")
start = time.time()
duration1 = ScrobblesAnalyzer._get_track_duration("Queen", "Bohemian Rhapsody")
elapsed1 = time.time() - start
print(f"   Resultado: {duration1}s, Tiempo: {elapsed1:.2f}s")

# Segunda llamada (desde caché en memoria)
print("\n🔹 Segunda consulta (caché en memoria)...")
start = time.time()
duration2 = ScrobblesAnalyzer._get_track_duration("Queen", "Bohemian Rhapsody")
elapsed2 = time.time() - start
print(f"   Resultado: {duration2}s, Tiempo: {elapsed2:.2f}s")

# Verificar que el archivo se guardó
cache_file = Path("data/durations.json")
if cache_file.exists():
    with open(cache_file) as f:
        cached = json.load(f)
    print(f"\n✓ Archivo durations.json creado con {len(cached)} entrada(s)")
    print(f"  Contenido: {list(cached.keys())[:3]}")
else:
    print("\n❌ Archivo durations.json no encontrado")
