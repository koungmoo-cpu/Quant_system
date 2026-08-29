FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (필요한 경우)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 한글 인코딩 에러 방지
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

# 포트 개방 (Google Cloud Run은 기본적으로 8080 포트를 사용합니다)
EXPOSE 8080

# uvicorn 서버 실행 (운영 환경이므로 --reload 옵션 제거)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
