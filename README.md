<div align="center">

# Simulador de BIOS / BIOS Simulator

**Simulador acadêmico de BIOS/UEFI x86 em Python, com interface gráfica, POST, Secure Boot e QEMU opcional**
**Academic x86 BIOS/UEFI simulator in Python, with a GUI, POST, Secure Boot and optional QEMU**

<!-- BADGES: apague a abertura e o fechamento deste comentario para reativar
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![QEMU](https://img.shields.io/badge/QEMU-optional-FF6600?logo=qemu&logoColor=white)
![Status](https://img.shields.io/badge/status-academic%20project-red)
-->

[Português](#português) · [English](#english)

</div>

---

## Português

Simulador didático de BIOS/UEFI x86 em modo real, com interface gráfica (CustomTkinter). O núcleo é **100% Python** e roda sem nenhum software externo. O [QEMU](https://www.qemu.org/) é opcional e serve apenas para executar de verdade o `boot.bin`.

<!-- ![Screenshot](docs/screenshot.png) -->

### Funcionalidades

- **CMOS / NVRAM Setup**: ordem de boot, modo de boot (UEFI ou Legacy) e Secure Boot, salvos em `cmos_config.json`
- **POST** com log em tempo real, barra de progresso e leitura do RTC pelas portas de E/S `70h`/`71h`
- **Injeção de falhas**: erro de checksum da CMOS, assinatura MBR inválida, teclado ausente e falha de RAM
- **Secure Boot** por hash SHA-256 do `boot.bin`, gravado na CMOS na primeira execução
- **Memory & IVT Viewer**: dump hexadecimal da RAM simulada de 1 MB e vetores das interrupções INT 10h, 13h e 16h
- **MBR Inspector**: tamanho do setor, assinatura `0x55AA`, tabela de partições e desmontagem simplificada
- **Boot Timeline**: as 5 etapas da inicialização, destacadas em tempo real
- **CPU Registers**: AX, BX, CX, DX, CS, IP e endereço físico
- **Hardware Monitor**: temperatura, ventoinha e tensões (valores fictícios do `hardware_map.json`)
- **Aba Documentação**: explica cada seção, indica o que é simulado e traz um roteiro de experimentos para aula
- **Modo console** (`main.py`) e **testes automatizados** do núcleo (`pytest`)

### O que é Python e o que depende do QEMU

| Recurso | Implementação |
|---|---|
| CMOS, POST, falhas, Secure Boot | Simulação em Python |
| RAM, IVT, registradores, interrupções | Simulação em Python |
| Análise e desmontagem do MBR | Python (apenas alguns opcodes) |
| Hardware Monitor | Dados estáticos em JSON |
| **BOOT EXECUTE** (execução real do `boot.bin`) | **QEMU** (opcional) |

Sem o QEMU, o **BOOT EXECUTE** apenas valida o bootloader e registra no log que ele foi entregue em `0x7C00`. O conteúdo do `boot.bin` não é copiado para a RAM simulada nem executado pelo Python.

### Pré-requisitos

- Python 3.10+
- `customtkinter` e `pytest` (`pip install customtkinter pytest`)
- `tkinter` (já incluso no Python do Windows; no Linux: `sudo apt install python3-tk`)
- QEMU (opcional): `qemu-system-x86_64` ou `qemu-system-i386` disponível no `PATH`

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
   sudo apt install python3-venv python3-pip python3-tk qemu-system-x86 -y
   ```
   > O QEMU é opcional; omita `qemu-system-x86` se não for usá-lo.
2. Crie e ative o ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install customtkinter pytest
   ```
4. Execute a interface gráfica, o modo console e os testes:
   ```bash
   python3 bios_gui.py
   python3 main.py
   pytest
   ```

### Preparando o `boot.bin`

O POST precisa de uma imagem `boot.bin` de **exatamente 512 bytes**, terminada em `55 AA`, na pasta do projeto. Você pode usar o botão **Select boot.bin** da aba MBR Inspector para escolher outro arquivo, ou gerar uma imagem de teste:

```bash
python -c "d=bytearray(512); d[0:5]=b'\xFA\xB8\x34\x12\xF4'; d[510:512]=b'\x55\xAA'; open('boot.bin','wb').write(d)"
```

Essa imagem contém `CLI`, `MOV AX, 0x1234` e `HLT`. O projeto inclui o `boot.asm`. Para regenerar o `boot.bin` a partir dele, instale o [NASM](https://www.nasm.us/) e execute `nasm -f bin boot.asm -o boot.bin`.

### Estrutura do projeto

- `bios_gui.py`: interface gráfica (CustomTkinter), incluindo a aba Documentação
- `bios_core.py`: núcleo do simulador (CPU, RAM, IVT, CMOS, POST, Secure Boot e MBR), sem dependência da interface
- `main.py`: ponto de entrada em modo console
- `test_bios_core.py`: testes automatizados do núcleo (`pytest`)
- `boot.asm` / `boot.bin`: código Assembly e imagem do setor de boot usada pelo simulador
- `cmos_config.json`: configurações da CMOS (criado ao salvar o Setup)
- `hardware_map.json`: dados do Hardware Monitor (criado com valores padrão na primeira execução)

### Autores

[@lucasnpiana](https://github.com/lucasnpiana)
[@felipenespolo](https://github.com/felipenespolo)
[@arthurfelini]((https://github.com/feliniarthur))
[@gabrielandreis]((https://github.com/gabriel-2823))


---

## English

An educational x86 real-mode BIOS/UEFI simulator with a graphical interface (CustomTkinter). The core is **100% Python** and runs without any external software. [QEMU](https://www.qemu.org/) is optional and is only used to actually execute `boot.bin`.

<!-- ![Screenshot](docs/screenshot.png) -->

### Features

- **CMOS / NVRAM Setup**: boot order, boot mode (UEFI or Legacy) and Secure Boot, stored in `cmos_config.json`
- **POST** with a live log, progress bar and RTC reads through I/O ports `70h`/`71h`
- **Fault injection**: CMOS checksum error, invalid MBR signature, missing keyboard and RAM failure
- **Secure Boot** based on the SHA-256 hash of `boot.bin`, stored in the CMOS on first run
- **Memory & IVT Viewer**: hex dump of the 1 MB simulated RAM and the INT 10h, 13h and 16h vectors
- **MBR Inspector**: sector size, `0x55AA` signature, partition table and simplified disassembly
- **Boot Timeline**: the 5 boot stages, highlighted in real time
- **CPU Registers**: AX, BX, CX, DX, CS, IP and physical address
- **Hardware Monitor**: temperature, fan and voltages (fictitious values from `hardware_map.json`)
- **Documentation tab**: explains every section, states what is simulated, and includes a classroom experiment guide
- **Console mode** (`main.py`) and **automated tests** for the core (`pytest`)

### What is Python and what needs QEMU

| Feature | Implementation |
|---|---|
| CMOS, POST, faults, Secure Boot | Python simulation |
| RAM, IVT, registers, interrupts | Python simulation |
| MBR analysis and disassembly | Python (only a few opcodes) |
| Hardware Monitor | Static JSON data |
| **BOOT EXECUTE** (real execution of `boot.bin`) | **QEMU** (optional) |

Without QEMU, **BOOT EXECUTE** only validates the bootloader and logs that it was handed over at `0x7C00`. The contents of `boot.bin` are neither copied into the simulated RAM nor executed by Python.

### Prerequisites

- Python 3.10+
- `customtkinter` and `pytest` (`pip install customtkinter pytest`)
- `tkinter` (bundled with Python on Windows; on Linux: `sudo apt install python3-tk`)
- QEMU (optional): `qemu-system-x86_64` or `qemu-system-i386` available on the `PATH`

### Running on Windows

1. Open PowerShell in the project folder.
2. Create and activate the virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   > If you get a permission error, run first: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
3. Install the dependencies:
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
   sudo apt install python3-venv python3-pip python3-tk qemu-system-x86 -y
   ```
   > QEMU is optional; omit `qemu-system-x86` if you will not use it.
2. Create and activate the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install customtkinter pytest
   ```
4. Run the graphical interface, the console mode and the tests:
   ```bash
   python3 bios_gui.py
   python3 main.py
   pytest
   ```

### Preparing `boot.bin`

POST needs a `boot.bin` image of **exactly 512 bytes**, ending in `55 AA`, in the project folder. You can use the **Select boot.bin** button in the MBR Inspector tab to pick another file, or generate a test image:

```bash
python -c "d=bytearray(512); d[0:5]=b'\xFA\xB8\x34\x12\xF4'; d[510:512]=b'\x55\xAA'; open('boot.bin','wb').write(d)"
```

This image contains `CLI`, `MOV AX, 0x1234` and `HLT`. The project includes `boot.asm`. To regenerate `boot.bin` from it, install [NASM](https://www.nasm.us/) and run `nasm -f bin boot.asm -o boot.bin`.

### Project structure

- `bios_gui.py`: graphical interface (CustomTkinter), including the Documentation tab
- `bios_core.py`: simulator core (CPU, RAM, IVT, CMOS, POST, Secure Boot and MBR), independent of the GUI
- `main.py`: console-mode entry point
- `test_bios_core.py`: automated tests for the core (`pytest`)
- `boot.asm` / `boot.bin`: Assembly source and boot sector image used by the simulator
- `cmos_config.json`: CMOS settings (created when the Setup is saved)
- `hardware_map.json`: Hardware Monitor data (created with defaults on first run)

### Authors

[@lucasnpiana](https://github.com/lucasnpiana)
[@felipenespolo](https://github.com/felipenespolo)
