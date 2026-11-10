"""Núcleo 100% Python do simulador acadêmico BIOS/UEFI x86."""
import hashlib
import json
import os
import zlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "cmos_config.json")
HARDWARE_FILE = os.path.join(BASE_DIR, "hardware_map.json")
VALID_BOOT_DEVICES = ("HDD", "USB", "NETWORK", "FLOPPY")
VALID_BOOT_MODES = ("LEGACY", "UEFI")
MAX_MEMORY_KB = 1024

DEFAULT_CONFIG = {
    "boot_order": ["HDD", "USB", "NETWORK"], "boot_mode": "UEFI",
    "secure_boot": True, "secure_boot_hash": "", "memory_kb": 64,
    "date": "2026-11-10", "supervisor_password": "",
    "boot_password_enabled": False,
    "fault_injection": {"cmos_checksum_error": False,
                        "invalid_mbr_signature": False,
                        "keyboard_missing": False},
}
DEFAULT_HARDWARE = {
    "cpu": "x86-64 Simulated Processor @ 3.40 GHz", "ram_total_mb": 8192,
    "storage_devices": [
        {"slot": "SATA 0", "type": "SSD", "model": "Simulated SSD 256GB", "status": "OK"},
        {"slot": "SATA 1", "type": "HDD", "model": "Simulated HDD 1TB", "status": "OK"}],
    "gpu": "VGA Compatible Graphics Controller", "fan_rpm": 2200,
    "cpu_temp_celsius": 42.5,
    "voltages": {"v3_3": 3.31, "v5_0": 5.02, "v12_0": 12.05}}

_registers = {"AX": 0, "BX": 0, "CX": 0, "DX": 0, "SI": 0, "DI": 0,
              "BP": 0, "SP": 0xFFFE, "CS": 0xF000, "DS": 0, "SS": 0,
              "ES": 0, "IP": 0xFFF0, "physical_address": 0xFFFF0}
_simulated_memory = bytearray(MAX_MEMORY_KB * 1024)

# CMOS RTC simplificado: registradores clássicos BCD (segundos/minutos/horas/dia/mês/ano).
_cmos = {0x00: 0x00, 0x02: 0x00, 0x04: 0x12, 0x07: 0x10,
         0x08: 0x11, 0x09: 0x26, 0x0A: 0x26, 0x0B: 0x02, 0x0D: 0x80}
_cmos_index = 0

# Ponteiros de rotina BIOS didáticos: offset, segmento. INT 10h/13h/16h têm
# alvos explícitos; todos os demais vetores recebem um stub único de firmware.
_IVT_TARGETS = {0x10: (0x0100, 0xF000), 0x13: (0x0200, 0xF000),
                0x16: (0x0300, 0xF000)}

def _update_physical_address():
    _registers["physical_address"] = (((_registers["CS"] & 0xFFFF) << 4) +
                                       (_registers["IP"] & 0xFFFF)) & 0xFFFFF

def _setup_ivt():
    """Preenche os 256 vetores: cada entrada é OFFSET(LE), SEGMENTO(LE)."""
    stub = (0x00F0, 0xF000)
    for number in range(256):
        offset, segment = _IVT_TARGETS.get(number, stub)
        entry = number * 4
        _simulated_memory[entry:entry + 4] = bytes((offset & 0xFF, offset >> 8,
                                                     segment & 0xFF, segment >> 8))

def reset_cpu():
    global _registers
    _registers = {"AX": 0, "BX": 0, "CX": 0, "DX": 0, "SI": 0, "DI": 0,
                  "BP": 0, "SP": 0xFFFE, "CS": 0xF000, "DS": 0, "SS": 0,
                  "ES": 0, "IP": 0xFFF0, "physical_address": 0xFFFF0}
    _setup_ivt()

def get_registers():
    _update_physical_address()
    return _registers.copy()

def set_register(name: str, value: int) -> bool:
    key = name.upper()
    if key in _registers and key != "physical_address":
        _registers[key] = int(value) & 0xFFFF
        _update_physical_address()
        return True
    return False

def get_register(name: str):
    return _registers.get(name.upper())

def post_check_memory(size_kb: int, simulate_failure: bool = False) -> bool:
    if simulate_failure:
        return False
    target_bytes = min(max(int(size_kb), 1) * 1024, len(_simulated_memory))
    try:
        for addr in range(0, target_bytes, 1024):
            _simulated_memory[addr] = 0xAA
            if _simulated_memory[addr] != 0xAA:
                return False
            _simulated_memory[addr] = 0
        return True
    except IndexError:
        return False

def peek_memory(address: int) -> int:
    if not 0 <= int(address) < len(_simulated_memory):
        raise ValueError("Endereço de memória fora da RAM simulada")
    return _simulated_memory[int(address)]

def poke_memory(address: int, value: int) -> bool:
    if not 0 <= int(address) < len(_simulated_memory):
        raise ValueError("Endereço de memória fora da RAM simulada")
    _simulated_memory[int(address)] = int(value) & 0xFF
    return True

