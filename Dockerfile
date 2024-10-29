FROM python:3.10-slim

LABEL vendor=neon.ai \
    ai.neon.name="neon-users-service"

ENV OVOS_CONFIG_BASE_FOLDER neon
ENV OVOS_CONFIG_FILENAME diana.yaml
ENV XDG_CONFIG_HOME /config
COPY docker_overlay/ /

RUN apt-get update && \
    apt-get install -y \
    gcc \
    python3  \
    python3-dev  \
    && pip install wheel

ADD . /neon_users_service
WORKDIR /neon_users_service
RUN pip install .[mq]

CMD ["neon_users_service"]