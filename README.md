# AudioScript Contextual

## Transcripción inmersiva potenciada por IA

> Tu ritmo. Tu profundidad. Tus datos.

**Beta de escritorio disponible para evaluación.** Actualización del 15 de noviembre de 2026: versión 0.9.5.0, compilación **2026.11.15.2**. No es una versión estable ni una garantía de transcripción sin errores.

**[Descargar el instalador y consultar las notas](https://github.com/tmarquez-mx/audioscript/releases/tag/v0.9.5.0)** · [Descarga directa del DMG](https://github.com/tmarquez-mx/audioscript/releases/download/v0.9.5.0/AudioScript_0.9.5.dmg) · [Verificación SHA-256](https://github.com/tmarquez-mx/audioscript/releases/download/v0.9.5.0/AudioScript_0.9.5.dmg.sha256)

**Requisitos: Mac con Apple Silicon y macOS 14 Sonoma o posterior.** Este instalador no es compatible con Intel, Windows ni macOS 13 Ventura. La página de la versión conserva su dirección; la compilación identifica el instalador actualizado.

## Propósito

AudioScript Contextual acompaña la transcripción como parte del análisis cualitativo. Escuchar, corregir, anotar, codificar e interpretar forman parte de una misma práctica metodológica, no de etapas necesariamente separadas.

La transcripción manual favorece la familiaridad con los datos, pero demanda tiempo. La transcripción automática acelera la producción de un borrador, pero requiere revisión. AudioScript articula ambas: aprovecha la rapidez del cómputo sin desplazar el control cognitivo y metodológico de quien investiga. La IA genera texto preliminar; la persona contrasta, corrige e interpreta.

## Privacidad y trabajo sin conexión

- El reconocimiento de voz se ejecuta en la computadora mediante Whisper. Las entrevistas no se envían a un servicio de transcripción en la nube.
- La descarga inicial de los modelos requiere internet. Con los recursos instalados, se puede transcribir sin conexión.
- Los proyectos, transcripciones, códigos y memos se guardan localmente. El instalador no incluye entrevistas, proyectos personales ni modelos descargados.
- El procesamiento local no sustituye el cuidado del equipo, los respaldos ni la revisión de lo que se comparte. Las exportaciones ordinarias pueden conservar datos identificables.

## Funciones disponibles

### Preparar y escuchar

Crea proyectos y agrega materiales de audio o video. Elige idioma, modelo Whisper y duración de los segmentos. El valor inicial es cinco minutos; puedes ajustarlo. Para archivos grandes, Quick Split permite crear partes persistentes. La capacidad efectiva depende del equipo, el espacio disponible y los límites de carga; no se promete tamaño ilimitado.

Los segmentos se pueden trabajar en cualquier orden: avanzar, volver a uno anterior o contrastar fragmentos para interpretar su sentido. El modo completo está orientado a audios cortos.

### Revisar y contextualizar

Edita el borrador mientras escuchas. La barra de selección permite aplicar negritas, subrayado, resaltado y tachado, o llevar una frase al campo de codificación. La ficha registra título, fecha y contexto. El diccionario de hablantes permite definir etiquetas, roles, alias y observaciones compartidas entre los materiales del proyecto.

El diccionario es supervisado: **no equivale a diarización automática**. Insertar etiquetas o elegir una preferencia de confidencialidad no sustituye nombres ya escritos ni anonimiza el audio.

### Analizar durante la transcripción

Registra citas codificadas y memos con nombre, fecha, tipo y segmento vinculado. Los tipos de memo son analítico, teórico y metodológico. Códigos y memos se autoguardan al completar y confirmar sus campos. Los avisos de error de guardado requieren atención antes de cerrar la sesión.

### Preparar una copia anonimizada

La anonimización local supervisada propone datos para revisar y permite añadir otros. Decide conservar, sustituir por texto o aplicar una franja negra, en una aparición o en todas las coincidencias del mismo dato. Revisa la copia completa antes de descargarla en TXT o Word.

La franja elimina el dato de la copia: no lo oculta debajo de una capa gráfica. El original permanece intacto. La copia no incluye audio, ficha, bibliografía, memos ni citas codificadas. La detección no es exhaustiva y el contexto puede seguir identificando a alguien; no se garantiza anonimato automático.

## Exportaciones

| Formato | Contenido y uso |
| --- | --- |
| Word limpio | Transcripción para lectura continua. |
| Word contextual | Transcripción, ficha y análisis disponible. |
| TXT | Texto de trabajo. |
| Excel | Tablas de memos y códigos, con detalle de citas codificadas. |
| QDC | Diccionario de códigos; no es un proyecto completo. |
| QDPX | Transcripción, citas codificadas y memos para QualCoder; no incluye audio. |
| RIS | Metadatos de la entrevista para Zotero; no incluye la transcripción completa. |

Puedes exportar avances sin terminar todos los segmentos. QDPX requiere que las citas sigan coincidiendo con el texto; si lo corriges, revisa las codificaciones. La compatibilidad con otros programas de análisis cualitativo no se presume equivalente a la comprobada con QualCoder. Una exportación no sustituye el respaldo del proyecto completo.

## Instalar y consultar el manual

1. Respalda tus proyectos y materiales y cierra la versión anterior.
2. Descarga y abre el DMG. Arrastra AudioScript Contextual a Applications.
3. Abre la app desde Aplicaciones, no desde el disco de instalación.
4. Completa la preparación inicial y descarga el modelo si aún no está instalado.

La app tiene **firma local ad hoc, sin notarización de Apple**. macOS puede mostrar un aviso de seguridad.

El **manual gráfico PDF de 13 páginas** está incluido en el DMG y se descarga también desde **Guía de uso > Manual gráfico (PDF)**. Usa capturas con datos sintéticos. Pasa el cursor por los botones para leer sus ayudas.

## Estado del desarrollo

La compilación publicada se probó en macOS 26.6.2 con Apple Silicon: arranque instalado, ayudas, descarga del manual, reproducción, transcripción real de audio sintético con Whisper tiny, autoguardado, códigos, memos, exportaciones y reapertura del proyecto. Esto no equivale a una validación en todas las versiones de macOS compatibles ni a una garantía de precisión para cualquier grabación.

Los módulos Python propios del instalador se distribuyen como bytecode, sin sus archivos `.py` legibles. Esto no es cifrado ni impide la ingeniería inversa. Las dependencias de terceros conservan sus avisos y licencias.

**Los archivos históricos de este repositorio no representan el código de la compilación actual.** Para instalar, utiliza los archivos de la publicación enlazada arriba. La versión actual no ofrece una aplicación web alojada, procesamiento remoto o híbrido, diarización automática ni instaladores para Windows o Mac Intel.

## Marco metodológico

Transcribir no es copiar el habla, sino interpretarla. Ochs (1979) sitúa la transcripción en relación con los intereses teóricos de quien investiga: qué aspectos de una interacción se atienden y cómo se representan. No es un registro neutro, sino una práctica selectiva (Bucholtz, 2000). Decidir qué pausas marcar, cómo representar un solapamiento o qué conservar del contexto es ya una decisión analítica.

Desde esta perspectiva, el control humano sobre el material empírico forma parte del rigor de la investigación cualitativa y de sus condiciones de credibilidad y confirmabilidad (Lincoln y Guba, 1985). AudioScript no busca automatizar la interpretación, sino sostener las condiciones para ejercerla durante la escucha y la revisión.

Se orienta a entrevistas, grupos focales, trabajo etnográfico, formación de posgrado, análisis inductivo de discurso y construcción de corpus cualitativos. Forma parte de una línea de trabajo sobre el uso reflexivo y crítico de la IA en investigación y docencia en ciencias sociales y humanidades.

## Referencias

Bucholtz, M. (2000). The politics of transcription. *Journal of Pragmatics, 32*(10), 1439-1465.

Lincoln, Y. S. y Guba, E. G. (1985). *Naturalistic inquiry*. Sage.

Ochs, E. (1979). Transcription as theory. En E. Ochs y B. B. Schieffelin (Eds.), *Developmental pragmatics* (pp. 43-72). Academic Press.

## Autoría

Dra. Teresa Márquez

IBERO, Ciencias Sociales y Políticas

[Techiholic Labs](https://techiholic.netlify.app/) · [Sitio de AudioScript Contextual](https://techiholic.netlify.app/audioscript_contextual)
