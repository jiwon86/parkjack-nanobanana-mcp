# Nano Banana MCP

Google Gemini API의 Nano Banana 이미지 생성 기능을 MCP 서버로 감싼 예제입니다.

PyPI 배포용 패키지 이름: `parkjack-nanobanana-mcp`

- 기본 모델: `gemini-3.1-flash-image-preview`
- 지원 기능: 텍스트-투-이미지, 이미지 편집, 검색 그라운딩, 결과 이미지 파일 저장
- 전송 방식: 기본 `stdio` (`FastMCP`)
- 모델 선택: 툴 호출마다 변경 가능, 또는 환경 변수로 기본값 지정 가능

## 왜 이렇게 만들었나

Google 문서 기준으로 Nano Banana 이미지는 `models.generateContent` REST 엔드포인트로 호출할 수 있습니다. 텍스트만 보내면 생성, 이미지와 텍스트를 같이 보내면 편집 흐름으로 사용할 수 있어서 MCP 툴 하나로 대부분의 워크플로를 감쌀 수 있습니다.

## 설치

PyPI에 배포한 뒤에는:

```bash
pip install parkjack-nanobanana-mcp
```

저장소에서 직접 설치하려면:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

환경 변수:

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
export NANOBANANA_DEFAULT_MODEL="gemini-3.1-flash-image-preview"
```

`.env.example`도 같이 제공됩니다.

- `GEMINI_API_KEY`가 없으면 `GOOGLE_API_KEY`도 자동으로 확인합니다.
- `NANOBANANA_DEFAULT_MODEL`으로 서버 기본 모델을 바꿀 수 있습니다.

## 실행

```bash
. .venv/bin/activate
parkjack-nanobanana-mcp
```

또는:

```bash
. .venv/bin/activate
python -m nanobanana_mcp
```

기본 transport는 `stdio`입니다. `NANOBANANA_MCP_TRANSPORT=streamable-http`로 바꾸면 FastMCP의 HTTP transport로 실행할 수 있습니다.

## MCP 등록 예시

예를 들어 `mcp.json`이나 클라이언트 설정에 아래처럼 등록할 수 있습니다.

Linux / macOS / WSL:

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

Windows:

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

저장소를 직접 clone해서 쓰는 경우에는 기존처럼 Python 경로 + `-m nanobanana_mcp` 방식으로 등록해도 됩니다.

## 제공 툴

### `nano_banana_models`

지원 모델과 문서상 특징을 반환합니다.

### `nano_banana_generate_image`

텍스트 생성과 이미지 편집을 모두 처리합니다.

주요 인자:

- `prompt`: 생성 또는 편집 지시문
- `image_paths`: 입력 이미지 경로 목록. 비우면 text-to-image, 넣으면 image-to-image/edit
- `model`: 호출마다 모델 선택 가능. 생략하면 서버 기본값 사용
- `aspect_ratio`: 예시 `1:1`, `16:9`, `9:16`
- `image_size`: `512`, `1K`, `2K`, `4K`
  `gemini-2.5-flash-image`에서는 자동 무시됨
- `include_text`: 텍스트 설명도 함께 받고 싶을 때 `true`
- `enable_web_search`: 웹 검색 그라운딩 사용
- `enable_image_search`: 이미지 검색 그라운딩 사용
- `output_dir`: 결과 파일을 저장할 디렉터리

반환값:

- 저장된 이미지 절대 경로
- MIME 타입, 파일 크기, sha256
- 모델이 함께 반환한 텍스트
- 사용량 메타데이터
- 검색 그라운딩 메타데이터

## 모델 변경 방식

사용자는 두 가지 방식으로 모델을 바꿀 수 있습니다.

1. MCP 툴 호출 시 `model` 파라미터를 직접 지정
2. 서버 시작 전 `NANOBANANA_DEFAULT_MODEL` 환경 변수로 기본값 변경

지원 모델:

- `gemini-3.1-flash-image-preview`
- `gemini-3-pro-image-preview`
- `gemini-2.5-flash-image`

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

## 사용 예시

### 1. 텍스트로 이미지 생성

```json
{
  "prompt": "A premium banana perfume product photo, dramatic studio lighting, elegant glass bottle, white background",
  "aspect_ratio": "1:1",
  "image_size": "2K",
  "include_text": true
}
```

### 2. 로컬 이미지를 기반으로 편집

```json
{
  "prompt": "Keep the face unchanged. Turn this into a cinematic profile portrait against a white seamless studio background.",
  "image_paths": ["/absolute/path/to/photo.jpg"],
  "include_text": true
}
```

### 3. 검색 그라운딩으로 인포그래픽 생성

```json
{
  "prompt": "Visualize today's weather forecast for Seoul as a clean infographic",
  "enable_web_search": true,
  "include_text": true
}
```

## 출력 파일 위치

기본적으로 결과는 `generated_images/<timestamp>/` 아래에 저장됩니다.

```text
generated_images/
  20260325_130000_123456/
    candidate_00_part_00.png
```

## 주의사항

- Google 문서상 생성된 모든 이미지에는 SynthID 워터마크가 포함됩니다.
- `gemini-2.5-flash-image`는 이 MCP 서버에서 정식 지원합니다.
- 다만 `gemini-2.5-flash-image`는 문서상 `imageSize`를 지원하지 않아서, 이 서버에서는 `image_size`가 들어와도 에러를 내지 않고 자동 무시합니다.
- 따라서 README의 다른 예시에서 `image_size`를 보고 그대로 복사하더라도, 모델을 `gemini-2.5-flash-image`로 바꿨다면 해당 값은 적용되지 않습니다.
- 이미지 검색 그라운딩을 켜면 소스 저작자 표시 요구사항을 지켜야 합니다. 응답에 `grounding_metadata`를 그대로 포함해 두었습니다.

## 간단 검증

실제 API 키 없이 로컬 파이프라인만 빠르게 확인하려면:

```bash
. .venv/bin/activate
python scripts/smoke_mock.py
```

## PyPI 배포

배포 파일 생성:

```bash
. .venv/bin/activate
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

TestPyPI 업로드:

```bash
python -m twine upload --repository testpypi dist/*
```

PyPI 업로드:

```bash
python -m twine upload dist/*
```

업로드 전 체크:

- PyPI 프로젝트 이름이 비어 있는지 다시 확인
- `GEMINI_API_KEY` 같은 실제 비밀값이 파일에 포함되지 않았는지 확인
- 버전을 다시 올릴 때는 [pyproject.toml](/mnt/c/MY/MCP/nanoBanana/pyproject.toml#L7)의 `version`을 먼저 증가
