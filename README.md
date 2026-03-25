# Nano Banana MCP

Google Gemini API의 Nano Banana 이미지 생성 기능을 MCP 서버로 감싼 Python 패키지입니다. Claude Code 같은 MCP 클라이언트에서 바로 연결해 텍스트-투-이미지, 이미지 편집, 검색 그라운딩 워크플로를 사용할 수 있습니다.

- PyPI: `parkjack-nanobanana-mcp`
- GitHub: `jiwon86/parkjack-nanobanana-mcp`
- 기본 모델: `gemini-3.1-flash-image-preview`
- 추천 실행 방식: `uvx`

## Highlights

- Claude Code에서 `uvx` 한 줄로 바로 연결 가능
- 텍스트 생성과 이미지 편집을 하나의 MCP 툴로 처리
- `gemini-3.1-flash-image-preview`, `gemini-3-pro-image-preview`, `gemini-2.5-flash-image` 지원
- 생성 이미지를 로컬 파일로 저장하고 경로, 해시, 메타데이터 반환
- 웹/이미지 검색 그라운딩 옵션 지원

## Quickstart

Claude Code에서 가장 간단하게 붙이는 방법입니다.

```json
{
  "mcpServers": {
    "nano-banana": {
      "command": "uvx",
      "args": ["parkjack-nanobanana-mcp"],
      "env": {
        "GEMINI_API_KEY": "YOUR_API_KEY",
        "NANOBANANA_DEFAULT_MODEL": "gemini-3.1-flash-image-preview"
      }
    }
  }
}
```

추가 후 Claude Code 안에서 `/mcp`로 연결 상태를 확인하면 됩니다.

## Installation Options

### 1. Zero-install with `uvx` (Recommended)

Python CLI를 설치 없이 실행하고 싶다면 `uvx`가 가장 깔끔합니다.

```json
{
  "mcpServers": {
    "nano-banana": {
      "command": "uvx",
      "args": ["parkjack-nanobanana-mcp"],
      "env": {
        "GEMINI_API_KEY": "YOUR_API_KEY",
        "NANOBANANA_DEFAULT_MODEL": "gemini-3.1-flash-image-preview"
      }
    }
  }
}
```

### 2. Installed CLI

직접 설치한 실행 파일을 쓰고 싶다면:

```bash
pip install parkjack-nanobanana-mcp
```

```json
{
  "mcpServers": {
    "nano-banana": {
      "command": "parkjack-nanobanana-mcp",
      "env": {
        "GEMINI_API_KEY": "YOUR_API_KEY",
        "NANOBANANA_DEFAULT_MODEL": "gemini-3.1-flash-image-preview"
      }
    }
  }
}
```

### 3. Local Development

저장소에서 직접 작업하거나 수정하면서 실행하려면:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

직접 실행:

```bash
. .venv/bin/activate
parkjack-nanobanana-mcp
```

또는:

```bash
. .venv/bin/activate
python -m nanobanana_mcp
```

## Configuration

지원 환경 변수:

- `GEMINI_API_KEY`: Gemini API 키
- `GOOGLE_API_KEY`: `GEMINI_API_KEY` 대체 키
- `NANOBANANA_DEFAULT_MODEL`: 기본 모델 지정
- `NANOBANANA_OUTPUT_DIR`: 생성 이미지 저장 디렉터리
- `NANOBANANA_MCP_TRANSPORT`: 기본값 `stdio`, 필요 시 `streamable-http`

