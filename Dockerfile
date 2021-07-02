# syntax = docker/dockerfile:1.0-experimental
FROM alpine:3.12.1 AS pip-install-env
RUN apk add --no-cache python3~=3.8 py3-pip gcc python3-dev~=3.8 zlib-dev libwebp-dev jpeg-dev git musl-dev
COPY requirements.txt .
RUN --mount=type=cache,id=custom-pip,target=/root/.cache/pip pip install wheel && pip install -r requirements.txt -t /packages
ENV PYTHONPATH=/packages
WORKDIR /workdir
COPY locales locales
RUN /packages/bin/pybabel compile -d locales

FROM alpine:3.12.1 AS release
RUN apk add --no-cache python3~=3.8 libwebp jpeg
COPY --from=pip-install-env /packages /packages
COPY --from=pip-install-env /workdir/locales /app/locales
ENV PYTHONPATH=/packages
WORKDIR /app
COPY . .
RUN git describe --dirty > .git-version
ENV SENTRY_RELEASE=$GITHUB_SHA
CMD python3 /app/main.py
LABEL org.opencontainers.image.source https://github.com/octo-tg-bot/octobotv4
