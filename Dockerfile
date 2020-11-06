FROM python:3.8-alpine
RUN apk add --no-cache gcc jpeg-dev zlib-dev libffi-dev musl-dev openssl-dev libwebp-dev
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD python /app/main.py
