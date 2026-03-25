from __future__ import annotations

import base64
import hashlib
import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import httpx
from mcp.server.fastmcp import Context, FastMCP

API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
SUPPORTED_MODELS: tuple[str, ...] = (
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
)
MODEL_CAPABILITIES: dict[str, dict[str, Any]] = {
    "gemini-3.1-flash-image-preview": {
        "label": "Nano Banana 2",
        "supports_image_size": True,
        "notes": [
            "Fast image model for high-volume workflows",
            "Supports aspectRatio and imageSize",
            "Supports grounded generation with Google Search",
        ],
    },
    "gemini-3-pro-image-preview": {
        "label": "Nano Banana Pro",
        "supports_image_size": True,
        "notes": [
            "Higher-fidelity professional asset generation",
            "Supports aspectRatio and imageSize",
            "Best when prompt following and text rendering quality matter",
        ],
    },
    "gemini-2.5-flash-image": {
        "label": "Nano Banana",
        "supports_image_size": False,
        "notes": [
            "Fast and efficient image generation",
            "Supports aspectRatio",
            "imageSize is ignored for this model",
        ],
    },
}
DEFAULT_MODEL = os.environ.get("NANOBANANA_DEFAULT_MODEL") or SUPPORTED_MODELS[0]
DEFAULT_OUTPUT_ROOT = Path(
    os.environ.get("NANOBANANA_OUTPUT_DIR", "generated_images")
).expanduser()

ModelName = Literal[
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
]


@dataclass(slots=True)
class SavedImage:
    path: Path
    mime_type: str
    byte_length: int
    sha256: str
    candidate_index: int
    part_index: int


mcp = FastMCP("Nano Banana MCP", json_response=True)


def _api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GEMINI_API_KEY or GOOGLE_API_KEY before starting the MCP server."
        )
    return api_key


def _validate_model_name(model: str) -> None:
    if model not in SUPPORTED_MODELS:
        supported = ", ".join(SUPPORTED_MODELS)
        raise ValueError(f"Unsupported model '{model}'. Supported models: {supported}")


def _coerce_output_dir(output_dir: str | None) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return DEFAULT_OUTPUT_ROOT.joinpath(timestamp).resolve()