def get_memory_hex_dump(start_address: int, size: int) -> str:
    """Dump no formato endereço | bytes hex | ASCII imprimível."""
    start, count = int(start_address), int(size)
    if start < 0 or count < 0 or start + count > len(_simulated_memory):
        raise ValueError("Intervalo solicitado está fora da memória física de 1 MB")
    lines = ["ENDEREÇO  | HEX                                               | ASCII"]
    for base in range(start, start + count, 16):
        chunk = _simulated_memory[base:min(base + 16, start + count)]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{base:05X}    | {hex_part:<47} | {ascii_part}")
    return "\n".join(lines)

def get_ivt_entries(start: int = 0, count: int = 256):
    if start < 0 or count < 0 or start + count > 256:
        raise ValueError("Faixa de vetores inválida")
    result = []
    for n in range(start, start + count):
        p = n * 4
        offset = _simulated_memory[p] | (_simulated_memory[p + 1] << 8)
        segment = _simulated_memory[p + 2] | (_simulated_memory[p + 3] << 8)
        result.append({"interrupt": n, "segment": segment, "offset": offset,
                       "physical": ((segment << 4) + offset) & 0xFFFFF})
    return result

def in_port(port: int) -> int:
    """Lê porta de E/S. 70h seleciona índice; 71h lê o registrador CMOS."""
    port = int(port) & 0xFFFF
    if port == 0x70:
        return _cmos_index & 0x7F
    if port == 0x71:
        return _cmos.get(_cmos_index & 0x7F, 0x00)
    return 0xFF

def out_port(port: int, value: int):
    global _cmos_index
    port, value = int(port) & 0xFFFF, int(value) & 0xFF
    if port == 0x70:
        _cmos_index = value & 0x7F
    elif port == 0x71:
        _cmos[_cmos_index & 0x7F] = value

def read_cmos_register(index: int) -> int:
    out_port(0x70, index)
    return in_port(0x71)

def handle_interrupt(int_number: int, ah_value: int, payload: str = "") -> dict:
    result = {"status": "SUCCESS", "message": ""}
    if int_number == 0x10:
        result["message"] = (f"[INT 10h, AH=0E] Vídeo: Caractere '{payload}' enviado à tela."
                              if ah_value == 0x0E else f"[INT 10h] Rotina de vídeo executada (AH={ah_value:#x}).")
    elif int_number == 0x13:
        result["message"] = ("[INT 13h, AH=02] Setor 0x7C00 lido com sucesso."
                              if ah_value == 0x02 else "[INT 13h] Serviço de disco executado.")
    elif int_number == 0x16:
        result["message"] = "[INT 16h] Interrupção de teclado acionada."
    else:
        result.update(status="ERROR", message=f"Interrupção INT {int(int_number):02X}h não implementada.")
    return result

