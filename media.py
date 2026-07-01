import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache

from shared_config import (
    AUDIO_SEGMENT_BITRATE,
    AUDIO_SEGMENT_CHANNELS,
    AUDIO_SEGMENT_FORMAT,
    AUDIO_SEGMENT_SAMPLE_RATE,
    BYTES_PER_MB,
    sanitize_filename,
)

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


TEMP_DIR = os.path.join(tempfile.gettempdir(), "audioscript_contextual")
os.makedirs(TEMP_DIR, exist_ok=True)


def _is_executable_file(path):
    return bool(path and os.path.isfile(path) and os.access(path, os.X_OK))


def _bundle_binary_candidates(binary_name):
    """Construye rutas relativas al código, al bundle y al ejecutable de Python."""
    module_dir = os.path.dirname(os.path.abspath(__file__))
    roots = [module_dir, os.path.dirname(sys.executable)]
    bundle_root = getattr(sys, "_MEIPASS", "")
    if bundle_root:
        roots.insert(0, bundle_root)

    candidates = []
    for root in roots:
        candidates.extend(
            [
                os.path.join(root, binary_name),
                os.path.join(root, "bin", binary_name),
                os.path.join(root, "Resources", binary_name),
                os.path.join(root, "Resources", "bin", binary_name),
            ]
        )
    return candidates


def get_ffmpeg_path():
    """Resuelve ffmpeg sin depender de rutas fijas de Homebrew o del sistema."""
    configured_path = os.environ.get("AUDIOSCRIPT_FFMPEG_PATH", "").strip()
    candidates = [configured_path, *_bundle_binary_candidates("ffmpeg")]
    system_path = shutil.which("ffmpeg")
    if system_path:
        candidates.append(system_path)

    for candidate in candidates:
        if _is_executable_file(candidate):
            return os.path.abspath(candidate)

    if imageio_ffmpeg is not None:
        try:
            imageio_path = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            imageio_path = None
        if _is_executable_file(imageio_path):
            return os.path.abspath(imageio_path)
    return None


@lru_cache(maxsize=1)
def configure_ffmpeg():
    """Expone el ffmpeg resuelto también como `ffmpeg` para Whisper."""
    resolved_ffmpeg = get_ffmpeg_path()
    if not resolved_ffmpeg:
        return None

    resolved_dir = os.path.dirname(resolved_ffmpeg)
    if os.path.basename(resolved_ffmpeg) == "ffmpeg":
        os.environ["PATH"] = f"{resolved_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        return resolved_ffmpeg

    alias_dir = os.path.join(TEMP_DIR, "ffmpeg-bin")
    os.makedirs(alias_dir, exist_ok=True)
    ffmpeg_alias = os.path.join(alias_dir, "ffmpeg")
    if os.path.lexists(ffmpeg_alias):
        alias_target = os.path.realpath(ffmpeg_alias)
        if alias_target != resolved_ffmpeg:
            os.unlink(ffmpeg_alias)
    if not os.path.exists(ffmpeg_alias):
        try:
            os.symlink(resolved_ffmpeg, ffmpeg_alias)
        except OSError:
            shutil.copy2(resolved_ffmpeg, ffmpeg_alias)
            os.chmod(ffmpeg_alias, 0o755)

    os.environ["PATH"] = f"{alias_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    return ffmpeg_alias

def check_ffmpeg():
    """Verifica si ffmpeg está disponible en el sistema o empaquetado."""
    ffmpeg_path = configure_ffmpeg()
    if not ffmpeg_path:
        return False

    try:
        subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def get_ffprobe_path(ffmpeg_path=None):
    """Resuelve ffprobe con la misma política portable usada para ffmpeg."""
    configured_path = os.environ.get("AUDIOSCRIPT_FFPROBE_PATH", "").strip()
    candidates = [configured_path, *_bundle_binary_candidates("ffprobe")]
    if ffmpeg_path:
        candidates.insert(1, os.path.join(os.path.dirname(ffmpeg_path), "ffprobe"))
    system_path = shutil.which("ffprobe")
    if system_path:
        candidates.append(system_path)

    for candidate in candidates:
        if _is_executable_file(candidate):
            return os.path.abspath(candidate)
    return None

