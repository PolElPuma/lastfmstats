#!/usr/bin/env python3
"""Test para identificar el bug de reemplazo de canción"""
import sys
sys.path.insert(0, 'src')

from load_scrobbles import Scrobble, ScrobblesAnalyzer
from datetime import datetime, timedelta
import random

def create_realistic_scrobbles():
    """Crea scrobbles realistas donde el último es diferente"""
    scrobbles = []
    base_date = datetime(2024, 1, 1, 0, 0, 0)
    
    tracks_data = [
        ("The Beatles", "Across the Universe", 50),
        ("Pink Floyd", "Comfortably Numb", 40),
        ("David Bowie", "Heroes", 35),
        ("Queen", "Bohemian Rhapsody", 30),
        ("The Rolling Stones", "Paint It Black", 25),
    ]
    
    scrobble_id = 0
    for artist, track, count in tracks_data:
        for i in range(count):
            date_offset = base_date + timedelta(hours=scrobble_id)
            data = {
                'artist': {'#text': artist},
                'name': track,
                'date': {
                    'uts': str(int(date_offset.timestamp())),
                    '#text': date_offset.strftime('%d %b %Y, %H:%M')
                },
                'image': [],
                'url': f'https://example.com/{artist}/{track}'
            }
            scrobbles.append(Scrobble(data))
            scrobble_id += 1
    
    return scrobbles

def test_consistent_results_multiple_calls():
    """Verifica que múltiples llamadas a get_top_tracks retornen lo mismo"""
    print("🧪 Test: Consistencia en múltiples llamadas")
    print("=" * 60)
    
    scrobbles = create_realistic_scrobbles()
    
    # Llamada 1
    top1 = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=3)
    # Llamada 2
    top2 = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=3)
    # Llamada 3
    top3 = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=3)
    
    print(f"Llamada 1: {top1}")
    print(f"Llamada 2: {top2}")
    print(f"Llamada 3: {top3}")
    
    assert top1 == top2 == top3, "❌ Resultados inconsistentes"
    print("✅ Todos los resultados son iguales")


def test_consistency_with_shuffled_input():
    """Verifica que get_top_tracks retorne lo mismo con scrobbles en diferente orden"""
    print("\n🧪 Test: Consistencia con scrobbles desordenados")
    print("=" * 60)
    
    scrobbles = create_realistic_scrobbles()
    
    # Primera ejecución con orden original
    top_original = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=3)
    
    # Desmezclar los scrobbles varias veces
    for shuffle_num in range(5):
        random.shuffle(scrobbles)
        top_shuffled = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=3)
        
        assert top_shuffled == top_original, f"❌ Resultados diferentes después de mezcla {shuffle_num}"
        print(f"  Mezcla {shuffle_num+1}: OK")
    
    print("✅ Resultados consistentes con cualquier orden de entrada")


def test_last_scrobble_not_in_result():
    """Verifica que el último scrobble no aparezca en el top incorrectamente"""
    print("\n🧪 Test: Verificar que último scrobble no reemplaza top")
    print("=" * 60)
    
    scrobbles = create_realistic_scrobbles()
    
    # El último scrobble debe ser "The Rolling Stones - Paint It Black" (1 sola vez)
    last_scrobble = scrobbles[-1]
    print(f"Último scrobble: {last_scrobble.artist} - {last_scrobble.track}")
    
    # Obtener top 3
    top3 = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=3)
    
    print(f"\nTop 3:")
    for i, ((artist, track), count) in enumerate(top3, 1):
        print(f"  {i}. {artist} - {track} ({count})")
        assert count > 1, f"❌ Un track con {count} escuchas no debería estar en top 3"
        assert not (artist == last_scrobble.artist and track == last_scrobble.track), \
            f"❌ El último scrobble apareció en top 3"
    
    print("✅ El último scrobble (1 sola escucha) no está en el top 3")


def test_most_played_track_per_day_consistency():
    """Verifica que get_most_played_track_per_day sea consistente"""
    print("\n🧪 Test: Consistencia en get_most_played_track_per_day")
    print("=" * 60)
    
    scrobbles = create_realistic_scrobbles()
    
    # Primera ejecución
    most_played_1 = ScrobblesAnalyzer.get_most_played_track_per_day(scrobbles)
    
    # Segunda ejecución con scrobbles en diferente orden
    random.shuffle(scrobbles)
    most_played_2 = ScrobblesAnalyzer.get_most_played_track_per_day(scrobbles)
    
    # Comparar
    if most_played_1 and most_played_2:
        for day in most_played_1:
            if day in most_played_2:
                artist1, track1, _, _, _ = most_played_1[day]
                artist2, track2, _, _, _ = most_played_2[day]
                assert artist1 == artist2 and track1 == track2, \
                    f"❌ Día {day}: track cambió de {artist1}-{track1} a {artist2}-{track2}"
    
    print("✅ Resultados consistentes para cada día")


def test_no_object_mutation():
    """Verifica que no haya mutación de objetos compartidos"""
    print("\n🧪 Test: Verificar que no haya mutación de objetos")
    print("=" * 60)
    
    scrobbles = create_realistic_scrobbles()
    
    # Copiar referencia a un scrobble original
    original_last = scrobbles[-1]
    original_last_artist = original_last.artist
    original_last_track = original_last.track
    
    # Hacer operaciones
    top1 = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=3)
    most_played = ScrobblesAnalyzer.get_most_played_track_per_day(scrobbles)
    
    # Verificar que el último scrobble no cambió
    assert scrobbles[-1].artist == original_last_artist, "❌ Artista del último scrobble fue modificado"
    assert scrobbles[-1].track == original_last_track, "❌ Track del último scrobble fue modificado"
    
    print(f"Último scrobble después de operaciones: {scrobbles[-1].artist} - {scrobbles[-1].track}")
    print("✅ Ningún objeto fue mutado")


if __name__ == "__main__":
    try:
        test_consistent_results_multiple_calls()
        test_consistency_with_shuffled_input()
        test_last_scrobble_not_in_result()
        test_most_played_track_per_day_consistency()
        test_no_object_mutation()
        
        print("\n" + "="*60)
        print("✅ TODOS LOS TESTS PASARON")
        print("El bug NO fue reproducido - necesitamos más información")
    except AssertionError as e:
        print(f"\n❌ BUG ENCONTRADO: {e}")
        sys.exit(1)
