# Image "station/greengrass": one simulated pump.
# The AWS IoT Greengrass V2 nucleus is the real one; the audio and the model live on the device.
# Greengrass in Docker requires a Linux host:
#   https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html
ARG BASE_IMAGE=debian:12-slim
FROM ${BASE_IMAGE}

# Pinned nucleus version. The zip comes from the official URL; if you pass GREENGRASS_SHA256,
# the build verifies the hash (the build prints the hash it downloaded).
ARG GREENGRASS_VERSION=2.18.3
ARG GREENGRASS_SHA256=""

ENV DEBIAN_FRONTEND=noninteractive \
    GGC_ROOT_PATH=/greengrass/v2 \
    TINI_KILL_PROCESS_GROUP=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# What the nucleus needs on Linux: Java (8 or later), sudo, ps, sh, ln, cp, kill, id, uname, grep.
# python3 is for the component: the recipe installs nothing.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl unzip sudo procps python3 python3-pip openjdk-17-jre-headless \
 && rm -rf /var/lib/apt/lists/* \
 && grep -Eq '^root[[:space:]]+ALL=\(ALL(:ALL)?\)[[:space:]]+ALL' /etc/sudoers

# Component dependencies, pinned (the same ones the model was measured with).
RUN pip3 install --no-cache-dir --break-system-packages \
      numpy==2.2.6 onnxruntime==1.23.2 awsiotsdk==1.31.0 awscrt==0.36.1

# User that runs the components (Greengrass launches them with sudo)
RUN groupadd --system ggc_group \
 && useradd --system --create-home --gid ggc_group ggc_user

# Nucleus installer
RUN curl -fsSL "https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-${GREENGRASS_VERSION}.zip" -o /tmp/greengrass.zip \
 && sha256sum /tmp/greengrass.zip \
 && if [ -n "${GREENGRASS_SHA256}" ]; then echo "${GREENGRASS_SHA256}  /tmp/greengrass.zip" | sha256sum -c -; fi \
 && unzip -q /tmp/greengrass.zip -d /opt/greengrass-installer \
 && rm /tmp/greengrass.zip \
 && java -jar /opt/greengrass-installer/lib/Greengrass.jar --version

# Amazon root CA: the nucleus needs it when the pump's certificate comes from Terraform
RUN curl -fsSL https://www.amazontrust.com/repository/AmazonRootCA1.pem -o /opt/greengrass-installer/AmazonRootCA1.pem \
 && grep -q "BEGIN CERTIFICATE" /opt/greengrass-installer/AmazonRootCA1.pem
ENV GREENGRASS_VERSION=${GREENGRASS_VERSION}

RUN mkdir -p /greengrass/v2 /data/station /run/station
COPY entrypoint.sh /usr/local/bin/station-entrypoint.sh
RUN chmod 755 /usr/local/bin/station-entrypoint.sh

# Always run with --init (docker run --init): without it, docker stop does not shut the nucleus down cleanly.
ENTRYPOINT ["/usr/local/bin/station-entrypoint.sh"]
