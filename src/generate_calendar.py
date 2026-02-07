#!/usr/bin/env python3
"""
Script para generar un calendario visual HTML con las canciones más escuchadas cada día
"""

from load_scrobbles import (
    ScrobblesLoader,
    ScrobblesAnalyzer
)


def main():
    print("\n" + "="*80)
    print("GENERADOR DE CALENDARIO - ESCUCHAS POR DÍA")
    print("="*80)
    
    # Cargar scrobbles
    loader = ScrobblesLoader('data')
    files = loader.list_files()
    
    if not files:
        print("❌ No se encontraron archivos de scrobbles")
        return
    
    print(f"\nCargando: {files[1]}")
    scrobbles = loader.load_file(files[1])
    
    if not scrobbles:
        print("❌ No se pudieron cargar los scrobbles")
        return
    
    print(f"✓ Se cargaron {len(scrobbles)} scrobbles")
    
    # Generar calendario
    print("\nGenerando calendario HTML... (no se descargarán imágenes; solo referencias a URLs)")
    ScrobblesAnalyzer.generate_calendar_html(scrobbles, output_file="calendar.html")
    
    print("\n" + "="*80)
    print("¡Calendario generado exitosamente!")
    print("Abre 'calendar.html' en tu navegador para ver el resultado")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
