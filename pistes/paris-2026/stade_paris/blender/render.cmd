@echo off
rem Rendu des vues de contrôle. Usage : blender\render.cmd [vues séparées par +|all] [résolution] [échantillons]
rem Blender est appelé via un chemin court (jonction) : le dossier de travail dépasse la limite MAX_PATH de certaines DLL.
setlocal
set ROOT=C:\Users\basil\AppData\Local\Temp\plda
set BLENDER=C:\Users\basil\AppData\Local\Temp\bl45\blender.exe
set VIEWS=%1
if "%VIEWS%"=="" set VIEWS=all
set RES=%2
if "%RES%"=="" set RES=1600x900
set SPP=%3
if "%SPP%"=="" set SPP=32
"%BLENDER%" -b --factory-startup -P "%ROOT%\blender\render_views.py" -- --root "%ROOT%" --views %VIEWS% --res %RES% --samples %SPP% > "%ROOT%\build\render_log.txt" 2>&1
echo exit=%ERRORLEVEL%
