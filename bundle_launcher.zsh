#!/bin/zsh

set -u

APP_ROOT="${0:A:h:h}"
RESOURCES_DIR="$APP_ROOT/Resources"
RUNTIME_BIN="$RESOURCES_DIR/runtime/audioscript_runtime"
SUPPORT_DIR="$HOME/Library/Application Support/AudioScript Contextual"
DATA_DIR="$SUPPORT_DIR/Projects"
STREAMLIT_CONFIG_DIR="$SUPPORT_DIR/.streamlit"
LOG_DIR="$HOME/Library/Logs/AudioScript Contextual"
LOG_FILE="$LOG_DIR/launcher.log"

mkdir -p "$SUPPORT_DIR" "$DATA_DIR" "$STREAMLIT_CONFIG_DIR" "$LOG_DIR"
exec >>"$LOG_FILE" 2>&1

show_dialog() {
  /usr/bin/osascript -e "display dialog \"$1\" buttons {\"OK\"} default button \"OK\" with title \"AudioScript Contextual\"" >/dev/null
}

find_port() {
  local port
  for port in {8501..8599}; do
    if ! /usr/sbin/lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "$port"
      return 0
    fi
  done
  return 1
}

echo "---- $(date) ----"
echo "Starting AudioScript Contextual Beta 0.9"

if [ "$(/usr/bin/uname -m)" != "arm64" ]; then
  show_dialog "Esta beta requiere una Mac con Apple Silicon (M1, M2, M3, M4 o M5) y macOS 13 Ventura o superior."
  exit 1
fi

if [ ! -x "$RUNTIME_BIN" ]; then
  show_dialog "La instalación está incompleta. Vuelve a copiar AudioScript Contextual desde el DMG."
  exit 1
fi

export AUDIOSCRIPT_RESOURCES_DIR="$RESOURCES_DIR"
export AUDIOSCRIPT_DATA_DIR="$DATA_DIR"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false
export STREAMLIT_THEME_BASE=light
export NO_PROXY="localhost,127.0.0.1"
export no_proxy="$NO_PROXY"

if ! "$RUNTIME_BIN" --self-test; then
  show_dialog "No pude verificar los componentes internos de AudioScript. Consulta el archivo de diagnóstico en Biblioteca/Logs/AudioScript Contextual."
  exit 1
fi

PORT="$(find_port)" || {
  show_dialog "No encontré un puerto local disponible para abrir AudioScript."
  exit 1
}
export AUDIOSCRIPT_STREAMLIT_PORT="$PORT"

cat > "$STREAMLIT_CONFIG_DIR/config.toml" <<CONFIG
[browser]
gatherUsageStats = false
serverAddress = "localhost"

[client]
toolbarMode = "minimal"

[theme]
base = "light"

[server]
headless = true
address = "localhost"
port = $PORT
maxUploadSize = 2048
CONFIG

APP_URL="http://localhost:$PORT"
cd "$SUPPORT_DIR"
"$RUNTIME_BIN" &
STREAMLIT_PID="$!"

READY=0
for attempt in {1..60}; do
  if /usr/bin/curl --silent --fail "$APP_URL/_stcore/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  if ! /bin/kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    break
  fi
  /bin/sleep 1
done

if [ "$READY" != "1" ]; then
  show_dialog "AudioScript no pudo iniciar. Consulta el archivo de diagnóstico en Biblioteca/Logs/AudioScript Contextual."
  wait "$STREAMLIT_PID" 2>/dev/null
  exit 1
fi

/usr/bin/open "$APP_URL" >/dev/null 2>&1
wait "$STREAMLIT_PID"
