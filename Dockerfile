FROM python:3.9.19-slim

WORKDIR /app

# 타임존 설정
ENV TZ=Asia/Seoul

# 타임존 데이터 설치 및 설정
RUN apt-get update && apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# requirements.txt 파일을 컨테이너의 /app 디렉토리로 복사
COPY requirements.txt /app

# requirements.txt에 명시된 필요한 패키지를 설치
RUN pip install --no-cache-dir -r requirements.txt

# 현재 디렉토리의 나머지 파일들을 컨테이너의 /app 디렉토리로 복사
COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]