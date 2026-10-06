# Simulador de BIOS — Protótipo

Um emulador/simulador de BIOS x86 com suporte a interface gráfica (GUI), registadores C compilados, verificação de POST e integração com QEMU e Docker.

---

## Pré-requisitos

### Para Windows
* **Python 3.10+** (com `pip` e suporte a ambientes virtuais `venv`)
* **QEMU** (opcional, para execução do bootloader `boot.bin`)
* **GCC / MinGW / MSYS2** (opcional, para recompilar a biblioteca C `registers.dll`)

### Para Linux (Ubuntu / Debian / Arch / Fedora)
* **Python 3.10+** (com `python3-venv` e `python3-pip`)
* **QEMU** (`qemu-system-x86`)
* **GCC / Make** (para compilar a biblioteca C `registers.so`)

---

## Como Executar no Windows

### Método 1: Via Ambiente Virtual Python (Recomendado)

1. Abrir o terminal PowerShell na pasta do projeto.
2. **Criar e ativar o ambiente virtual:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(Caso ocorra erro de permissão no PowerShell, execute `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` antes)*

3. **Instalar as dependências:**
   ```powershell
   pip install customtkinter pytest
   ```

4. **Executar a Interface Gráfica (GUI):**
   ```powershell
   python bios_gui.py
   ```

5. **Executar em modo linha de comando ou testes:**
   ```powershell
   python main.py
   pytest
   ```

---

## Como Executar no Linux

### Método 1: Via Ambiente Virtual Python

1. **Instalar dependências do sistema (Exemplo Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install python3-venv python3-pip qemu-system-x86 build-essential -y
   ```

2. **Criar e ativar o ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar as dependências:**
   ```bash
   pip install customtkinter pytest
   ```

4. **Compilar a biblioteca C (se necessário):**
   ```bash
   make
   # Ou manualmente:
   gcc -shared -o registers.so -fPIC registers.c
   ```

5. **Executar a Interface Gráfica (GUI):**
   ```bash
   python3 bios_gui.py
   ```

6. **Executar os testes automatizados:**
   ```bash
   pytest
   ```

---

## Como Executar via Docker (Ambiente Isolado)

1. **Construir a imagem Docker:**
   ```bash
   docker build -t simulador-bios .
   ```

2. **Executar o container interativo:**
   ```bash
   docker run -it --rm simulador-bios
   ```

3. **Executar os testes automatizados via Docker:**
   ```bash
   docker run --rm simulador-bios pytest
   ```

---

## Estrutura do Projeto

* `bios_gui.py`: Interface gráfica interativa da BIOS (desenvolvida em CustomTkinter).
* `bios_core.py`: Lógica central do simulador de BIOS e rotinas de POST.
* `main.py`: Ponto de entrada do sistema em modo console/terminal.
* `registers.c` / `registers.h`: Código em C para manipulação dos registradores simulados.
* `boot.asm` / `boot.bin`: Código Assembly e imagem compilada de bootloader simulado.
* `cmos_config.json`: Persistência de configurações CMOS/BIOS (ex: ordem de boot).
* `Dockerfile` & `Makefile`: Arquivos de automação para compilação e conteinerização.