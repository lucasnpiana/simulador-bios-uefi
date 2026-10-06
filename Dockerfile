# Usa o Ubuntu 22.04 como base do nosso compilador universal
FROM ubuntu:22.04

# Instala as ferramentas de compilação de baixo nível
RUN apt-get update && apt-get install -y \
    build-essential \
    nasm \
    make \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Define a pasta de trabalho dentro do container
WORKDIR /codigo