예시:

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
export NANOBANANA_DEFAULT_MODEL="gemini-3.1-flash-image-preview"
```

`.env.example`도 같이 제공됩니다.

## Tooling

### `nano_banana_generate_image`

텍스트 생성과 이미지 편집을 모두 처리하는 메인 툴입니다.

주요 인자:

- `prompt`: 생성 또는 편집 지시문
- `image_paths`: 입력 이미지 경로 목록. 비우면 text-to-image, 넣으면 image edit
- `model`: 사용할 모델. 생략하면 서버 기본값 사용
- `aspect_ratio`: 예시 `1:1`, `16:9`, `9:16`
- `image_size`: `512`, `1K`, `2K`, `4K`
- `include_text`: 이미지와 함께 텍스트 설명도 받고 싶을 때 사용
- `enable_web_search`: 웹 검색 그라운딩
- `enable_image_search`: 이미지 검색 그라운딩
- `output_dir`: 결과 파일 저장 경로

반환값:

- 저장된 이미지 절대 경로
- MIME 타입, 파일 크기, sha256
- 모델이 함께 반환한 텍스트
- 사용량 메타데이터
- 검색 그라운딩 메타데이터

### `nano_banana_models`

지원 모델, 기본 모델, 모델별 제약사항을 반환합니다.

## Supported Models

| Model | Notes |
| --- | --- |
| `gemini-3.1-flash-image-preview` | 기본값. 빠른 이미지 생성과 검색 그라운딩에 적합 |
| `gemini-3-pro-image-preview` | 더 높은 품질과 프롬프트 충실도가 필요할 때 적합 |
| `gemini-2.5-flash-image` | 지원됨. 다만 `image_size`는 자동 무시 |

모델 변경 방식:

1. MCP 툴 호출 시 `model` 파라미터 직접 지정
2. 서버 시작 전 `NANOBANANA_DEFAULT_MODEL` 환경 변수로 기본값 지정

예시:

```json
{
  "prompt": "Create a premium skincare product shot with elegant typography",
  "model": "gemini-3-pro-image-preview",
  "image_size": "2K",
  "include_text": true
}
```

`gemini-2.5-flash-image` 예시:

```json
{
  "prompt": "Create a clean app icon of a banana robot on a white background",
  "model": "gemini-2.5-flash-image",
  "aspect_ratio": "1:1",
  "include_text": true
}
```

## Example Prompts

### Text-to-image

```json
{
  "prompt": "A premium banana perfume product photo, dramatic studio lighting, elegant glass bottle, white background",
  "aspect_ratio": "1:1",
  "image_size": "2K",
  "include_text": true
}
```

### Image edit

```json
{
  "prompt": "Keep the face unchanged. Turn this into a cinematic profile portrait against a white seamless studio background.",
  "image_paths": ["/absolute/path/to/photo.jpg"],
  "include_text": true
}
```

### Grounded infographic

```json
{
  "prompt": "Visualize today's weather forecast for Seoul as a clean infographic",
  "enable_web_search": true,
  "include_text": true
}
```

## Output

기본적으로 생성 결과는 `generated_images/<timestamp>/` 아래에 저장됩니다.

```text
generated_images/
  20260325_130000_123456/
    candidate_00_part_00.png
```

## Operational Notes

- Google 문서상 생성된 모든 이미지에는 SynthID 워터마크가 포함됩니다.
- `gemini-2.5-flash-image`는 지원되지만 `image_size`는 문서상 미지원이라 자동 무시됩니다.
- 이미지 검색 그라운딩을 켜면 소스 저작자 표시 요구사항을 지켜야 합니다.
- 실제 비밀값은 README 예시 그대로 커밋하지 말고, 로컬 설정 또는 비밀 관리 방식으로 넣는 것을 권장합니다.

## Verification

실제 API 키 없이 로컬 파이프라인만 확인하려면:

```bash
. .venv/bin/activate
python scripts/smoke_mock.py
```

## Publishing

배포 파일 생성:

```bash
. .venv/bin/activate
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

PyPI 업로드:

```bash
python -m twine upload dist/*
```

업로드 전 체크:

- PyPI 프로젝트 이름이 비어 있는지 다시 확인
- 실제 비밀값이 파일에 포함되지 않았는지 확인
- 새 릴리스를 올릴 때는 [pyproject.toml](/mnt/c/MY/MCP/nanoBanana/pyproject.toml#L7)의 `version`을 먼저 증가
