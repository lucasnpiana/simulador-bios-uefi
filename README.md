<div align="center">

# Simulador de BIOS / BIOS Simulator

**Simulador de BIOS x86 com interface gráfica, registradores em C, POST, QEMU e Docker**
**x86 BIOS simulator with a GUI, C registers, POST, QEMU and Docker**

<!-- BADGES: apague a abertura e o fechamento deste comentario para reativar
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![C](https://img.shields.io/badge/C-registers-00599C?logo=c&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-build-2496ED?logo=docker&logoColor=white)
![QEMU](https://img.shields.io/badge/QEMU-emulator-FF6600?logo=qemu&logoColor=white)
![Status](https://img.shields.io/badge/status-academic%20project-red)
-->

[Português](#português) · [English](#english)

</div>

---

## Português

Protótipo de um emulador/simulador de BIOS x86 com interface gráfica (GUI), registradores implementados em C, verificação de POST e integração com QEMU e Docker.

<!-- ![Screenshot](docs/screenshot.png) -->

### Funcionalidades

- Simulação de **POST** com log em tempo real e barra de progresso
- Monitor de registradores (AX, BX, CX, DX, CS, IP) e endereço físico
- **CMOS Setup** para escolher a ordem de boot, salva em `cmos_config.json`
- Simulação de falha de RAM
- Exportação do log do POST
- Compilação do `boot.bin` via Docker e execução no **QEMU**

### Pré-requisitos

**Windows**
- Python 3.10+ (com `pip` e `venv`)
- QEMU (opcional, para executar o bootloader `boot.bin`)
- GCC / MinGW / MSYS2 (opcional, para recompilar a biblioteca C `registers.dll`)
- Docker Desktop (para o botão **BOOT EXECUTE**)

**Linux (Ubuntu / Debian / Arch / Fedora)**
- Python 3.10+ (com `python3-venv` e `python3-pip`)
- QEMU (`qemu-system-x86`)
- GCC / Make (para compilar a biblioteca C `registers.so`)

### Como executar no Windows

1. Abra o PowerShell na pasta do projeto.
2. Crie e ative o ambiente virtual:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   > Se ocorrer erro de permissão, execute antes: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
3. Instale as dependências:
   ```powershell
   pip install customtkinter pytest
   ```
4. Execute a interface gráfica:
   ```powershell
   python bios_gui.py
   ```
5. Modo console ou testes:
   ```powershell
   python main.py
   pytest
   ```

### Como executar no Linux

1. Instale as dependências do sistema (Ubuntu/Debian):
   ```bash
   sudo apt update
   sudo apt install python3-venv python3-pip qemu-system-x86 build-essential -y
   ```
2. Crie e ative o ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install customtkinter pytest
   ```
4. Compile a biblioteca C (se necessário):
   ```bash
   make
   # ou manualmente:
   gcc -shared -o registers.so -fPIC registers.c
   ```
5. Execute a interface gráfica e os testes:
   ```bash
   python3 bios_gui.py
   pytest
   ```

### Como executar via Docker

O botão **BOOT EXECUTE** da interface usa a imagem `sys-compilador` para compilar o `boot.bin`. Gere-a uma vez:

```bash
docker build -t sys-compilador .
```

Para o ambiente isolado completo:

```bash
docker build -t simulador-bios .
docker run -it --rm simulador-bios
docker run --rm simulador-bios pytest
```

### Estrutura do projeto

- `bios_gui.py`: interface gráfica interativa (CustomTkinter)
- `bios_core.py`: lógica central do simulador e rotinas de POST
- `main.py`: ponto de entrada em modo console
- `registers.c` / `registers.h`: manipulação dos registradores simulados, em C
- `boot.asm` / `boot.bin`: código Assembly e imagem do bootloader simulado
- `cmos_config.json`: persistência das configurações CMOS/BIOS (ex.: ordem de boot)
- `Dockerfile` e `Makefile`: automação de compilação e conteinerização

### Autores

[@lucasnpiana](https://github.com/lucasnpiana)
[@felipenespolo](https://github.com/felipenespolo)

---

## English

A prototype of an x86 BIOS emulator/simulator with a graphical interface (GUI), registers implemented in C, POST verification, and QEMU and Docker integration.

<!-- ![Screenshot](docs/screenshot.png) -->

### Features

- **POST** simulation with a live log and progress bar
- Register monitor (AX, BX, CX, DX, CS, IP) and physical address
- **CMOS Setup** to choose the boot order, stored in `cmos_config.json`
- RAM failure simulation
- POST log export
- `boot.bin` build through Docker and execution on **QEMU**

### Prerequisites

**Windows**
- Python 3.10+ (with `pip` and `venv`)
- QEMU (optional, to run the `boot.bin` bootloader)
- GCC / MinGW / MSYS2 (optional, to rebuild the C library `registers.dll`)
- Docker Desktop (for the **BOOT EXECUTE** button)

**Linux (Ubuntu / Debian / Arch / Fedora)**
- Python 3.10+ (with `python3-venv` and `python3-pip`)
- QEMU (`qemu-system-x86`)
- GCC / Make (to build the C library `registers.so`)

### Running on Windows

1. Open PowerShell in the project folder.
2. Create and activate the virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   > If you get a permission error, run first: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
3. Install dependencies:
   ```powershell
   pip install customtkinter pytest
   ```
4. Run the graphical interface:
   ```powershell
   python bios_gui.py
   ```
5. Console mode or tests:
   ```powershell
   python main.py
   pytest
   ```

### Running on Linux

1. Install system dependencies (Ubuntu/Debian):
   ```bash
   sudo apt update
   sudo apt install python3-venv python3-pip qemu-system-x86 build-essential -y
   ```
2. Create and activate the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install customtkinter pytest
   ```
4. Build the C library (if needed):
   ```bash
   make
   # or manually:
   gcc -shared -o registers.so -fPIC registers.c
   ```
5. Run the GUI and the tests:
   ```bash
   python3 bios_gui.py
   pytest
   ```

### Running with Docker

The interface's **BOOT EXECUTE** button uses the `sys-compilador` image to build `boot.bin`. Build it once:

```bash
docker build -t sys-compilador .
```

For the full isolated environment:

```bash
docker build -t simulador-bios .
docker run -it --rm simulador-bios
docker run --rm simulador-bios pytest
```

### Project structure

- `bios_gui.py`: interactive graphical interface (CustomTkinter)
- `bios_core.py`: core simulator logic and POST routines
- `main.py`: console-mode entry point
- `registers.c` / `registers.h`: simulated register handling, written in C
- `boot.asm` / `boot.bin`: Assembly source and image of the simulated bootloader
- `cmos_config.json`: persisted CMOS/BIOS settings (e.g. boot order)
- `Dockerfile` and `Makefile`: build and containerization automation

### Authors

[@lucasnpiana](https://github.com/lucasnpiana)
[@felipenespolo](https://github.com/felipenespolo)