def _guess_mime_type(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError(
            f"Could not infer an image MIME type from '{image_path}'. "
            "Use a standard image extension like .png, .jpg, or .webp."
        )
    return mime_type


def _file_part(image_path: Path) -> dict[str, Any]:
    payload = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return {
        "inline_data": {
            "mime_type": _guess_mime_type(image_path),
            "data": payload,
        }
    }


def _build_generation_config(
    *,
    include_text: bool,
    aspect_ratio: str | None,
    image_size: str | None,
) -> dict[str, Any]:
    generation_config: dict[str, Any] = {
        "responseModalities": ["TEXT", "IMAGE"] if include_text else ["IMAGE"]
    }

    image_config: dict[str, Any] = {}
    if aspect_ratio:
        image_config["aspectRatio"] = aspect_ratio
    if image_size:
        image_config["imageSize"] = image_size
    if image_config:
        generation_config["imageConfig"] = image_config

    return generation_config


def _build_search_tools(
    *, enable_web_search: bool, enable_image_search: bool
) -> list[dict[str, Any]]:
    if not enable_web_search and not enable_image_search:
        return []

    search_types: dict[str, Any] = {}
    if enable_web_search:
        search_types["webSearch"] = {}
    if enable_image_search:
        search_types["imageSearch"] = {}

    google_search: dict[str, Any] = {}
    if search_types:
        google_search["searchTypes"] = search_types

    return [{"google_search": google_search}]


def _extract_inline_data(part: dict[str, Any]) -> dict[str, Any] | None:
    return part.get("inlineData") or part.get("inline_data")


def _mime_extension(mime_type: str) -> str:
    extension = mimetypes.guess_extension(mime_type) or ".bin"
    if extension == ".jpe":
        return ".jpg"
    return extension


def _save_images(response_json: dict[str, Any], output_dir: Path) -> list[SavedImage]:
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_images: list[SavedImage] = []
    for candidate_index, candidate in enumerate(response_json.get("candidates", [])):
        parts = ((candidate.get("content") or {}).get("parts")) or []
        for part_index, part in enumerate(parts):
            inline_data = _extract_inline_data(part)
            if not inline_data:
                continue

            mime_type = (
                inline_data.get("mimeType")
                or inline_data.get("mime_type")
                or "application/octet-stream"
            )
            payload = inline_data.get("data")
            if not payload:
                continue

            raw_bytes = base64.b64decode(payload)
            extension = _mime_extension(mime_type)
            file_path = output_dir / (
                f"candidate_{candidate_index:02d}_part_{part_index:02d}{extension}"
            )
            file_path.write_bytes(raw_bytes)

            saved_images.append(
                SavedImage(
                    path=file_path.resolve(),
                    mime_type=mime_type,
                    byte_length=len(raw_bytes),
                    sha256=hashlib.sha256(raw_bytes).hexdigest(),
                    candidate_index=candidate_index,
                    part_index=part_index,
                )
            )

    return saved_images


def _extract_texts(response_json: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for candidate in response_json.get("candidates", []):
        parts = ((candidate.get("content") or {}).get("parts")) or []
        for part in parts:
            text = part.get("text")
            if text:
                texts.append(text)
    return texts


def _extract_grounding_metadata(response_json: dict[str, Any]) -> list[dict[str, Any]]:
    metadata_items: list[dict[str, Any]] = []
    for candidate in response_json.get("candidates", []):
        grounding = candidate.get("groundingMetadata") or candidate.get(
            "grounding_metadata"
        )
        if grounding:
            metadata_items.append(grounding)
    return metadata_items


def _validate_request(
    *,
    model: ModelName,
    image_paths: list[str] | None,
) -> None:
    _validate_model_name(model)

    if image_paths:
        for image_path in image_paths:
            path = Path(image_path).expanduser()
            if not path.exists():
                raise FileNotFoundError(f"Input image not found: {path}")
            if not path.is_file():
                raise ValueError(f"Input image must be a file: {path}")


async def _warn(ctx: Context, message: str) -> None:
    warning = getattr(ctx, "warning", None)
    if callable(warning):
        await warning(message)
        return

    info = getattr(ctx, "info", None)
    if callable(info):
        await info(f"[warning] {message}")


async def _normalize_image_size(
    *,
    model: ModelName,
    image_size: str | None,
    ctx: Context,
) -> str | None:
    if not image_size:
        return None

    if MODEL_CAPABILITIES[model]["supports_image_size"]:
        return image_size

    await _warn(
        ctx,
        f"Ignoring image_size for '{model}' because this model does not support it."
    )
    return None


async def _generate_content(
    *,
    model: ModelName,
    parts: list[dict[str, Any]],
    include_text: bool,
    aspect_ratio: str | None,
    image_size: str | None,
    enable_web_search: bool,
    enable_image_search: bool,
    request_timeout_s: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": _build_generation_config(
            include_text=include_text,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    }

    tools = _build_search_tools(
        enable_web_search=enable_web_search,
        enable_image_search=enable_image_search,
    )
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=request_timeout_s) as client:
        response = await client.post(
            f"{API_BASE_URL}/{model}:generateContent",
            headers={
                "x-goog-api-key": _api_key(),
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if response.is_error:
        try:
            error_json = response.json()
        except ValueError:
            error_json = {"raw": response.text}
        raise RuntimeError(
            f"Gemini API request failed with status {response.status_code}: {error_json}"
        )

    return response.json()


@mcp.tool()
def nano_banana_models() -> dict[str, Any]:
    """Return the supported Nano Banana model ids and usage notes."""
    _validate_model_name(DEFAULT_MODEL)

    return {
        "default_model": DEFAULT_MODEL,
        "models": [
            {
                "id": model_id,
                "label": MODEL_CAPABILITIES[model_id]["label"],
                "supports_image_size": MODEL_CAPABILITIES[model_id][
                    "supports_image_size"
                ],
                "notes": MODEL_CAPABILITIES[model_id]["notes"],
            }
            for model_id in SUPPORTED_MODELS
        ],
    }


@mcp.tool()
async def nano_banana_generate_image(
    prompt: str,
    ctx: Context,
    image_paths: list[str] | None = None,
    model: ModelName = DEFAULT_MODEL,
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    include_text: bool = False,
    enable_web_search: bool = False,
    enable_image_search: bool = False,
    output_dir: str | None = None,
    request_timeout_s: float = 180.0,
) -> dict[str, Any]:
    """
    Generate or edit images with Nano Banana.

    Pass only `prompt` for text-to-image generation.
    Pass `image_paths` plus `prompt` for image editing / image-to-image.
    """
    _validate_request(model=model, image_paths=image_paths)
    image_size = await _normalize_image_size(
        model=model,
        image_size=image_size,
        ctx=ctx,
    )

    await ctx.info(f"Calling Nano Banana model '{model}'")

    parts: list[dict[str, Any]] = [{"text": prompt}]
    resolved_inputs: list[str] = []

    for image_path in image_paths or []:
        path = Path(image_path).expanduser().resolve()
        parts.append(_file_part(path))
        resolved_inputs.append(str(path))

    response_json = await _generate_content(
        model=model,
        parts=parts,
        include_text=include_text,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        enable_web_search=enable_web_search,
        enable_image_search=enable_image_search,
        request_timeout_s=request_timeout_s,
    )

    resolved_output_dir = _coerce_output_dir(output_dir)
    saved_images = _save_images(response_json, resolved_output_dir)
    texts = _extract_texts(response_json)
    grounding_metadata = _extract_grounding_metadata(response_json)

    await ctx.info(
        f"Nano Banana finished with {len(saved_images)} image(s) and {len(texts)} text part(s)."
    )

    return {
        "ok": True,
        "model": model,
        "mode": "edit" if resolved_inputs else "generate",
        "prompt": prompt,
        "input_images": resolved_inputs,
        "output_dir": str(resolved_output_dir),
        "images": [
            {
                "path": str(image.path),
                "mime_type": image.mime_type,
                "bytes": image.byte_length,
                "sha256": image.sha256,
                "candidate_index": image.candidate_index,
                "part_index": image.part_index,
            }
            for image in saved_images
        ],
        "texts": texts,
        "grounding_metadata": grounding_metadata,
        "usage_metadata": response_json.get("usageMetadata")
        or response_json.get("usage_metadata"),
        "prompt_feedback": response_json.get("promptFeedback")
        or response_json.get("prompt_feedback"),
        "finish_reasons": [
            candidate.get("finishReason") or candidate.get("finish_reason")
            for candidate in response_json.get("candidates", [])
        ],
        "raw_candidate_count": len(response_json.get("candidates", [])),
    }


def main() -> None:
    transport = os.environ.get("NANOBANANA_MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
