#!/bin/bash

# ==============================================================================
# Google Cloud Run 배포 스크립트 (Backend)
# ==============================================================================

# 프로젝트 설정 변수 (본인의 환경에 맞게 수정하세요)
PROJECT_ID=ai-stock-506110		  # 예: my-ai-quant-123
REGION="asia-northeast3"                  # 서울 리전
SERVICE_NAME="ai-stock-backend"           # Cloud Run 서비스 이름

echo "🚀 배포를 시작합니다: $SERVICE_NAME (Region: $REGION)"

# 1. gcloud 명령어가 사용 가능한지 확인
if ! command -v gcloud &> /dev/null
then
    echo "❌ Error: gcloud CLI가 설치되어 있지 않습니다."
    echo "설치 가이드: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 2. (선택) 현재 프로젝트 ID 명시적 설정
# gcloud config set project ai-stock-506110

# 3. .env 파일에서 GOOGLE_GENAI_API_KEY 읽어오기
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -z "$GOOGLE_GENAI_API_KEY" ]; then
    echo "❌ Error: .env 파일에 GOOGLE_GENAI_API_KEY가 설정되어 있지 않습니다."
    exit 1
fi

# 4. Google Cloud Run 배포 실행
# 소스 코드에서 빌드와 배포를 동시에 수행 (Cloud Build 자동 사용)
gcloud run deploy $SERVICE_NAME \
  --quiet \
  --project $PROJECT_ID \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars GOOGLE_GENAI_API_KEY="$GOOGLE_GENAI_API_KEY"
  
# (참고) 환경변수가 많거나 보안이 중요한 경우 --set-secrets 를 통해 Secret Manager와 연동하는 것을 권장합니다.

echo "✅ 배포 명령이 실행되었습니다!"