def parse_duration_from_ffmpeg_output(output_text):
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output_text or "")
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

def get_media_metadata(file_path):
    """Obtiene metadatos básicos sin depender de librerías adicionales."""
    ffmpeg_path = configure_ffmpeg()
    ffprobe_path = get_ffprobe_path(ffmpeg_path)
    metadata = {
        "size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        "duration_seconds": None,
        "bitrate": "",
        "sample_rate": "",
    }

    if ffprobe_path:
        command = [
            ffprobe_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            probe = json.loads(result.stdout or "{}")
            format_info = probe.get("format", {})
            audio_stream = next(
                (stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"),
                {},
            )
            if format_info.get("duration"):
                metadata["duration_seconds"] = float(format_info["duration"])
            if format_info.get("bit_rate"):
                metadata["bitrate"] = f"{round(int(format_info['bit_rate']) / 1000):,} kbps"
            if audio_stream.get("sample_rate"):
                metadata["sample_rate"] = f"{float(audio_stream['sample_rate']) / 1000:.1f} kHz"
            return metadata
        except Exception:
            pass

    if ffmpeg_path:
        try:
            result = subprocess.run(
                [ffmpeg_path, "-i", file_path],
                capture_output=True,
                text=True,
            )
            metadata["duration_seconds"] = parse_duration_from_ffmpeg_output(
                f"{result.stderr}\n{result.stdout}"
            )
        except Exception:
            pass
    return metadata

def format_duration(seconds):
    if not seconds:
        return "desconocida"
    total_seconds = int(round(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def detect_silence_ranges(file_path, ffmpeg_path, noise_db=-35, min_silence_seconds=0.35):
    """Detecta pausas naturales con ffmpeg para evitar cortes sobre palabras."""
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-nostats",
        "-i",
        file_path,
        "-af",
        f"silencedetect=noise={noise_db}dB:d={min_silence_seconds}",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = f"{result.stderr}\n{result.stdout}"
    starts = [float(value) for value in re.findall(r"silence_start:\s*([0-9.]+)", output)]
    ends = [float(value) for value in re.findall(r"silence_end:\s*([0-9.]+)", output)]

    ranges = []
    for index, start in enumerate(starts):
        if index < len(ends) and ends[index] > start:
            ranges.append((start, ends[index]))
    return ranges

def nearest_silence_cut(target_seconds, silence_ranges, search_window_seconds=8):
    """Devuelve el centro del silencio mas cercano al corte objetivo."""
    best_cut = None
    best_distance = None
    for silence_start, silence_end in silence_ranges:
        center = (silence_start + silence_end) / 2
        distance = abs(center - target_seconds)
        if distance <= search_window_seconds and (best_distance is None or distance < best_distance):
            best_cut = center
            best_distance = distance
    return best_cut

def build_quick_split_cut_points(duration_seconds, file_size, max_segment_mb, use_silence, silence_ranges):
    """Calcula cortes por tamano aproximado y los ajusta a silencios cercanos."""
    if not duration_seconds or duration_seconds <= 0 or not file_size:
        return [], 0

    max_bytes = max_segment_mb * BYTES_PER_MB
    target_seconds = max(60, int((max_bytes / file_size) * duration_seconds))
    cut_points = []
    silence_adjustments = 0
    next_cut = target_seconds

    while next_cut < duration_seconds - 30:
        cut_at = next_cut
        if use_silence and silence_ranges:
            silence_cut = nearest_silence_cut(next_cut, silence_ranges)
            if silence_cut and 20 < silence_cut < duration_seconds - 20:
                cut_at = silence_cut
                silence_adjustments += 1

        if not cut_points or cut_at - cut_points[-1] >= 30:
            cut_points.append(cut_at)
        next_cut += target_seconds

    return cut_points, silence_adjustments

def estimate_quick_split_preview(file_size, max_segment_mb, duration_seconds=None):
    """Genera rangos estimados para previsualizar Quick Split sin procesar audio."""
    max_bytes = max_segment_mb * BYTES_PER_MB
    segment_count = max(1, int((file_size + max_bytes - 1) // max_bytes))
    if duration_seconds and duration_seconds > 0:
        segment_seconds = duration_seconds / segment_count
    else:
        segment_seconds = 0

    segments = []
    for index in range(segment_count):
        start = index * segment_seconds if segment_seconds else None
        end = min((index + 1) * segment_seconds, duration_seconds) if segment_seconds else None
        if index == segment_count - 1:
            estimated_size = max(1, file_size - (max_bytes * index))
        else:
            estimated_size = min(max_bytes, file_size)
        segments.append(
            {
                "index": index + 1,
                "start": start,
                "end": end,
                "size_bytes": estimated_size,
            }
        )
    return segments


def build_ffmpeg_error_message(action_label, exc):
    """Resume el motivo real informado por ffmpeg en un RuntimeError legible."""
    stderr_text = (exc.stderr or exc.stdout or "").strip()
    if stderr_text:
        detail_lines = [line for line in stderr_text.splitlines() if line.strip()]
        detail_tail = "\n".join(detail_lines[-15:])
        return f"No pude {action_label}.\n\nDetalle de ffmpeg:\n{detail_tail}"
    return f"No pude {action_label}. ffmpeg devolvió el código {exc.returncode}."


def build_ffmpeg_segment_command(
    ffmpeg_path,
    file_path,
    output_target,
    *,
    start_time=None,
    end_time=None,
    segment_seconds=None,
    segment_start_number=1,
):
    """Construye el comando base de ffmpeg reutilizado por ambos modos de división."""
    command = [ffmpeg_path, "-y"]
    if start_time is not None:
        command.extend(["-ss", f"{start_time:.3f}"])
    if end_time is not None:
        command.extend(["-to", f"{end_time:.3f}"])
    command.extend(
        [
            "-i",
            file_path,
            "-vn",
            "-map",
            "0:a:0",
        ]
    )
    if segment_seconds is not None:
        command.extend(
            [
                "-f",
                "segment",
                "-segment_time",
                str(segment_seconds),
                "-segment_start_number",
                str(segment_start_number),
                "-reset_timestamps",
                "1",
            ]
        )
    command.extend(
        [
            "-ac",
            AUDIO_SEGMENT_CHANNELS,
            "-ar",
            AUDIO_SEGMENT_SAMPLE_RATE,
            "-b:a",
            AUDIO_SEGMENT_BITRATE,
            output_target,
        ]
    )
    return command


def _prepare_segment_output_dir(output_dir):
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)


def _run_ffmpeg_segment(command, action_label):
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(build_ffmpeg_error_message(action_label, exc)) from exc


def _repair_audio_source(file_path):
    """Normaliza un flujo dañado omitiendo cuadros ilegibles antes de segmentarlo."""
    ffmpeg_path = configure_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("No pude activar ffmpeg para reparar el audio.")

    handle, repaired_path = tempfile.mkstemp(
        prefix="audioscript_repaired_",
        suffix=".wav",
        dir=TEMP_DIR,
    )
    os.close(handle)
    command = [
        ffmpeg_path,
        "-y",
        "-fflags",
        "+discardcorrupt",
        "-err_detect",
        "ignore_err",
        "-i",
        file_path,
        "-vn",
        "-map",
        "0:a:0",
        "-af",
        "aresample=async=1:first_pts=0",
        "-ac",
        AUDIO_SEGMENT_CHANNELS,
        "-ar",
        AUDIO_SEGMENT_SAMPLE_RATE,
        "-c:a",
        "pcm_s16le",
        repaired_path,
    ]
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        if not os.path.exists(repaired_path) or os.path.getsize(repaired_path) <= 44:
            raise RuntimeError("ffmpeg no pudo recuperar audio utilizable del archivo.")
        return repaired_path
    except subprocess.CalledProcessError as exc:
        if os.path.exists(repaired_path):
            os.unlink(repaired_path)
        raise RuntimeError(build_ffmpeg_error_message("reparar el audio dañado", exc)) from exc


def split_media(
    file_path,
    output_dir,
    output_pattern,
    *,
    action_label,
    segment_seconds=None,
    time_ranges=None,
):
    """Motor único para generar segmentos por duración o por rangos calculados."""
    ffmpeg_path = configure_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("No pude activar ffmpeg para dividir el material.")
    if bool(segment_seconds) == bool(time_ranges):
        raise ValueError("Indica segment_seconds o time_ranges, pero no ambos.")

    _prepare_segment_output_dir(output_dir)
    if time_ranges:
        output_files = []
        for index, (start, end) in enumerate(time_ranges, start=1):
            output_path = output_pattern % index
            command = build_ffmpeg_segment_command(
                ffmpeg_path,
                file_path,
                output_path,
                start_time=start,
                end_time=end,
            )
            _run_ffmpeg_segment(command, action_label)
            output_files.append(output_path)
        return output_files

    command = build_ffmpeg_segment_command(
        ffmpeg_path,
        file_path,
        output_pattern,
        segment_seconds=segment_seconds,
        segment_start_number=1,
    )
    _run_ffmpeg_segment(command, action_label)
    glob_pattern = re.sub(r"%0?\d*d", "*", output_pattern)
    return sorted(glob.glob(glob_pattern))

def split_large_media_by_size(file_path, original_name, max_segment_mb, output_dir, use_silence=True):
    """Divide un archivo grande en segmentos temporales compatibles con Whisper."""
    ffmpeg_path = configure_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("No pude activar ffmpeg para dividir el archivo.")

    metadata = get_media_metadata(file_path)
    file_size = metadata["size_bytes"]
    segment_count = max(1, int((file_size + (max_segment_mb * BYTES_PER_MB) - 1) // (max_segment_mb * BYTES_PER_MB)))
    duration = metadata.get("duration_seconds")
    segment_seconds = max(60, int((duration or segment_count * 600) / segment_count) + 1)

    safe_base = sanitize_filename(
        os.path.splitext(original_name)[0],
        preserve_extension=False,
        default_name="archivo",
    )
    silence_ranges = []
    silence_adjustments = 0
    cut_points = []
    if duration:
        if use_silence:
            silence_ranges = detect_silence_ranges(file_path, ffmpeg_path)
        cut_points, silence_adjustments = build_quick_split_cut_points(
            duration,
            file_size,
            max_segment_mb,
            use_silence,
            silence_ranges,
        )

    output_pattern = os.path.join(output_dir, f"{safe_base}_parte%03d.{AUDIO_SEGMENT_FORMAT}")
    time_ranges = None
    if cut_points:
        time_ranges = list(zip([0] + cut_points, cut_points + [duration]))
    segment_files = split_media(
        file_path,
        output_dir,
        output_pattern,
        action_label="dividir el archivo grande",
        segment_seconds=None if time_ranges else segment_seconds,
        time_ranges=time_ranges,
    )
    metadata["silence_ranges_count"] = len(silence_ranges)
    metadata["silence_adjustments"] = silence_adjustments
    metadata["used_silence_detection"] = bool(use_silence and silence_ranges)
    return segment_files, metadata

def split_audio(file_path, segment_mins, output_dir, output_format=AUDIO_SEGMENT_FORMAT):
    """Divide el audio en fragmentos ligeros de N minutos compatibles con Whisper."""
    segment_seconds = int(segment_mins * 60)
    chunk_pattern = os.path.join(output_dir, f"chunk_%03d.{output_format}")

    def split_source(source_path):
        duration = get_media_metadata(source_path).get("duration_seconds")
        time_ranges = None
        if duration and duration > 0:
            time_ranges = []
            start = 0.0
            while start < duration - 0.01:
                end = min(start + segment_seconds, duration)
                time_ranges.append((start, end))
                start = end
        return split_media(
            source_path,
            output_dir,
            chunk_pattern,
            action_label="dividir el audio",
            segment_seconds=None if time_ranges else segment_seconds,
            time_ranges=time_ranges,
        )

    try:
        return split_source(file_path)
    except RuntimeError as original_error:
        repaired_path = None
        try:
            repaired_path = _repair_audio_source(file_path)
            recovered_chunks = split_source(repaired_path)
            if recovered_chunks:
                return recovered_chunks
        except RuntimeError as repair_error:
            raise RuntimeError(
                "El archivo contiene datos de audio dañados y no pude recuperarlos automáticamente. "
                "Prueba convertirlo a WAV o M4A y vuelve a cargarlo."
            ) from repair_error
        finally:
            if repaired_path and os.path.exists(repaired_path):
                os.unlink(repaired_path)
        raise original_error
