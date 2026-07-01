#!/bin/zsh

set -euo pipefail

ROOT_DIR="${0:A:h}"
APP_NAME="AudioScript Contextual.app"
BUNDLE_DIR="$ROOT_DIR/dist/$APP_NAME"
CONTENTS_DIR="$BUNDLE_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
RUNTIME_BUILD_DIR="$ROOT_DIR/build/pyinstaller-runtime"
RUNTIME_DIST_DIR="$ROOT_DIR/build/pyinstaller-dist"
BUILD_PYTHON="${AUDIOSCRIPT_BUILD_PYTHON:-$HOME/Library/Application Support/AudioScript Contextual/.venv/bin/python}"
ICON_SOURCE="$ROOT_DIR/assets/AppIcon.icns"

SOURCE_FILES=(
  "App.py"
  "data_model.py"
  "media.py"
  "shared_config.py"
  "styles.py"
  "transcribe.py"
  "ui_components.py"
  "requirements.txt"
)

if [ "$(/usr/bin/uname -m)" != "arm64" ]; then
  echo "El bundle beta solo puede construirse desde una Mac Apple Silicon." >&2
  exit 1
fi

if [ ! -x "$BUILD_PYTHON" ]; then
  echo "No encuentro el Python de compilación: $BUILD_PYTHON" >&2
  exit 1
fi

if ! "$BUILD_PYTHON" -c 'import PyInstaller' >/dev/null 2>&1; then
  echo "Instala PyInstaller en el entorno de compilación antes de continuar." >&2
  exit 1
fi

echo "Construyendo runtime autosuficiente para Apple Silicon"
rm -rf "$RUNTIME_BUILD_DIR" "$RUNTIME_DIST_DIR"
mkdir -p "$RUNTIME_BUILD_DIR" "$RUNTIME_DIST_DIR"

"$BUILD_PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --onedir \
  --name audioscript_runtime \
  --target-architecture arm64 \
  --distpath "$RUNTIME_DIST_DIR" \
  --workpath "$RUNTIME_BUILD_DIR/work" \
  --specpath "$RUNTIME_BUILD_DIR" \
  --collect-all streamlit \
  --collect-all whisper \
  --collect-all imageio_ffmpeg \
  --collect-all tiktoken \
  --collect-data docx \
  --copy-metadata streamlit \
  --copy-metadata openai-whisper \
  --copy-metadata torch \
  --copy-metadata pandas \
  "$ROOT_DIR/bundle_runtime.py"

echo "Ensamblando $APP_NAME"
rm -rf "$BUNDLE_DIR"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR/runtime"

for file_name in "${SOURCE_FILES[@]}"; do
  cp "$ROOT_DIR/$file_name" "$RESOURCES_DIR/$file_name"
done

rsync -a --exclude='.DS_Store' --exclude='._*' "$ROOT_DIR/assets/" "$RESOURCES_DIR/assets/"
rsync -a --exclude='.DS_Store' --exclude='._*' "$RUNTIME_DIST_DIR/audioscript_runtime/" "$RESOURCES_DIR/runtime/"

cp "$ROOT_DIR/bundle_launcher.zsh" "$MACOS_DIR/AudioScript Contextual"
chmod +x "$MACOS_DIR/AudioScript Contextual" "$RESOURCES_DIR/runtime/audioscript_runtime"

if [ -f "$ICON_SOURCE" ]; then
  cp "$ICON_SOURCE" "$RESOURCES_DIR/AppIcon.icns"
fi

cat > "$CONTENTS_DIR/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>es</string>
  <key>CFBundleDisplayName</key>
  <string>AudioScript Contextual</string>
  <key>CFBundleExecutable</key>
  <string>AudioScript Contextual</string>
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
  <key>CFBundleIdentifier</key>
  <string>mx.tmarquez.audioscript</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>AudioScript Contextual</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.9.0-beta</string>
  <key>CFBundleVersion</key>
  <string>0.9.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
  <key>LSArchitecturePriority</key>
  <array><string>arm64</string></array>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
PLIST

plutil -lint "$CONTENTS_DIR/Info.plist"
"$RESOURCES_DIR/runtime/audioscript_runtime" --self-test
codesign --force --deep --sign - "$BUNDLE_DIR"

echo "Bundle autosuficiente actualizado en: $BUNDLE_DIR"
