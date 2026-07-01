# AudioScript Contextual Beta 0.9 para Mac

Esta beta está preparada exclusivamente para computadoras Mac con Apple Silicon
(M1, M2, M3, M4 o M5) y macOS 13 Ventura o posterior.

## Qué incluye la aplicación

El bundle incorpora Python, Streamlit, Whisper, Torch, ffmpeg y los componentes
necesarios para transcribir, dividir audios y exportar documentos. No requiere
Homebrew, Terminal ni una instalación previa de Python.

El modelo de Whisper no viene dentro del DMG. Durante el primer inicio podrás
elegir Medium, recomendado para la beta, o Large. Esa es la única descarga
necesaria para usar AudioScript.

## Instalación

1. Abre el archivo `AudioScript_Beta.dmg`.
2. Arrastra `AudioScript Contextual.app` a la carpeta Aplicaciones.
3. Abre Aplicaciones, haz clic derecho sobre AudioScript Contextual y elige `Abrir`.
4. Si aparece el aviso `Apple no pudo verificar...`, pulsa `Listo`; no elijas
   `Mover al basurero`.
5. Abre `Ajustes del Sistema` > `Privacidad y seguridad`.
6. Desplázate hasta la sección `Seguridad`. Junto al aviso de que AudioScript fue
   bloqueado, pulsa `Abrir de todos modos`.
7. Autoriza con Touch ID o con la contraseña de la Mac y confirma nuevamente `Abrir`.
8. Sigue la instalación guiada y elige el modelo Medium o Large.
9. Mantén conexión a internet hasta que termine la descarga del modelo.

El botón `Abrir de todos modos` aparece después de intentar abrir la app al menos
una vez. Si no aparece, vuelve a Aplicaciones, intenta abrir AudioScript y regresa
inmediatamente a `Privacidad y seguridad`.

## Privacidad y funcionamiento local

Después de descargar el modelo, la transcripción se ejecuta dentro de la Mac. Los
audios, videos, transcripciones, memos y códigos permanecen en almacenamiento local
y no se envían a un servidor de AudioScript.

Puedes desconectar internet después de completar la descarga inicial y continuar
transcribiendo. AudioScript abre una página `localhost` en el navegador; esa página
pertenece a la aplicación que está ejecutándose en tu propia computadora.

## Modelos disponibles

- `Medium`: opción recomendada. Equilibra precisión, velocidad y uso de memoria.
- `Large`: puede mejorar audios difíciles, pero requiere más espacio, memoria y tiempo.

Los modelos se guardan en:

```text
~/Library/Application Support/AudioScript Contextual/whisper_models
```

## Proyectos y archivos locales

Los proyectos se guardan en:

```text
~/Library/Application Support/AudioScript Contextual/Projects
```

La aplicación no borra los archivos originales elegidos por la persona usuaria.

## Abrir y cerrar

Abre AudioScript desde Aplicaciones o desde su icono en el Dock. Para cerrar el
servidor local, usa `Salir` sobre el icono de AudioScript o cierra la aplicación.

## Si la aplicación no abre

1. Comprueba que la Mac tenga Apple Silicon y macOS 13 o posterior.
2. Abre Aplicaciones y usa clic derecho > `Abrir`.
3. Revisa el diagnóstico local:

```text
~/Library/Logs/AudioScript Contextual/launcher.log
```

No compartas audios ni transcripciones al reportar un error. Basta con describir
la acción realizada, copiar el mensaje visible y señalar la versión de macOS.
