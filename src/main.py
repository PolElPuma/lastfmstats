#!/usr/bin/env python3
"""
Main para cargar scrobbles, calcular estadísticas y generar el calendario HTML
"""
from load_scrobbles import ScrobblesLoader, ScrobblesAnalyzer, Scrobble
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo


def select_file() -> Optional[str]:
    """
    Permite al usuario seleccionar un archivo JSON de scrobbles
    
    Returns:
        Ruta del archivo seleccionado o None si se cancela
    """
    loader = ScrobblesLoader('data')
    files = loader.list_files()
    
    if not files:
        print("❌ No se encontraron archivos de scrobbles en la carpeta 'data'")
        return None
    
    print("\n" + "="*60)
    print("📁 Archivos de Scrobbles Disponibles:")
    print("="*60)
    for i, file in enumerate(files, 1):
        from pathlib import Path
        filename = Path(file).name
        size_mb = Path(file).stat().st_size / (1024 * 1024)
        print(f"{i}. {filename} ({size_mb:.2f} MB)")
    print("="*60)
    
    while True:
        try:
            choice = input(f"\nSelecciona un archivo (1-{len(files)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
            else:
                print(f"❌ Por favor ingresa un número entre 1 y {len(files)}")
        except ValueError:
            print("❌ Entrada inválida. Ingresa un número.")


def select_start_date() -> Optional[datetime]:
    """
    Permite al usuario seleccionar una fecha de inicio
    
    Returns:
        Objeto datetime con la fecha seleccionada o None si no se especifica
    """
    print("\n" + "="*60)
    print("📅 Seleccionar Fecha de Inicio (opcional)")
    print("="*60)
    print("Formato: DD/MM/YYYY o YYYY-MM-DD")
    print("Deja en blanco para usar todos los datos")
    print("="*60)
    
    while True:
        date_str = input("\nFecha de inicio: ").strip()
        
        if not date_str:
            print("✓ Se usarán todos los datos disponibles")
            return None
        
        # Intentar parsear el formato DD/MM/YYYY
        for fmt in ["%d/%m/%Y", "%Y-%m-%d"]:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                print(f"✓ Fecha seleccionada: {date_obj.strftime('%d de %B de %Y')}")
                return date_obj
            except ValueError:
                continue
        
        print(f"❌ Formato de fecha inválido. Intenta DD/MM/YYYY o YYYY-MM-DD")


def filter_scrobbles_by_date(
    scrobbles: List[Scrobble],
    start_date: Optional[datetime]
) -> List[Scrobble]:
    """
    Filtra los scrobbles a partir de una fecha
    
    Args:
        scrobbles: Lista de scrobbles
        start_date: Fecha de inicio o None para usar todos
        
    Returns:
        Lista filtrada de scrobbles
    """
    if not start_date:
        return scrobbles
    
    # Convertir start_date a timestamp Unix para facilitar comparación
    start_timestamp = int(start_date.timestamp())
    
    filtered = []
    for scrobble in scrobbles:
        if scrobble.uts:
            try:
                scrobble_timestamp = int(scrobble.uts)
                if scrobble_timestamp >= start_timestamp:
                    filtered.append(scrobble)
            except (ValueError, TypeError):
                pass
    
    return filtered


def select_n_items() -> int:
    """
    Permite al usuario seleccionar cuántas canciones, artistas y álbumes mostrar
    
    Returns:
        Número de items a mostrar (default: 20)
    """
    print("\n" + "="*60)
    print("📦 Cantidad de Canciones, Artistas y Álbumes")
    print("="*60)
    print("Ingresa cuántos items mostrar de cada categoría")
    print("(default: 20, mínimo: 5, máximo: 100)")
    print("="*60)
    
    while True:
        try:
            n_str = input("\nCantidad de items: ").strip()
            
            if not n_str:
                print("✓ Se mostrarán 20 items por categoría")
                return 20
            
            n = int(n_str)
            if 5 <= n <= 100:
                print(f"✓ Se mostrarán {n} items por categoría")
                return n
            else:
                print("❌ Ingresa un número entre 5 y 100")
        except ValueError:
            print("❌ Entrada inválida. Ingresa un número.")


def select_n_days() -> Tuple[int, int]:
    """
    Permite al usuario seleccionar cuántos días y canciones por día mostrar
    
    Returns:
        Tupla (n_días, n_canciones_pico) - cantidad de días y canciones con mayor pico
    """
    print("\n" + "="*60)
    print("🔥 Días y Canciones con Mayor Pico")
    print("="*60)
    print("Ingresa cuántos días mostrar en el resumen")
    print("(default: 5, mínimo: 3, máximo: 20)")
    print("="*60)
    
    while True:
        try:
            n_str = input("\nCantidad de días: ").strip()
            
            if not n_str:
                print("✓ Se mostrarán 5 días y 5 canciones con mayor pico")
                return (5, 5)
            
            n = int(n_str)
            if 3 <= n <= 20:
                print(f"✓ Se mostrarán {n} días")
                return (n, n)
            else:
                print("❌ Ingresa un número entre 3 y 20")
        except ValueError:
            print("❌ Entrada inválida. Ingresa un número.")


def select_split_by_year() -> bool:
    """
    Permite al usuario seleccionar si desea dividir el calendario por año
    
    Returns:
        True si desea dividir por año, False si desea un calendario único
    """
    print("\n" + "="*60)
    print("📅 Dividir Calendario por Año")
    print("="*60)
    print("¿Deseas dividir el calendario por años separados con paginación?")
    print("(default: sí)")
    print("="*60)
    
    while True:
        choice = input("\n¿Dividir por años? (s/n): ").strip().lower()
        
        if not choice or choice == 's':
            print("✓ Calendario dividido por años con paginación")
            return True
        elif choice == 'n':
            print("✓ Calendario único para todo el período")
            return False
        else:
            print("❌ Por favor, ingresa 's' o 'n'")




def calculate_summary_for_scrobbles(scrobbles: List[Scrobble], n_items: int, n_days: int, n_peak_plays: int) -> Dict[str, Any]:
    """
    Calcula un resumen de estadísticas para un conjunto de scrobbles.
    
    Args:
        scrobbles: Lista de scrobbles
        n_items: Número de items a incluir en tops
        n_days: Número de días para tops
        n_peak_plays: Número de tracks para peak plays
    
    Returns:
        Diccionario con todas las estadísticas
    """
    top_tracks = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=n_items) or []

    # Para cada top track, obtener el día pico
    track_peaks: Dict[str, Dict[str, Any]] = {}
    for (artist, track), _ in top_tracks:
        res = ScrobblesAnalyzer.get_peak_day_for_track(scrobbles, artist, track)
        key = f"{artist}||{track}"
        if res:
            date, count, total = res
            track_peaks[key] = {"date": date, "count": count, "total": total}
        else:
            track_peaks[key] = {}

    # Top N artistas
    top_artists = ScrobblesAnalyzer.get_top_artists(scrobbles, n=n_items) or []

    # Top N álbumes
    top_albums = ScrobblesAnalyzer.get_top_albums(scrobbles, n=n_items) or []

    # Top N días
    top_days = ScrobblesAnalyzer.get_top_days_overall(scrobbles, n=n_days) or []

    # Obtener la canción más escuchada de cada uno de esos días
    most_played = ScrobblesAnalyzer.get_most_played_track_per_day(scrobbles) or {}
    top_days_most_played = {}
    for day, _ in top_days:
        if day in most_played:
            artist, track, image_url, url, plays = most_played[day]
            top_days_most_played[day] = (artist, track, plays)
        else:
            top_days_most_played[day] = ()

    # Top N canciones por escuchas en su día pico
    top_tracks_peak_plays = ScrobblesAnalyzer.get_top_tracks_by_peak_plays(scrobbles, n=n_peak_plays) or []

    # Top N canciones por mayor racha de días seguidos
    top_tracks_consecutive = ScrobblesAnalyzer.get_top_tracks_by_consecutive_days(scrobbles, n=n_days) or []
    # Top N artistas y álbumes por racha de días seguidos
    top_artists_consecutive = ScrobblesAnalyzer.get_top_artists_by_consecutive_days(scrobbles, n=n_days) or []
    top_albums_consecutive = ScrobblesAnalyzer.get_top_albums_by_consecutive_days(scrobbles, n=n_days) or []

    return {
        "top_tracks": top_tracks,
        "track_peaks": track_peaks,
        "top_tracks_consecutive_days": top_tracks_consecutive,
        "top_artists_consecutive_days": top_artists_consecutive,
        "top_albums_consecutive_days": top_albums_consecutive,
        "hourly_top": ScrobblesAnalyzer.get_hourly_top(scrobbles) or {},
        "top_artists": top_artists,
        "top_albums": top_albums,
        "top_days": top_days,
        "top_days_most_played": top_days_most_played,
        "top_tracks_peak_plays": top_tracks_peak_plays,
    }


