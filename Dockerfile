# syntax = docker/dockerfile:1.0-experimental
FROM alpine:3 AS venv-create
RUN apk add --no-cache build-base python3 python3-dev py3-pip zlib-dev libwebp-dev jpeg-dev git musl-dev curl libffi-dev re2-dev
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN python3 -m venv /venv
COPY pyproject.toml poetry.lock ./
RUN --mount=type=cache,id=custom-pip,target=/root/.cache/pip \
    /root/.local/bin/poetry export -f requirements.txt --without-hashes | /venv/bin/pip install -r /dev/stdin
ENV PYTHONPATH=/packages
WORKDIR /workdir
COPY locales locales
RUN /venv/bin/pybabel compile -d locales

FROM alpine:3 AS release
RUN apk add --no-cache python3 libwebp jpeg re2
COPY --from=venv-create /venv /venv
COPY --from=venv-create /workdir/locales /app/locales
WORKDIR /app
COPY . .
ARG CI
ARG DESCRIBE
RUN if [ $CI = "true" ]; then \
  echo $DESCRIBE > .git-version; \
 else \
  echo "Built outside CI, unknown ver" >  .git-version; \
 fi
ENV SENTRY_RELEASE=$GITHUB_SHA
CMD /venv/bin/python3 /app/main.py
LABEL org.opencontainers.image.source https://github.com/octo-tg-bot/octobotv4
