# Imagen "estacion/greengrass": una bomba simulada.
# El nucleus de AWS IoT Greengrass V2 es el real; el audio y el modelo viven en el equipo.
# Greengrass en Docker pide un host Linux:
#   https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html
ARG BASE_IMAGE=debian:12-slim
FROM ${BASE_IMAGE}

# Versión fija del nucleus. El zip sale de la URL oficial; si pasas GREENGRASS_SHA256,
# el build verifica el hash (el build imprime el hash que descargó).
ARG GREENGRASS_VERSION=2.18.3
ARG GREENGRASS_SHA256=""

ENV DEBIAN_FRONTEND=noninteractive \
    GGC_ROOT_PATH=/greengrass/v2 \
    TINI_KILL_PROCESS_GROUP=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# Lo que pide el nucleus en Linux: Java (8 o más), sudo, ps, sh, ln, cp, kill, id, uname, grep.
# python3 es del componente: la receta no instala nada.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl unzip sudo procps python3 python3-pip openjdk-17-jre-headless \
 && rm -rf /var/lib/apt/lists/* \
 && grep -Eq '^root[[:space:]]+ALL=\(ALL(:ALL)?\)[[:space:]]+ALL' /etc/sudoers

# Dependencias del componente, con versión fija (las mismas con las que se midió el modelo).
RUN pip3 install --no-cache-dir --break-system-packages \
      numpy==2.2.6 onnxruntime==1.23.2 awsiotsdk==1.31.0 awscrt==0.36.1

# Usuario que corre los componentes (Greengrass los lanza con sudo)
RUN groupadd --system ggc_group \
 && useradd --system --create-home --gid ggc_group ggc_user

# Instalador del nucleus
RUN curl -fsSL "https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-${GREENGRASS_VERSION}.zip" -o /tmp/greengrass.zip \
 && sha256sum /tmp/greengrass.zip \
 && if [ -n "${GREENGRASS_SHA256}" ]; then echo "${GREENGRASS_SHA256}  /tmp/greengrass.zip" | sha256sum -c -; fi \
 && unzip -q /tmp/greengrass.zip -d /opt/greengrass-installer \
 && rm /tmp/greengrass.zip \
 && java -jar /opt/greengrass-installer/lib/Greengrass.jar --version

# CA raíz de Amazon: la necesita el nucleus cuando el certificado de la bomba viene de Terraform
RUN curl -fsSL https://www.amazontrust.com/repository/AmazonRootCA1.pem -o /opt/greengrass-installer/AmazonRootCA1.pem \
 && grep -q "BEGIN CERTIFICATE" /opt/greengrass-installer/AmazonRootCA1.pem
ENV GREENGRASS_VERSION=${GREENGRASS_VERSION}

RUN mkdir -p /greengrass/v2 /data/estacion /run/estacion
COPY entrypoint.sh /usr/local/bin/estacion-entrypoint.sh
RUN chmod 755 /usr/local/bin/estacion-entrypoint.sh

# Ejecutar siempre con --init (docker run --init): sin eso, docker stop no apaga bien el nucleus.
ENTRYPOINT ["/usr/local/bin/estacion-entrypoint.sh"]
