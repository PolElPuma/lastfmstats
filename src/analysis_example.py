#!/usr/bin/env python3
"""
Ejemplo de uso de las funciones de análisis de scrobbles
Demuestra cómo calcular los n más escuchados con filtrado por fechas
"""

from load_scrobbles import ScrobblesLoader, ScrobblesAnalyzer, display_top_artists, display_top_albums, display_top_tracks


def main():
    print("\n" + "="*80)
    print("ANÁLISIS DE SCROBBLES - EJEMPLO")
    print("="*80)
    
    # Cargar scrobbles
    loader = ScrobblesLoader('data')
    files = loader.list_files()
    
    if not files:
        print("No se encontraron archivos de scrobbles")
        return
    
    print(f"\nCargando: {files[0]}")
    scrobbles = loader.load_file(files[0])
    
    if not scrobbles:
        print("No se pudieron cargar los scrobbles")
        return
    
    # Análisis sin filtro de fechas (todo el histórico)
    print("\n" + "-"*80)
    print("ANÁLISIS DEL PERÍODO COMPLETO")
    print("-"*80)
    
    # Top 10 artistas
    top_artists = ScrobblesAnalyzer.get_top_artists(scrobbles, n=10)
    display_top_artists(top_artists, len(scrobbles))
    
    # Top 10 álbumes
    top_albums = ScrobblesAnalyzer.get_top_albums(scrobbles, n=10)
    display_top_albums(top_albums, len(scrobbles))
    
    # Top 10 canciones
    top_tracks = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=10)
    display_top_tracks(top_tracks, len(scrobbles))
    
    # Análisis con filtro de fechas (últimos 7 días)
    print("\n" + "-"*80)
    print("ANÁLISIS ÚLTIMOS 7 DÍAS")
    print("-"*80)
    
    # Ejemplo: últimas escuchas hasta "05 Feb 2026, 13:57"
    from_date = "29 Jan 2026, 00:00"  # 7 días atrás
    to_date = "05 Feb 2026, 23:59"     # Hasta hoy
    
    top_artists_week = ScrobblesAnalyzer.get_top_artists(scrobbles, n=10, from_date=from_date, to_date=to_date)
    filtered_count = len([s for s in scrobbles if ScrobblesAnalyzer._parse_date(s.utc_time) 
                         and ScrobblesAnalyzer._parse_date(from_date) <= ScrobblesAnalyzer._parse_date(s.utc_time) <= ScrobblesAnalyzer._parse_date(to_date)])
    
    print(f"Scrobbles en el período: {filtered_count}")
    display_top_artists(top_artists_week, filtered_count)
    
    top_albums_week = ScrobblesAnalyzer.get_top_albums(scrobbles, n=10, from_date=from_date, to_date=to_date)
    display_top_albums(top_albums_week, filtered_count)
    
    top_tracks_week = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=10, from_date=from_date, to_date=to_date)
    display_top_tracks(top_tracks_week, filtered_count)
    
    # Ejemplo: Top 20 en lugar de Top 10
    print("\n" + "-"*80)
    print("TOP 20 ARTISTAS DE TODOS LOS TIEMPOS")
    print("-"*80)
    
    top_20_artists = ScrobblesAnalyzer.get_top_artists(scrobbles, n=20)
    display_top_artists(top_20_artists, len(scrobbles))


if __name__ == "__main__":
    main()
