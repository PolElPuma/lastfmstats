#!/usr/bin/env python3
"""Script para probar el flujo interactivo"""
import sys
import subprocess
import time

# Test 1: Flujo simple sin tiempo
print("=" * 60)
print("Test 1: Flujo sin estadísticas de tiempo")
print("=" * 60)

inputs1 = "1\n1\n\n\n\ns\nn\n"
proc1 = subprocess.Popen(
    ["python3", "src/main.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd="/workspaces/lastfmstats"
)

try:
    output1, _ = proc1.communicate(input=inputs1, timeout=60)
    if "✓ Calendario generado" in output1:
        print("✅ Test 1 PASSED: Calendario generado correctamente")
    else:
        print("❌ Test 1 FAILED")
        print("Last 30 lines:")
        print("\n".join(output1.split("\n")[-30:]))
except subprocess.TimeoutExpired:
    proc1.kill()
    print("❌ Test 1 TIMEOUT: Proceso excedió 60 segundos")

time.sleep(2)

# Test 2: Flujo con tiempo (cuidado, puede tardar)
print("\n" + "=" * 60)
print("Test 2: Flujo CON estadísticas de tiempo (puede tardar)")
print("=" * 60)

inputs2 = "1\n1\n\n\n\ns\ns\n"
proc2 = subprocess.Popen(
    ["python3", "src/main.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd="/workspaces/lastfmstats"
)

try:
    # Timeout más largo para permitir que haga llamadas a API
    output2, _ = proc2.communicate(input=inputs2, timeout=300)
    if "✓ Calendario generado" in output2:
        print("✅ Test 2 PASSED: Calendario generado con estadísticas de tiempo")
        # Contar llamadas a API
        api_calls = output2.count("[API duration]")
        print(f"   Llamadas a API realizadas: {api_calls}")
    else:
        print("❌ Test 2 FAILED")
        print("Last 30 lines:")
        print("\n".join(output2.split("\n")[-30:]))
except subprocess.TimeoutExpired:
    proc2.kill()
    print("❌ Test 2 TIMEOUT: Proceso excedió 300 segundos")
    print("Esto es normal si hace muchas llamadas a API con rate limiting")

print("\n✓ Tests completados")
