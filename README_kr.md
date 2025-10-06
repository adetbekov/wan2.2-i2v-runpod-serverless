# Wan22 for RunPod Serverless
[English README](README.md)

이 프로젝트는 [Wan22](https://github.com/Comfy-Org/Wan_2.2_ComfyUI_Repackaged)를 RunPod Serverless 환경에서 쉽게 배포하고 사용할 수 있도록 설계된 템플릿입니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/generate_video)](https://console.runpod.io/hub/wlsdml1114/generate_video)

Wan22는 정적 이미지를 자연스러운 움직임과 사실적인 애니메이션을 가진 고품질 비디오로 생성하는 고급 AI 모델입니다.

## 🎨 Engui Studio 통합

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

이 InfiniteTalk 템플릿은 포괄적인 AI 모델 관리 플랫폼인 **Engui Studio**를 위해 주로 설계되었습니다. API를 통해 사용할 수 있지만, Engui Studio는 향상된 기능과 더 넓은 모델 지원을 제공합니다.

## ✨ 주요 기능

*   **이미지-투-비디오 생성**: 정적 이미지를 자연스러운 움직임을 가진 동적 비디오로 변환합니다.
*   **고품질 출력**: 사실적인 애니메이션을 가진 고해상도 비디오를 생성합니다.
*   **사용자 정의 가능한 매개변수**: 시드, 너비, 높이, 프롬프트 등 다양한 매개변수로 비디오 생성을 제어할 수 있습니다.
*   **ComfyUI 통합**: 유연한 워크플로우 관리를 위해 ComfyUI 위에 구축되었습니다.

## 🚀 RunPod Serverless 템플릿

이 템플릿은 Wan22를 RunPod Serverless Worker로 실행하는 데 필요한 모든 구성 요소를 포함합니다.

*   **Dockerfile**: 모델 실행에 필요한 환경을 구성하고 모든 의존성을 설치합니다.
*   **handler.py**: RunPod Serverless용 요청을 처리하는 핸들러 함수를 구현합니다.
*   **entrypoint.sh**: Worker가 시작될 때 초기화 작업을 수행합니다.
*   **wan22_nolora.json**: LoRA 없이 이미지-투-비디오 생성을 위한 워크플로우
*   **wan22_1lora.json**: 1개 LoRA 쌍으로 이미지-투-비디오 생성을 위한 워크플로우
*   **wan22_2lora.json**: 2개 LoRA 쌍으로 이미지-투-비디오 생성을 위한 워크플로우
*   **wan22_3lora.json**: 3개 LoRA 쌍으로 이미지-투-비디오 생성을 위한 워크플로우

### GPU 호환성

이 템플릿은 **NVIDIA A100 GPU**에 최적화되어 있으며 CUDA 호환성 문제에 대한 포괄적인 수정 사항이 포함되어 있습니다:

- **SageAttention 수정**: SageAttentionNode가 ComfyUI에 등록되는 것을 방지
  - Docker 빌드 중 NODE_CLASS_MAPPINGS에서 노드 제거
  - 노드가 완전히 로드되지 않도록 하는 깔끔한 아키텍처 솔루션
  - 런타임 패칭이나 함수 교체 불필요
  - 시스템이 기본 PyTorch attention 메커니즘 사용 (A100과 완전 호환)
- **환경 변수**: 커널 오류를 방지하기 위한 CUDA 호환성 플래그 설정:
  - `CUDA_LAUNCH_BLOCKING=1` - 더 나은 오류 보고를 위한 동기 CUDA 작업 활성화
  - `TORCH_COMPILE_DISABLE=1` - 문제를 일으킬 수 있는 PyTorch 컴파일 비활성화
  - `DISABLE_SAGE_ATTENTION=1` - SageAttention 명시적으로 비활성화
  - `COMFYUI_DISABLE_OPTIMIZATION=1` - 호환되지 않을 수 있는 공격적인 최적화 비활성화

### 입력

`input` 객체는 다음 필드를 포함해야 합니다.

#### 이미지 입력 (하나만 사용)
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | 아니오* | - | 입력 이미지 소스. 다음을 지원:<br>1. **HTTP/HTTPS URL**: 이미지가 다운로드됩니다 (예: `"https://example.com/image.jpg"`)<br>2. **로컬 파일 경로**: 네트워크 볼륨의 이미지 경로 (예: `"/my_volume/image.jpg"`) |
| `image_base64` | `string` | 아니오* | - | Base64로 인코딩된 이미지 문자열. 데이터 URI 접두사 있거나 없이 지원 (예: `"/9j/4AAQSkZJRg..."` 또는 `"data:image/jpeg;base64,/9j/4AAQSkZJRg..."`) |

**참고**: `image_path` 또는 `image_base64` 중 하나는 필수이지만, 둘 다 제공할 수 없습니다.

#### LoRA 설정
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `lora_pairs` | `array` | 아니오 | `[]` | LoRA 쌍의 배열. 각 쌍은 `high`, `low`, `high_weight`, `low_weight`를 포함 |

**중요**: LoRA 모델을 사용하려면 RunPod 네트워크 볼륨의 `/loras/` 폴더에 LoRA 파일들을 업로드해야 합니다. `lora_pairs`의 LoRA 모델 이름은 `/loras/` 폴더의 파일명과 일치해야 합니다.

#### LoRA 쌍 구조
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `high` | `string` | 예 | - | High LoRA 모델 이름 |
| `low` | `string` | 예 | - | Low LoRA 모델 이름 |
| `high_weight` | `float` | 아니오 | `1.0` | High LoRA 가중치 |
| `low_weight` | `float` | 아니오 | `1.0` | Low LoRA 가중치 |

#### 비디오 생성 매개변수
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | 예 | - | 생성할 비디오에 대한 설명 텍스트 |
| `seed` | `integer` | 예 | - | 비디오 생성을 위한 랜덤 시드 |
| `cfg` | `float` | 예 | - | 생성을 위한 CFG 스케일 |
| `width` | `integer` | 예 | - | 출력 비디오의 픽셀 단위 너비 |
| `height` | `integer` | 예 | - | 출력 비디오의 픽셀 단위 높이 |
| `length` | `integer` | 아니오 | `81` | 생성할 비디오의 길이 |
| `steps` | `integer` | 아니오 | `10` | 디노이징 스텝 수 |

**요청 예시:**

#### 1. 로컬 파일 경로 사용
```json
{
  "input": {
    "prompt": "사람이 자연스럽게 걷는 모습.",
    "image_path": "/my_volume/image.jpg",
    "seed": 12345,
    "cfg": 7.5,
    "width": 512,
    "height": 512,
    "length": 81,
    "steps": 10
  }
}
```

#### 2. HTTP URL 사용
```json
{
  "input": {
    "prompt": "사람이 자연스럽게 걷는 모습.",
    "image_path": "https://example.com/images/portrait.jpg",
    "seed": 12345,
    "cfg": 7.5,
    "width": 512,
    "height": 512
  }
}
```

#### 3. Base64 문자열 사용
```json
{
  "input": {
    "prompt": "사람이 자연스럽게 걷는 모습.",
    "image_path": "/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "seed": 12345,
    "cfg": 7.5,
    "width": 512,
    "height": 512,
    "lora_pairs": [
      {
        "high": "lora_high_model.safetensors",
        "low": "lora_low_model.safetensors",
        "high_weight": 1.0,
        "low_weight": 0.8
      }
    ]
  }
}
```

#### 4. 여러 LoRA 쌍 (최대 3개)
```json
{
  "input": {
    "prompt": "사람이 자연스럽게 걷는 모습.",
    "image_path": "/my_volume/image.jpg",
    "seed": 12345,
    "cfg": 7.5,
    "width": 512,
    "height": 512,
    "lora_pairs": [
      {
        "high": "lora1_high.safetensors",
        "low": "lora1_low.safetensors",
        "high_weight": 1.0,
        "low_weight": 0.8
      },
      {
        "high": "lora2_high.safetensors",
        "low": "lora2_low.safetensors",
        "high_weight": 0.9,
        "low_weight": 0.7
      }
    ]
  }
}
```

### 출력

#### 성공

작업이 성공하면 생성된 비디오가 Base64로 인코딩된 JSON 객체를 반환합니다.

| 매개변수 | 타입 | 설명 |
| --- | --- | --- |
| `video` | `string` | Base64로 인코딩된 비디오 파일 데이터입니다. |

**성공 응답 예시:**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### 오류

작업이 실패하면 오류 메시지를 포함한 JSON 객체를 반환합니다.

| 매개변수 | 타입 | 설명 |
| --- | --- | --- |
| `error` | `string` | 발생한 오류에 대한 설명입니다. |

**오류 응답 예시:**

```json
{
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🛠️ 사용법 및 API 참조

1.  이 저장소를 기반으로 RunPod에서 Serverless Endpoint를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면 아래 API 참조에 따라 HTTP POST 요청을 통해 작업을 제출합니다.

### 📁 네트워크 볼륨 사용

Base64로 인코딩된 파일을 직접 전송하는 대신 RunPod의 Network Volumes를 사용하여 대용량 파일을 처리할 수 있습니다. 이는 특히 대용량 이미지 파일과 LoRA 모델을 다룰 때 유용합니다.

1.  **네트워크 볼륨 생성 및 연결**: RunPod 대시보드에서 Network Volume(예: S3 기반 볼륨)을 생성하고 Serverless Endpoint 설정에 연결합니다.
2.  **파일 업로드**: 사용하려는 이미지 파일과 LoRA 모델을 생성된 Network Volume에 업로드합니다.
3.  **파일 구성**: 
    - 입력 이미지는 Network Volume 내 어디든 배치할 수 있습니다
    - LoRA 모델 파일은 Network Volume 내의 `/loras/` 폴더에 배치해야 합니다
4.  **경로 지정**: API 요청 시 Network Volume 내의 파일 경로를 지정합니다:
    - `image_path`의 경우: 이미지 파일의 전체 경로 사용 (예: `"/my_volume/images/portrait.jpg"`)
    - LoRA 모델의 경우: 파일명만 사용 (예: `"my_lora_model.safetensors"`) - 시스템이 자동으로 `/loras/` 폴더에서 찾습니다

## 🔧 워크플로우 구성

이 템플릿은 다음 워크플로우 구성을 포함합니다:

*   **wan22.json**: 이미지-투-비디오 생성 워크플로우

워크플로우는 ComfyUI를 기반으로 하며 Wan22 처리를 위한 모든 필요한 노드를 포함합니다:
- 프롬프트를 위한 CLIP 텍스트 인코딩
- VAE 로딩 및 처리
- 비디오 생성을 위한 WanImageToVideo 노드
- 이미지 연결 및 처리 노드

## 🙏 원본 프로젝트

이 프로젝트는 다음 원본 저장소를 기반으로 합니다. 모델과 핵심 로직에 대한 모든 권리는 원본 작성자에게 있습니다.

*   **Wan22:** [https://github.com/Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 라이선스

원본 Wan22 프로젝트는 해당 라이선스를 따릅니다. 이 템플릿도 해당 라이선스를 준수합니다.
