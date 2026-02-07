#!/usr/bin/env python3
"""
Ejemplo simple de uso de las funciones de análisis global de días
"""

from load_scrobbles import (
    ScrobblesLoader,
    ScrobblesAnalyzer,
    display_top_days_overall
)


def main():
    print("\n" + "="*80)
    print("EJEMPLO: DÍAS CON MÁS ESCUCHAS")
    print("="*80)
    
    # Cargar
    loader = ScrobblesLoader('data')
    scrobbles = loader.load_file(loader.list_files()[0])
    
    # Ejemplo 1: Top 10 días por total de escuchas
    print("\n" + "-"*80)
    print("EJEMPLO 1: Top 10 días con más escuchas totales")
    print("-"*80)
    
    top_days = ScrobblesAnalyzer.get_top_days_overall(scrobbles, n=10)
    display_top_days_overall(top_days, n=10, metric="escuchas")
    
    # Ejemplo 2: Top 10 días por artistas diferentes
    print("\n" + "-"*80)
    print("EJEMPLO 2: Top 10 días con más artistas diferentes")
    print("-"*80)
    
    top_artists_days = ScrobblesAnalyzer.get_top_days_overall_by_artist_count(scrobbles, n=10)
    display_top_days_overall(top_artists_days, n=10, metric="artistas diferentes")
    
    # Ejemplo 3: Top 10 días por canciones diferentes
    print("\n" + "-"*80)
    print("EJEMPLO 3: Top 10 días con más canciones diferentes")
    print("-"*80)
    
    top_tracks_days = ScrobblesAnalyzer.get_top_days_overall_by_track_count(scrobbles, n=10)
    display_top_days_overall(top_tracks_days, n=10, metric="canciones diferentes")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
