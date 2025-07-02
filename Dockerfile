FROM python:3.10-slim

LABEL vendor=neon.ai \
    ai.neon.name="neon-users-service"

ENV OVOS_CONFIG_BASE_FOLDER=neon
ENV OVOS_CONFIG_FILENAME=diana.yaml
ENV OVOS_DEFAULT_CONFIG=/opt/neon/diana.yaml
ENV XDG_CONFIG_HOME=/config
ENV XDG_DATA_HOME=/data
ENV HEALTHCHECK_PORT=8080
COPY docker_overlay/ /

RUN apt-get update && \
    apt-get install -y \
    gcc \
    curl \
    jq \
    python3 \
    python3-dev \
    && pip install wheel

COPY . /neon_users_service
WORKDIR /neon_users_service
RUN pip install --no-cache-dir .[mq,mongodb]

HEALTHCHECK CMD "/opt/neon/healthcheck.sh"
CMD ["neon_users_service"]