def get_bootloader_hash(file_path="boot.bin") -> str:
    full_path = os.path.join(BASE_DIR, file_path)
    if not os.path.isfile(full_path):
        return ""
    with open(full_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_secure_boot(file_path="boot.bin"):
    config = load_config()
    if not config.get("secure_boot", True):
        return True, "Secure Boot [DESATIVADO]. Boot permitido."
    current_hash = get_bootloader_hash(file_path)
    if not current_hash:
        return False, "Erro de Boot: Imagem 'boot.bin' não encontrada."
    authorized = config.get("secure_boot_hash", "")
    if not authorized:
        config["secure_boot_hash"] = current_hash
        save_config(config)
        return True, f"Assinatura gravada na NVRAM ({current_hash[:10]}...). Secure Boot OK."
    if current_hash == authorized:
        return True, f"Assinatura SHA-256 autorizada ({current_hash[:10]}...). Boot UEFI OK."
    return False, f"VIOLAÇÃO DE SECURE BOOT! Assinatura ({current_hash[:10]}...) não coincide!"

def inspect_mbr(file_path="boot.bin", invalid_signature_fault=None):
    """Analisa imagem de setor. Retorna tamanho, assinatura, partições e disassembly."""
    full_path = os.path.join(BASE_DIR, file_path)
    if not os.path.isfile(full_path):
        return {"exists": False, "valid_size": False, "signature": None,
                "signature_valid": False, "partitions": [], "disassembly": [],
                "error": "Arquivo boot.bin não encontrado."}
    with open(full_path, "rb") as f:
        data = f.read(513)
    if invalid_signature_fault is None:
        invalid_signature_fault = load_config().get("fault_injection", {}).get("invalid_mbr_signature", False)
    size_ok = len(data) == 512
    signature = data[510:512] if len(data) >= 512 else b""
    signature_ok = size_ok and signature == b"\x55\xAA" and not invalid_signature_fault
    partitions = []
    if len(data) >= 510:
        for i in range(4):
            p = 446 + i * 16
            entry = data[p:p + 16]
            boot_flag = entry[0]
            partitions.append({"index": i + 1, "bootable": boot_flag == 0x80,
                "boot_flag": boot_flag, "type": entry[4],
                "start_lba": int.from_bytes(entry[8:12], "little"),
                "sectors": int.from_bytes(entry[12:16], "little")})
    disassembly = []
    # Desmontagem didática de um subconjunto pequeno de opcodes x86.
    names = {0x90: (1, "NOP"), 0xFA: (1, "CLI"), 0xFB: (1, "STI"),
             0xF4: (1, "HLT"), 0xC3: (1, "RET"), 0xCD: (2, "INT"),
             0xEB: (2, "JMP short"), 0xE9: (3, "JMP near"),
             0xB8: (3, "MOV AX, imm16"), 0xB4: (2, "MOV AH, imm8"),
             0xB0: (2, "MOV AL, imm8"), 0x31: (2, "XOR r/m16, r16"),
             0x8E: (2, "MOV segment, r/m16"), 0xA0: (3, "MOV AL, [moffs8]")}
    pos, limit = 0, min(64, len(data))
    while pos < limit:
        op = data[pos]
        if op not in names:
            disassembly.append({"offset": pos, "bytes": f"{op:02X}", "instruction": f"DB 0x{op:02X}"})
            pos += 1
            continue
        length, mnemonic = names[op]
        raw = data[pos:pos + length]
        if len(raw) < length:
            disassembly.append({"offset": pos, "bytes": raw.hex(" ").upper(), "instruction": "<instrução truncada>"})
            break
        if op == 0xCD:
            text = f"INT {raw[1]:02X}h"
        elif op == 0xEB:
            dest = (pos + 2 + int.from_bytes(raw[1:2], "little", signed=True)) & 0xFFFF
            text = f"JMP 0x{dest:04X}"
        elif op == 0xE9:
            dest = (pos + 3 + int.from_bytes(raw[1:3], "little", signed=True)) & 0xFFFF
            text = f"JMP 0x{dest:04X}"
        elif op == 0xB8:
            text = f"MOV AX, 0x{int.from_bytes(raw[1:3], 'little'):04X}"
        elif op in (0xB4, 0xB0):
            text = f"{mnemonic.split(',')[0]}, 0x{raw[1]:02X}"
        else:
            text = mnemonic
        disassembly.append({"offset": pos, "bytes": raw.hex(" ").upper(), "instruction": text})
        pos += length
    return {"exists": True, "size": len(data), "valid_size": size_ok,
            "signature": signature.hex(" ").upper() if signature else "ausente",
            "signature_valid": signature_ok, "partitions": partitions,
            "disassembly": disassembly,
            "error": "" if size_ok else f"Setor deve possuir exatamente 512 bytes (lidos: {len(data)})."}

def validate_config(config):
    errors = []
    order = config.get("boot_order")
    if not isinstance(order, list) or not order:
        errors.append("boot_order precisa ser uma lista não vazia.")
    else:
        errors.extend(f"Dispositivo de boot desconhecido: {d!r}." for d in order if d not in VALID_BOOT_DEVICES)
    if config.get("boot_mode", "UEFI") not in VALID_BOOT_MODES:
        errors.append("Modo de boot inválido.")
    memory = config.get("memory_kb", 64)
    if not isinstance(memory, int) or not 1 <= memory <= MAX_MEMORY_KB:
        errors.append(f"memory_kb precisa ser um inteiro entre 1 e {MAX_MEMORY_KB}.")
    return errors

def load_config():
    config = DEFAULT_CONFIG.copy()
    config["fault_injection"] = DEFAULT_CONFIG["fault_injection"].copy()
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                stored = json.load(f)
            if isinstance(stored, dict):
                config.update(stored)
                faults = DEFAULT_CONFIG["fault_injection"].copy()
                faults.update(stored.get("fault_injection", {}))
                config["fault_injection"] = faults
        except (json.JSONDecodeError, OSError):
            pass
    # Erro de checksum simula CMOS corrompida: descarta parâmetros e usa defaults.
    if config.get("fault_injection", {}).get("cmos_checksum_error"):
        faults = config["fault_injection"].copy()
        config = DEFAULT_CONFIG.copy()
        config["fault_injection"] = faults
    if validate_config(config):
        config = DEFAULT_CONFIG.copy()
        config["fault_injection"] = DEFAULT_CONFIG["fault_injection"].copy()
    return config

def save_config(config):
    merged = DEFAULT_CONFIG.copy()
    merged.update(config)
    merged["fault_injection"] = DEFAULT_CONFIG["fault_injection"].copy()
    merged["fault_injection"].update(config.get("fault_injection", {}))
    errors = validate_config(merged)
    if errors:
        raise ValueError("Configuração inválida: " + "; ".join(errors))
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

def load_hardware_map():
    if os.path.isfile(HARDWARE_FILE):
        try:
            with open(HARDWARE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    save_hardware_map(DEFAULT_HARDWARE)
    return DEFAULT_HARDWARE.copy()

def save_hardware_map(hw_data):
    with open(HARDWARE_FILE, "w", encoding="utf-8") as f:
        json.dump(hw_data, f, indent=2, ensure_ascii=False)

# IVT pronta desde a importação, para o visualizador funcionar antes do POST.
_setup_ivt()
