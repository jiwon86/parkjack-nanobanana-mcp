from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import nanobanana_mcp.server as server

PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aK9cAAAAASUVORK5CYII="
)


class DummyContext:
    async def info(self, message: str) -> None:
        print(message)

    async def warning(self, message: str) -> None:
        print(f"WARNING: {message}")


async def fake_generate_content(**_: object) -> dict[str, object]:
    return {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {"text": "mock response"},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": PNG_B64,
                            }
                        },
                    ]
                },
            }
        ],
        "usageMetadata": {"promptTokenCount": 12},
    }


async def main() -> None:
    original_generate_content = server._generate_content
    server._generate_content = fake_generate_content
    try:
        with TemporaryDirectory() as tmpdir:
            result = await server.nano_banana_generate_image(
                prompt="smoke test prompt",
                ctx=DummyContext(),
                output_dir=tmpdir,
                include_text=True,
            )

            image_path = Path(result["images"][0]["path"])
            assert result["ok"] is True
            assert image_path.exists()
            assert result["texts"] == ["mock response"]
            print(f"Smoke test passed: {image_path}")

            result_25 = await server.nano_banana_generate_image(
                prompt="smoke test prompt 2.5",
                ctx=DummyContext(),
                output_dir=tmpdir,
                model="gemini-2.5-flash-image",
                image_size="2K",
                include_text=True,
            )
            assert result_25["model"] == "gemini-2.5-flash-image"
            print("Smoke test passed for gemini-2.5-flash-image")
    finally:
        server._generate_content = original_generate_content


if __name__ == "__main__":
    asyncio.run(main())
