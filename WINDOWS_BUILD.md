# Compilar el ejecutable de Windows

Esta guía explica cómo generar un `.exe` de Last.fm Stats desde una máquina Windows usando PyInstaller.

## Requisitos

- Windows 10 o 11
- Python 3.9+ recomendado
- Conexión a Internet para instalar dependencias
- El repositorio clonado en la máquina Windows

## 1) Instalar Python

1. Descarga Python desde https://www.python.org/downloads/windows/
2. Asegúrate de marcar `Add Python to PATH`
3. Comprueba que funciona:

```powershell
python --version
```

## 2) Abrir PowerShell en la raíz del proyecto

Desde la carpeta del repositorio:

```powershell
cd C:\ruta\a\lastfmstats
```

## 3) Instalar dependencias

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
```

## 4) Compilar el ejecutable

Opción rápida:

```powershell
build_windows.bat
```

Opción manual:

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name LastFMStats --paths "%CD%\src" "%CD%\src\gui.py"
```

El ejecutable se generará en:

```text
\dist\LastFMStats.exe
```

## 5) Ejecutar el programa

```powershell
.\dist\LastFMStats.exe
```

## 6) Observaciones importantes

- La compilación debe hacerse en Windows. PyInstaller no genera un `.exe` de Windows desde Linux/macOS.
- El programa usa una caché local para datos y duraciones de canciones. En una instalación normal, eso se guarda en:

```text
%LOCALAPPDATA%\LastFMStats\data
```

- Si quieres una versión más portable, puedes compartir la carpeta `dist` junto con la estructura mínima que necesite la app.

## 7) Solución de problemas

### Error de PyInstaller no encontrado

```powershell
python -m pip install pyinstaller
```

### Error de dependencias faltantes

```powershell
python -m pip install -r requirements.txt
```

### Proyecto no se abre en Windows

Comprueba que el archivo `build_windows.bat` esté en la raíz y que `src\gui.py` exista.

## 8) Alternativa recomendada

Para una experiencia mínima sin instalar más herramientas, usa directamente:

```powershell
python src\gui.py
```

Eso te permite probar la interfaz gráfica antes de empaquetar la versión final.
