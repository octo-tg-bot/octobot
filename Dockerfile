FROM alpine:3.12.1
RUN apk add --no-cache python3~=3.8 py3-cryptography py3-pillow~=7.1.2-r0 py3-pip
WORKDIR /app
COPY requirements-alpine.txt .
RUN pip install --no-cache-dir -r requirements-alpine.txt
COPY locales locales
RUN pybabel compile -d locales
COPY . .
CMD python3 /app/main.py
LABEL org.opencontainers.image.source https://github.com/octo-tg-bot/octobotv4
