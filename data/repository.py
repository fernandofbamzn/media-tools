"""Repositorio de acceso a archivos multimedia."""

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from clibaseapp.exceptions import BinaryMissingError, ExternalToolError, PermissionAccessError
from core.exceptions import InvalidMediaMetadataError
from models.schemas import CleanPlan, OptimizePlan, OptimizeOutcome, MediaFile, Track


logger = logging.getLogger(__name__)


class MediaRepository:
    """Acceso a archivos multimedia para analisis, remux y optimizacion."""

    def analyze_file(self, path: Path) -> MediaFile:
        """Analiza un archivo con mkvmerge y enriquece con ffprobe si existe."""

        try:
            result = subprocess.run(
                ["mkvmerge", "-J", str(path)],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
        except PermissionError as exc:
            logger.exception("Permiso denegado al analizar archivo: %s", path)
            raise PermissionAccessError(f"Permiso denegado al analizar: {path}") from exc
        except FileNotFoundError as exc:
            logger.exception("Binario mkvmerge no encontrado")
            raise BinaryMissingError("No se encontro 'mkvmerge'.") from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            logger.error("mkvmerge fallo para %s: %s", path, stderr)
            raise ExternalToolError(f"mkvmerge error para '{path.name}'. {stderr}") from exc
        except json.JSONDecodeError as exc:
            logger.exception("JSON invalido de mkvmerge para: %s", path)
            raise InvalidMediaMetadataError(f"JSON invalido de mkvmerge para '{path}'.") from exc

        tracks: List[Track] = []
        for raw_track in data.get("tracks", []):
            props = raw_track.get("properties", {})
            name = str(props.get("track_name", ""))
            title = str(props.get("title", ""))
            tracks.append(
                Track(
                    id=int(raw_track["id"]),
                    codec=str(raw_track.get("codec", "")),
                    language=str(props.get("language", "und")),
                    type=str(raw_track.get("type", "")),
                    name=name or title,
                    track_name=name,
                    title=title,
                    language_ietf=str(props.get("language_ietf", "")),
                    channels=props.get("audio_channels"),
                    bitrate=props.get("bitrate"),
                    default=bool(props.get("default_track", False)),
                    forced=bool(props.get("forced_track", False)),
                )
            )

        self._enrich_tracks_with_ffprobe(path, tracks)
        return MediaFile(
            path=path,
            container=str(data.get("container", {}).get("type", "unknown")),
            tracks=tracks,
        )

    def _run_ffprobe(self, path: Path) -> List[dict]:
        if shutil.which("ffprobe") is None:
            return []

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=index,codec_type,bit_rate:stream_tags=title,language",
                    "-of",
                    "json",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout or "{}")
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            logger.warning("No se pudo enriquecer metadata con ffprobe para '%s'.", path, exc_info=True)
            return []

        streams = data.get("streams", [])
        return streams if isinstance(streams, list) else []

    def _enrich_tracks_with_ffprobe(self, path: Path, tracks: List[Track]) -> None:
        streams = self._run_ffprobe(path)
        if not streams:
            return

        grouped_tracks: Dict[str, List[Track]] = {"video": [], "audio": [], "subtitles": []}
        for track in tracks:
            grouped_tracks.setdefault(track.type, []).append(track)

        grouped_streams: Dict[str, List[dict]] = {"video": [], "audio": [], "subtitles": []}
        for stream in streams:
            codec_type = str(stream.get("codec_type", ""))
            if codec_type == "subtitle":
                codec_type = "subtitles"
            grouped_streams.setdefault(codec_type, []).append(stream)

        for track_type, track_list in grouped_tracks.items():
            stream_list = grouped_streams.get(track_type, [])
            for track, stream in zip(track_list, stream_list):
                tags = stream.get("tags", {}) or {}
                if not track.title:
                    track.title = str(tags.get("title", ""))
                if not track.track_name:
                    track.track_name = track.title
                if not track.name:
                    track.name = track.track_name or track.title
                if not track.language_ietf:
                    track.language_ietf = str(tags.get("language", ""))
                if track.bitrate is None:
                    bit_rate = stream.get("bit_rate")
                    if bit_rate is not None:
                        try:
                            track.bitrate = int(bit_rate)
                        except (TypeError, ValueError):
                            pass

    def analyze_many(self, files: List[Path]) -> List[MediaFile]:
        return [self.analyze_file(f) for f in files]

    def _build_ffmpeg_command(self, plan: OptimizePlan, ffmpeg_args: List[str] | None = None) -> list[str]:
        args = ffmpeg_args or plan.profile.ffmpeg_args
        return [
            "ffmpeg",
            "-y",
            "-analyzeduration",
            "200M",
            "-probesize",
            "200M",
            "-i",
            str(plan.media_file.path),
            "-map",
            "0",
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            *args,
        ]

    def _replace_audio_args(self, ffmpeg_args: List[str], codec: str, bitrate: str) -> List[str]:
        replaced: List[str] = []
        index = 0
        while index < len(ffmpeg_args):
            current = ffmpeg_args[index]
            if current in {"-c:a", "-b:a"} and index + 1 < len(ffmpeg_args):
                index += 2
                continue
            replaced.append(current)
            index += 1

        replaced.extend(["-c:a", codec, "-b:a", bitrate])
        return replaced

    def _is_opus_layout_failure(self, stderr: str, plan: OptimizePlan) -> bool:
        if plan.profile.audio_codec != "libopus":
            return False
        lowered = stderr.lower()
        markers = (
            "invalid channel layout",
            "mapping family",
            "error while opening encoder",
        )
        return any(marker in lowered for marker in markers)

    def execute_remux(self, plan: CleanPlan) -> None:
        input_path = plan.media_file.path
        temp_path = input_path.with_name(f"{input_path.stem}_tmp{input_path.suffix}")

        kept_audios = [a.track.id for a in plan.tracks_to_keep if a.track.type == "audio"]
        kept_subs = [a.track.id for a in plan.tracks_to_keep if a.track.type == "subtitles"]

        cmd = ["mkvmerge", "-o", str(temp_path)]

        if kept_audios:
            cmd.extend(["--audio-tracks", ",".join(map(str, kept_audios))])
        else:
            cmd.append("--no-audio")

        if kept_subs:
            cmd.extend(["--subtitle-tracks", ",".join(map(str, kept_subs))])
        else:
            cmd.append("--no-subtitles")

        cmd.append(str(input_path))

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except FileNotFoundError as exc:
            raise BinaryMissingError("No se encontro 'mkvmerge'.") from exc
        except subprocess.CalledProcessError as exc:
            if temp_path.exists():
                temp_path.unlink()
            stderr = (exc.stderr or "").strip()
            raise ExternalToolError(f"Error al limpiar '{input_path.name}'. {stderr}") from exc

        try:
            input_path.unlink()
            temp_path.rename(input_path)
        except OSError as exc:
            if temp_path.exists():
                temp_path.unlink()
            raise PermissionAccessError(f"Fallo de permisos al sobreescribir '{input_path.name}'.") from exc

    def execute_optimization(self, plan: OptimizePlan) -> OptimizeOutcome:
        input_path = plan.media_file.path
        output_path = plan.output_path
        temp_output = output_path.with_name(f"{output_path.stem}.tmp{output_path.suffix}")

        cmd = self._build_ffmpeg_command(plan)
        cmd.append(str(temp_output))

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            if temp_output.exists():
                temp_output.unlink()

            if self._is_opus_layout_failure(stderr, plan):
                logger.warning(
                    "Fallo codificando audio con Opus para '%s'. Reintentando con AAC.",
                    input_path.name,
                )
                fallback_args = self._replace_audio_args(plan.profile.ffmpeg_args, "aac", "384k")
                fallback_cmd = self._build_ffmpeg_command(plan, fallback_args)
                fallback_cmd.append(str(temp_output))
                try:
                    subprocess.run(fallback_cmd, capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as retry_exc:
                    if temp_output.exists():
                        temp_output.unlink()
                    retry_stderr = (retry_exc.stderr or "").strip()
                    raise ExternalToolError(
                        f"Error al optimizar '{input_path.name}'. {retry_stderr}"
                    ) from retry_exc
                except FileNotFoundError as retry_exc:
                    raise BinaryMissingError("No se encontro 'ffmpeg'.") from retry_exc
            else:
                raise ExternalToolError(f"Error al optimizar '{input_path.name}'. {stderr}") from exc
        except FileNotFoundError as exc:
            raise BinaryMissingError("No se encontro 'ffmpeg'.") from exc

        try:
            if output_path.exists():
                output_path.unlink()
            temp_output.rename(output_path)
            optimized_size = output_path.stat().st_size
        except OSError as exc:
            if temp_output.exists():
                temp_output.unlink()
            raise PermissionAccessError(f"Fallo de permisos al guardar '{output_path.name}'.") from exc

        return OptimizeOutcome(
            input_path=input_path,
            output_path=output_path,
            original_size=plan.original_size,
            optimized_size=optimized_size,
            bytes_saved=plan.original_size - optimized_size,
        )

    def replace_original_with_output(self, output: OptimizeOutcome) -> None:
        backup_path = output.input_path.with_name(f"{output.input_path.stem}.backup{output.input_path.suffix}")

        try:
            if backup_path.exists():
                backup_path.unlink()
            output.input_path.rename(backup_path)
            output.output_path.rename(output.input_path)
            backup_path.unlink()
        except OSError as exc:
            if backup_path.exists() and not output.input_path.exists():
                backup_path.rename(output.input_path)
            raise PermissionAccessError(
                f"No se pudo reemplazar '{output.input_path.name}' por la copia optimizada."
            ) from exc
