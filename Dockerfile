FROM emscripten/emsdk:6.0.1@sha256:d0be652409a4d3362b8a36c3279dd1123ff1c9327e603d86d9361aa84f1d2e4c

RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf automake bison build-essential ca-certificates cmake curl flex gettext \
    git git-lfs libffi-dev libssl-dev libtool make ninja-build patch pkg-config \
    python3 python3-venv rsync unzip wget zlib1g-dev zstd \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /project
COPY . /project
CMD ["bash", "build.sh"]
