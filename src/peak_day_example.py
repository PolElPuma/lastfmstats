#!/usr/bin/env python3
"""
Ejemplo simple de uso de la función get_peak_day_for_track
Muestra cómo usar la nueva funcionalidad en solo unos líneas
"""

from load_scrobbles import (
    ScrobblesLoader,
    ScrobblesAnalyzer,
    display_peak_day_for_track,
    display_top_tracks
)


def main():
    print("\n" + "="*80)
    print("EJEMPLO: BUSCAR EL DÍA CON MÁS ESCUCHAS DE UNA CANCIÓN")
    print("="*80)
    
    # 1. Cargar scrobbles
    loader = ScrobblesLoader('data')
    scrobbles = loader.load_file(loader.list_files()[1])
    
    # 2. Obtener la canción más escuchada
    print("\nObteniendo la canción más escuchada...")
    top_tracks = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=1)
    (artist, track), total = top_tracks[0]
    
    print(f"✓ Canción más escuchada: '{track}' de {artist} ({total} escuchas totales)")
    
    # 3. Calcular el día pico
    print("\nCalculando el día con más escuchas...")
    peak = ScrobblesAnalyzer.get_peak_day_for_track(scrobbles, artist, track)
    
    if peak:
        display_peak_day_for_track(peak)
    
    # 4. Ejemplo con otra canción: Buscar por artista y título
    print("\n" + "-"*80)
    print("EJEMPLO 2: Buscar una canción específica")
    print("-"*80)
    
    # Supongamos que queremos buscar "Creep" de Radiohead
    search_track = "todo lo que hago cuando no estás"
    search_artist = "Mori"
    
    print(f"\nBuscando: '{search_track}' de {search_artist}")
    
    peak = ScrobblesAnalyzer.get_peak_day_for_track(scrobbles, search_artist, search_track)
    
    if peak:
        display_peak_day_for_track(peak)
    else:
        print(f"❌ No se encontró: '{search_track}' de {search_artist}")
        
        # Mostrar algunas canciones de Radiohead disponibles
        radiohead_tracks = set(s.track for s in scrobbles if s.artist == search_artist)
        if radiohead_tracks:
            print(f"\nCanciones disponibles de {search_artist}:")
            for i, track_name in enumerate(sorted(radiohead_tracks)[:5], 1):
                print(f"  {i}. {track_name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
