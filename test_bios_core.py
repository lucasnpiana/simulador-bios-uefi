"""
test_bios_core.py
Testes automatizados do núcleo do simulador de BIOS.

Rodar com:
    pytest test_bios_core.py -v

Requer que registers.so já esteja compilado (rode 'make' antes).
"""

import os
import pytest

import bios_core


# --- fixtures ---------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_before_each_test():
    """Garante que cada teste começa com a CPU zerada, sem depender
    da ordem em que os testes rodam."""
    bios_core.reset_cpu()
    yield


@pytest.fixture
def temp_config_file(tmp_path, monkeypatch):
    """Redireciona o CONFIG_FILE pra um arquivo temporário, pra os testes
    não sobrescreverem o cmos_config.json real do projeto."""
    fake_path = tmp_path / "cmos_config_test.json"
    monkeypatch.setattr(bios_core, "CONFIG_FILE", str(fake_path))
    return fake_path


# --- testes de reset e registradores ----------------------------------------

def test_reset_cpu_define_reset_vector_correto():
    """Depois do reset, CS:IP precisa apontar pro reset vector real do x86."""
    bios_core.reset_cpu()
    regs = bios_core.get_registers()

    assert regs["CS"] == 0xF000
    assert regs["IP"] == 0xFFF0
    assert regs["physical_address"] == 0xFFFF0


def test_reset_cpu_zera_registradores_de_dados():
    bios_core.set_register("AX", 0x1234)
    bios_core.reset_cpu()
    regs = bios_core.get_registers()

    assert regs["AX"] == 0
    assert regs["BX"] == 0
    assert regs["CX"] == 0
    assert regs["DX"] == 0


def test_set_e_get_register_roundtrip():
    """O valor escrito precisa ser exatamente o valor lido de volta."""
    assert bios_core.set_register("AX", 0xABCD) is True
    assert bios_core.get_register("AX") == 0xABCD


def test_set_register_nome_invalido_retorna_false():
    assert bios_core.set_register("ZZ", 123) is False


def test_get_register_nome_invalido_retorna_none():
    assert bios_core.get_register("ZZ") is None


def test_get_registers_retorna_todos_os_campos():
    regs = bios_core.get_registers()
    campos_esperados = {
        "AX", "BX", "CX", "DX", "SI", "DI", "BP", "SP",
        "CS", "DS", "SS", "ES", "IP", "physical_address",
    }
    assert campos_esperados.issubset(regs.keys())


# --- testes de memória --------------------------------------------------

def test_post_check_memory_sem_falha_retorna_true():
    assert bios_core.post_check_memory(64, simulate_failure=False) is True


def test_post_check_memory_com_falha_simulada_retorna_false():
    assert bios_core.post_check_memory(64, simulate_failure=True) is False


def test_post_check_memory_respeita_limite_maximo():
    """Pedir mais memória do que o limite não deve travar nem estourar
    o buffer, só deve saturar no máximo permitido."""
    resultado = bios_core.post_check_memory(999999, simulate_failure=False)
    assert resultado is True  # deve rodar normalmente, sem crash


def test_peek_poke_memory_roundtrip():
    endereco = 0x1000
    bios_core.poke_memory(endereco, 0x42)
    assert bios_core.peek_memory(endereco) == 0x42


def test_peek_memory_endereco_fora_do_limite_nao_estoura():
    """Endereço além de 1 MB precisa retornar 0 com segurança,
    não travar o programa."""
    assert bios_core.peek_memory(0xFFFFFFFF) == 0


# --- testes de validação de configuração --------------------------------

def test_validate_config_aceita_configuracao_valida():
    config = {"boot_order": ["HDD", "USB"], "memory_kb": 64, "date": "2026-08-06"}
    assert bios_core.validate_config(config) == []


def test_validate_config_rejeita_dispositivo_desconhecido():
    config = {"boot_order": ["HDD", "DISQUETE_MAGICO"], "memory_kb": 64, "date": "2026-08-06"}
    erros = bios_core.validate_config(config)
    assert len(erros) == 1
    assert "DISQUETE_MAGICO" in erros[0]


def test_validate_config_rejeita_boot_order_vazia():
    config = {"boot_order": [], "memory_kb": 64, "date": "2026-08-06"}
    erros = bios_core.validate_config(config)
    assert len(erros) == 1


def test_validate_config_rejeita_memoria_acima_do_limite():
    config = {"boot_order": ["HDD"], "memory_kb": 99999, "date": "2026-08-06"}
    erros = bios_core.validate_config(config)
    assert any("memory_kb" in e for e in erros)


def test_validate_config_rejeita_memoria_negativa_ou_zero():
    config = {"boot_order": ["HDD"], "memory_kb": 0, "date": "2026-08-06"}
    erros = bios_core.validate_config(config)
    assert any("memory_kb" in e for e in erros)


# --- testes de load/save config (usando arquivo temporário) -------------

def test_save_config_grava_e_load_config_le_de_volta(temp_config_file):
    config = {"boot_order": ["USB", "HDD"], "memory_kb": 128, "date": "2026-01-01"}
    bios_core.save_config(config)

    assert os.path.exists(temp_config_file)
    config_lida = bios_core.load_config()
    assert config_lida == config


def test_save_config_rejeita_config_invalida(temp_config_file):
    config_invalida = {"boot_order": [], "memory_kb": 64, "date": "2026-01-01"}
    with pytest.raises(ValueError):
        bios_core.save_config(config_invalida)


def test_load_config_sem_arquivo_retorna_padrao(temp_config_file):
    """Se o arquivo de config não existe ainda, precisa cair no padrão
    em vez de quebrar."""
    config = bios_core.load_config()
    assert config == bios_core.DEFAULT_CONFIG


def test_load_config_com_arquivo_corrompido_retorna_padrao(temp_config_file):
    """Se o JSON salvo estiver corrompido, o programa não pode travar —
    precisa recuperar com a configuração padrão."""
    with open(temp_config_file, "w", encoding="utf-8") as f:
        f.write("{ isso nao é json valido")

    config = bios_core.load_config()
    assert config == bios_core.DEFAULT_CONFIG