"""
bios_core.py
Núcleo 100% Python do simulador de BIOS/UEFI.
Gerencia registradores simulados, memória de 1 MB, vetor de interrupções,
validação de Secure Boot, inventário de hardware e persistência da CMOS.
"""

import hashlib
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "cmos_config.json")
HARDWARE_FILE = os.path.join(BASE_DIR, "hardware_map.json")

VALID_BOOT_DEVICES = ("HDD", "USB", "NETWORK", "FLOPPY")
VALID_BOOT_MODES = ("LEGACY", "UEFI")
MAX_MEMORY_KB = 1024  # 1 MB simulado

DEFAULT_CONFIG = {
    "boot_order": ["HDD", "USB", "NETWORK"],
    "boot_mode": "UEFI",
    "secure_boot": True,
    "secure_boot_hash": "",
    "memory_kb": 64,
    "date": "2026-11-10",
    "supervisor_password": "",
    "boot_password_enabled": False
}

DEFAULT_HARDWARE = {
    "cpu": "x86-64 Simulated Processor @ 3.40 GHz",
    "ram_total_mb": 8192,
    "storage_devices": [
        {"slot": "SATA 0", "type": "SSD", "model": "Simulated SSD 256GB", "status": "OK"},
        {"slot": "SATA 1", "type": "HDD", "model": "Simulated HDD 1TB", "status": "OK"}
    ],
    "gpu": "VGA Compatible Graphics Controller",
    "fan_rpm": 2200,
    "cpu_temp_celsius": 42.5,
    "voltages": {"v3_3": 3.31, "v5_0": 5.02, "v12_0": 12.05}
}

# --- Estado do Processador e Memória Física em Python Nativo ----------------

_registers = {
    "AX": 0x0000, "BX": 0x0000, "CX": 0x0000, "DX": 0x0000,
    "SI": 0x0000, "DI": 0x0000, "BP": 0x0000, "SP": 0xFFFE,
    "CS": 0xF000, "DS": 0x0000, "SS": 0x0000, "ES": 0x0000,
    "IP": 0xFFF0,
    "physical_address": 0xFFFF0
}

# Array de 1 MB (1024 KB) para emulação direta de RAM física em Python
_simulated_memory = bytearray(MAX_MEMORY_KB * 1024)


# --- API de CPU e Memória (Substitui o código C / ctypes) -------------------

def _update_physical_address():
    """Calcula o endereço físico x86 (Real Mode) a partir do segmento CS e offset IP."""
    phys = ((_registers["CS"] & 0xFFFF) << 4) + (_registers["IP"] & 0xFFFF)
    _registers["physical_address"] = phys & 0xFFFFF


def reset_cpu():
    """Reinicia o estado dos registradores da CPU (x86 Reset Vector)."""
    global _registers
    _registers = {
        "AX": 0x0000, "BX": 0x0000, "CX": 0x0000, "DX": 0x0000,
        "SI": 0x0000, "DI": 0x0000, "BP": 0x0000, "SP": 0xFFFE,
        "CS": 0xF000, "DS": 0x0000, "SS": 0x0000, "ES": 0x0000,
        "IP": 0xFFF0,
        "physical_address": 0xFFFF0
    }


def get_registers() -> dict:
    """Retorna o estado atual de todos os registradores."""
    _update_physical_address()
    return _registers.copy()


def set_register(name: str, value: int) -> bool:
    """Define o valor de um registrador específico (16 bits)."""
    name_upper = name.upper()
    if name_upper in _registers and name_upper != "physical_address":
        _registers[name_upper] = value & 0xFFFF
        _update_physical_address()
        return True
    return False


def get_register(name: str) -> int | None:
    """Lê o valor de um registrador específico."""
    name_upper = name.upper()
    return _registers.get(name_upper, None)


def post_check_memory(size_kb: int, simulate_failure: bool = False) -> bool:
    """Executa o teste de leitura/escrita de RAM durante a rotina de POST."""
    if simulate_failure:
        return False
    
    target_bytes = min(size_kb * 1024, len(_simulated_memory))
    try:
        # Teste de padrões de memória nos blocos simulados
        for addr in range(0, target_bytes, 1024):
            _simulated_memory[addr] = 0xAA
            if _simulated_memory[addr] != 0xAA:
                return False
            _simulated_memory[addr] = 0x00
        return True
    except IndexError:
        return False


def peek_memory(address: int) -> int:
    """Lê 1 byte diretamente de um endereço de memória física."""
    addr = address & 0xFFFFF
    return _simulated_memory[addr]


def poke_memory(address: int, value: int) -> bool:
    """Escreve 1 byte em um endereço da memória física."""
    addr = address & 0xFFFFF
    _simulated_memory[addr] = value & 0xFF
    return True


# --- Simulação de Serviços de Interrupção (BIOS Interrupt Vectors) --------