def main():
    # Seleccionar archivo
    filepath = select_file()
    if not filepath:
        return
    
    # Cargar scrobbles
    loader = ScrobblesLoader('data')
    scrobbles = loader.load_file(filepath)
    if not scrobbles:
        print("❌ No se cargaron scrobbles. Saliendo.")
        return
    
    print(f"✓ Se cargaron {len(scrobbles)} scrobbles correctamente")
    
    # Seleccionar fecha de inicio
    start_date = select_start_date()
    
    # Filtrar por fecha si se especificó
    if start_date:
        scrobbles_original = len(scrobbles)
        scrobbles = filter_scrobbles_by_date(scrobbles, start_date)
        print(f"✓ Filtrados a {len(scrobbles)} scrobbles desde {start_date.strftime('%d/%m/%Y')}")
        if len(scrobbles) == 0:
            print("❌ No hay scrobbles posteriores a esa fecha. Saliendo.")
            return
    
    # Seleccionar cantidad de items
    n_items = select_n_items()
    
    # Seleccionar cantidad de días
    n_days, n_peak_plays = select_n_days()
    
    # Seleccionar si dividir por años
    split_by_year = select_split_by_year()
    
    # Calcular estadísticas
    print("\n📊 Calculando estadísticas...")
    
    if split_by_year:
        # Agrupar scrobbles por año y calcular stats para cada año
        from datetime import datetime
        from collections import defaultdict
        
        scrobbles_by_year: Dict[int, List[Scrobble]] = defaultdict(list)
        for scrobble in scrobbles:
            try:
                year = datetime.fromtimestamp(int(scrobble.uts)).year
            except (ValueError, TypeError):
                year = 0
            scrobbles_by_year[year].append(scrobble)
        
        summary_by_year: Dict[int, Dict[str, Any]] = {}
        for year in sorted(scrobbles_by_year.keys(), reverse=True):
            if year == 0:
                continue  # Saltar años inválidos
            print(f"  📅 {year}...", end=" ", flush=True)
            summary_by_year[year] = calculate_summary_for_scrobbles(
                scrobbles_by_year[year],
                n_items, n_days, n_peak_plays
            )
            print("✓")
        
        summary = summary_by_year
    else:
        summary = calculate_summary_for_scrobbles(scrobbles, n_items, n_days, n_peak_plays)

    print("✓ Estadísticas calculadas")
    print("\n📝 Generando calendar.html con resumen...")
    ScrobblesAnalyzer.generate_calendar_html(
        scrobbles, 
        output_file="calendar.html", 
        summary=summary,
        n_items=n_items,
        n_days=n_days,
        n_peak_plays=n_peak_plays,
        split_by_year=split_by_year
    )
    print("✓ Calendario generado: calendar.html")
    # Mostrar información final
    track_per_day = ScrobblesAnalyzer.get_most_played_track_per_day(scrobbles) or {}
    print(f"  Total de días: {len(track_per_day)}")
    print("\n🎉 Abre el archivo en tu navegador para ver el calendario interactivo")


if __name__ == '__main__':
    main()
