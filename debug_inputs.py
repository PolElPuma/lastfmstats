#!/usr/bin/env python3
"""Test simple del primer input"""
import subprocess

inputs = "1\n1\n\n\n\ns\nn\n"
print(f"Inputs a enviar ({len(inputs)} caracteres):")
print(repr(inputs))
print()

proc = subprocess.Popen(
    ["python3", "src/main.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd="/workspaces/lastfmstats"
)

# Enviar inputs y capturar output en tiempo real
for i, line in enumerate(inputs.split("\n")):
    print(f"[Input {i}]: {repr(line)}")

print("\n[Ejecutando...]")
try:
    output, _ = proc.communicate(input=inputs, timeout=120)
    print(output)
except subprocess.TimeoutExpired:
    proc.kill()
    print("❌ TIMEOUT: El proceso se colgó")
    print("Output hasta ahora:")
    print(output.decode() if isinstance(output, bytes) else str(output))