def handle_interrupt(int_number: int, ah_value: int, payload: str = "") -> dict:
    """
    Simula o tratamento de interrupções clássicas do x86 (HAL da BIOS):
    - INT 10h: Serviços de Vídeo
    - INT 13h: Serviços de Disco
    - INT 16h: Serviços de Teclado
    """
    result = {"status": "SUCCESS", "message": ""}
    
    if int_number == 0x10:  # INT 10h - Vídeo
        if ah_value == 0x0E:  # Escrever caractere modo Teletype
            result["message"] = f"[INT 10h, AH=0E] Vídeo: Caractere '{payload}' enviado à tela."
        else:
            result["message"] = f"[INT 10h] Rotina de vídeo executada (AH={hex(ah_value)})."
            
    elif int_number == 0x13:  # INT 13h - Disco
        if ah_value == 0x02:  # Leitura de setor MBR
            result["message"] = f"[INT 13h, AH=02] Setor 0x7C00 lido com sucesso."
        elif ah_value == 0x00:  # Reset de controladora de disco
            result["message"] = f"[INT 13h, AH=00] Controladora de disco reiniciada."
        else:
            result["message"] = f"[INT 13h] Serviço de armazenamento (AH={hex(ah_value)}) OK."
            
    elif int_number == 0x16:  # INT 16h - Teclado
        result["message"] = f"[INT 16h] Interrupção de teclado acionada."
    else:
        result["status"] = "ERROR"
        result["message"] = f"Interrupção INT {hex(int_number)} não implementada."

    return result


# --- UEFI & Verificação de Secure Boot -------------------------------------

def get_bootloader_hash(file_path: str = "boot.bin") -> str:
    """Calcula o hash SHA-256 da assinatura do bootloader."""
    full_path = os.path.join(BASE_DIR, file_path)
    if not os.path.exists(full_path):
        return ""
    with open(full_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verify_secure_boot(file_path: str = "boot.bin") -> tuple[bool, str]:
    """Valida a assinatura do bootloader com a chave confiável da NVRAM."""
    config = load_config()
    
    if not config.get("secure_boot", True):
        return True, "Secure Boot [DESATIVADO]. Boot permitido."
        
    current_hash = get_bootloader_hash(file_path)
    if not current_hash:
        return False, "Erro de Boot: Imagem 'boot.bin' não encontrada."
        
    authorized_hash = config.get("secure_boot_hash", "")
    
    # Se for a primeira execução, armazena a hash atual como a chave autorizada
    if not authorized_hash:
        config["secure_boot_hash"] = current_hash
        save_config(config)
        return True, f"Assinatura gravada na NVRAM ({current_hash[:10]}...). Secure Boot OK."
        
    if current_hash == authorized_hash:
        return True, f"Assinatura SHA-256 autorizada ({current_hash[:10]}...). Boot UEFI OK."
    else:
        return False, f"VIOLAÇÃO DE SECURE BOOT! Assinatura ({current_hash[:10]}...) não coincide!"


# --- Inventário de Hardware (Tabela SMBIOS / DMI) --------------------------

def load_hardware_map() -> dict:
    """Lê as especificações do hardware simulado (CPU, Discos, Voltagens)."""
    if os.path.exists(HARDWARE_FILE):
        try:
            with open(HARDWARE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
            
    save_hardware_map(DEFAULT_HARDWARE)
    return DEFAULT_HARDWARE.copy()


def save_hardware_map(hw_data: dict) -> None:
    with open(HARDWARE_FILE, "w", encoding="utf-8") as f:
        json.dump(hw_data, f, indent=2, ensure_ascii=False)


# --- Gerenciamento da Configuração CMOS/NVRAM --------------------------------

def validate_config(config: dict) -> list[str]:
    """Valida se a estrutura de dados da CMOS está correta."""
    errors = []

    boot_order = config.get("boot_order")
    if not isinstance(boot_order, list) or not boot_order:
        errors.append("boot_order precisa ser uma lista não vazia.")
    else:
        for device in boot_order:
            if device not in VALID_BOOT_DEVICES:
                errors.append(f"Dispositivo de boot desconhecido: {device!r}.")

    boot_mode = config.get("boot_mode", "UEFI")
    if boot_mode not in VALID_BOOT_MODES:
        errors.append(f"Modo de boot inválido: {boot_mode!r}.")

    memory_kb = config.get("memory_kb")
    if not isinstance(memory_kb, int) or not (1 <= memory_kb <= MAX_MEMORY_KB):
        errors.append(f"memory_kb precisa ser um inteiro entre 1 e {MAX_MEMORY_KB}.")

    return errors


def load_config() -> dict:
    """Carrega as configurações salvas no arquivo JSON (CMOS)."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            return DEFAULT_CONFIG.copy()

        if not validate_config(config):
            merged_config = DEFAULT_CONFIG.copy()
            merged_config.update(config)
            return merged_config

        return DEFAULT_CONFIG.copy()

    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """Salva a configuração CMOS atualizada."""
    errors = validate_config(config)
    if errors:
        raise ValueError("Configuração inválida: " + "; ".join(errors))
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)