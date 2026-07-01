# AudioScript Contextual

Aplicación local para transcripción inmersiva, memoing y codificación cualitativa
asistida por Whisper, pensada para entrevistas, grupos focales, clases, diarios de
campo y trabajo interpretativo.

## Estado actual

AudioScript Contextual se distribuye actualmente como una beta para macOS Apple
Silicon mediante un archivo `.dmg`.

Versión beta distribuible: [tmarquez-mx/audioscript](https://github.com/tmarquez-mx/audioscript)

## Qué hace

- Transcribe audio y video localmente con Whisper.
- Permite trabajar por segmentos o en modo completo.
- Facilita memoing y codificación desde la misma interfaz.
- Exporta a `TXT`, `DOCX`, `XLSX` y `QDC`.
- Divide materiales grandes en segmentos para mantener un flujo de trabajo estable.

## Privacidad

La prioridad de AudioScript Contextual es la protección de datos.

- La aplicación corre en tu propia Mac.
- Los audios, videos, transcripciones, memos y códigos se mantienen en almacenamiento local.
- No se envían archivos a un servidor de AudioScript.
- La única descarga inicial es el modelo de Whisper elegido por la persona usuaria.
- Después de esa descarga, la app puede seguir funcionando sin conexión.

## Requisitos

- Mac con Apple Silicon: `M1`, `M2`, `M3`, `M4` o `M5`
- macOS `13 Ventura` o posterior
- Conexión a internet solo para la descarga inicial del modelo Whisper

## Instalación rápida

1. Descarga `AudioScript_Beta.dmg` desde la sección de Releases.
2. Abre el `.dmg`.
3. Arrastra `AudioScript Contextual.app` a `Aplicaciones`.
4. Abre la app desde `Aplicaciones`.
5. Si macOS muestra un aviso de seguridad, intenta abrirla una vez y luego ve a:
   `Ajustes del Sistema` > `Privacidad y seguridad` > `Abrir de todos modos`.
6. Sigue la instalación guiada y elige el modelo Whisper inicial.

## Modelos Whisper

- `Medium`: recomendado para la beta. Equilibra precisión, velocidad y tamaño.
- `Large`: útil para audios más difíciles, pero tarda más y ocupa más espacio.

La descarga del modelo ocurre una sola vez. Después, el modelo corre localmente en
la Mac.

## Archivos de la aplicación

Los proyectos y recursos locales se guardan en:

```text
~/Library/Application Support/AudioScript Contextual
```

## Documentación para testers

Consulta la guía detallada en:

- [GUIA_BETA_MAC.md](/Users/teresamarquez/Documents/unir%202%20codigos/GUIA_BETA_MAC.md)

## Estado de la beta

Esta versión es una beta distribuible, todavía no firmada ni notarizada por Apple.
Por eso macOS puede mostrar avisos de seguridad durante la instalación inicial.

## Pendientes

Queda pendiente preparar:

- una infografía de instalación y privacidad
- una futura distribución firmada/notarizada para macOS
