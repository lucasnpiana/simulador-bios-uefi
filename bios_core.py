"""
bios_core.py
Núcleo compartilhado do simulador de BIOS: ponte com o módulo C (ctypes)
e gerenciamento da configuração simulada de CMOS/NVRAM.

Tanto a interface de terminal (main.py) quanto a interface gráfica
(bios_gui.py) importam este módulo, em vez de duplicar a lógica de
carregar a biblioteca e ler/escrever configuração — assim as duas
interfaces sempre falam com o mesmo núcleo, da mesma forma.
"""

import ctypes
import json
import os
import platform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "cmos_config.json")

VALID_BOOT_DEVICES = ("HDD", "USB", "NETWORK", "FLOPPY")
MAX_MEMORY_KB = 1024  # limite real do módulo C (1 MB simulado)

DEFAULT_CONFIG = {
    "boot_order": ["HDD", "USB", "NETWORK"],
    "memory_kb": 64,
    "date": "2026-08-04",
}


# --- Carregamento da biblioteca C, multiplataforma -------------------------

def _library_filename():
    system = platform.system()
    if system == "Windows":
        return "registers.dll"
    if system == "Darwin":
        return "registers.dylib"
    return "registers.so"


class RegistersSnapshot(ctypes.Structure):
    """Precisa bater EXATAMENTE com a struct RegistersSnapshot em registers.h
    (mesma ordem e mesmos tipos de campo)."""
    _fields_ = [
        ("AX", ctypes.c_uint16), ("BX", ctypes.c_uint16),
        ("CX", ctypes.c_uint16), ("DX", ctypes.c_uint16),
        ("SI", ctypes.c_uint16), ("DI", ctypes.c_uint16),
        ("BP", ctypes.c_uint16), ("SP", ctypes.c_uint16),
        ("CS", ctypes.c_uint16), ("DS", ctypes.c_uint16),
        ("SS", ctypes.c_uint16), ("ES", ctypes.c_uint16),
        ("IP", ctypes.c_uint16),
        ("physical_address", ctypes.c_uint32),
    ]


class BiosCoreError(RuntimeError):
    """Erro ao carregar ou usar o módulo de baixo nível em C."""


def _load_library():
    lib_path = os.path.join(BASE_DIR, _library_filename())
    if not os.path.exists(lib_path):
        raise BiosCoreError(
            f"Biblioteca '{_library_filename()}' não encontrada em {BASE_DIR}.\n"
            "Rode 'make' (ou 'make all') antes de executar o simulador, "
            "para compilar registers.c."
        )
    lib = ctypes.CDLL(lib_path)

    lib.reset_cpu.argtypes = []
    lib.reset_cpu.restype = None

    lib.get_registers.argtypes = [ctypes.POINTER(RegistersSnapshot)]
    lib.get_registers.restype = None

    lib.get_physical_address.argtypes = []
    lib.get_physical_address.restype = ctypes.c_uint32

    lib.set_register.argtypes = [ctypes.c_char_p, ctypes.c_uint16]
    lib.set_register.restype = ctypes.c_int

    lib.get_register.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint16)]
    lib.get_register.restype = ctypes.c_int

    lib.post_check_memory.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.post_check_memory.restype = ctypes.c_int

    lib.peek_memory.argtypes = [ctypes.c_uint32]
    lib.peek_memory.restype = ctypes.c_uint8

    lib.poke_memory.argtypes = [ctypes.c_uint32, ctypes.c_uint8]
    lib.poke_memory.restype = ctypes.c_int

    return lib


_lib = _load_library()


# --- API de alto nível pra CPU/memória --------------------------------------

def reset_cpu():
    _lib.reset_cpu()


def get_registers() -> dict:
    """Retorna todos os registradores e o endereço físico atual numa
    única chamada ao C, em vez de uma chamada por registrador."""
    snap = RegistersSnapshot()
    _lib.get_registers(ctypes.byref(snap))
    return {field: getattr(snap, field) for field, _ in snap._fields_}


def set_register(name: str, value: int) -> bool:
    ok = _lib.set_register(name.encode("ascii"), ctypes.c_uint16(value & 0xFFFF))
    return bool(ok)


def get_register(name: str) -> int | None:
    value = ctypes.c_uint16()
    ok = _lib.get_register(name.encode("ascii"), ctypes.byref(value))
    return value.value if ok else None


def post_check_memory(size_kb: int, simulate_failure: bool = False) -> bool:
    return bool(_lib.post_check_memory(int(size_kb), int(simulate_failure)))


def peek_memory(address: int) -> int:
    return _lib.peek_memory(ctypes.c_uint32(address))


def poke_memory(address: int, value: int) -> bool:
    return bool(_lib.poke_memory(ctypes.c_uint32(address), ctypes.c_uint8(value)))


# --- Configuração (simulação de CMOS/NVRAM) ---------------------------------

def validate_config(config: dict) -> list[str]:
    """Retorna uma lista de erros de validação (vazia se estiver tudo ok).
    Centralizar isso aqui evita que a GUI e o terminal aceitem
    configurações inconsistentes de formas diferentes."""
    errors = []

    boot_order = config.get("boot_order")
    if not isinstance(boot_order, list) or not boot_order:
        errors.append("boot_order precisa ser uma lista não vazia.")
    else:
        for device in boot_order:
            if device not in VALID_BOOT_DEVICES:
                errors.append(f"Dispositivo de boot desconhecido: {device!r}.")

    memory_kb = config.get("memory_kb")
    if not isinstance(memory_kb, int) or not (1 <= memory_kb <= MAX_MEMORY_KB):
        errors.append(f"memory_kb precisa ser um inteiro entre 1 e {MAX_MEMORY_KB}.")

    return errors


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            return DEFAULT_CONFIG.copy()

        if not validate_config(config):
            return config
        # config salva estava corrompida/inválida -> volta ao padrão
        return DEFAULT_CONFIG.copy()

    return DEFAULT_CONFIG.copy()



def save_config(config: dict) -> None:
    errors = validate_config(config)
    if errors:
        raise ValueError("Configuração inválida: " + "; ".join(errors))
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)