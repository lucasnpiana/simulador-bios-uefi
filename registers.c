/*
 * registers.c
 * Núcleo de baixo nível do simulador de BIOS.
 *
 * Representa a CPU (registradores de 16 bits, como em modo real x86) e a
 * memória endereçável de 1 MB (0x00000-0xFFFFF), simulando rotinas que uma
 * BIOS real executa logo após o reset da máquina.
 *
 * Compilado como biblioteca compartilhada e chamado pelo Python via ctypes
 * (ver bios_core.py).
 */

#include <string.h>
#include "registers.h"

#define MEMORY_SIZE (1024u * 1024u)
#define MAX_MEMORY_KB (MEMORY_SIZE / 1024u)

#define RESET_CS 0xF000u
#define RESET_IP 0xFFF0u

typedef struct {
    uint16_t AX, BX, CX, DX;
    uint16_t SI, DI, BP, SP;
    uint16_t CS, DS, SS, ES;
    uint16_t IP;
} CPU;

static CPU cpu;
static uint8_t memory[MEMORY_SIZE];

uint32_t get_physical_address(void) {
    return ((uint32_t)cpu.CS << 4) + cpu.IP;
}

void reset_cpu(void) {
    memset(&cpu, 0, sizeof(cpu));
    cpu.CS = RESET_CS;
    cpu.IP = RESET_IP;
    cpu.SS = 0x0000;
    cpu.SP = 0x7C00;
}

void get_registers(RegistersSnapshot *out) {
    if (!out) return;
    out->AX = cpu.AX; out->BX = cpu.BX; out->CX = cpu.CX; out->DX = cpu.DX;
    out->SI = cpu.SI; out->DI = cpu.DI; out->BP = cpu.BP; out->SP = cpu.SP;
    out->CS = cpu.CS; out->DS = cpu.DS; out->SS = cpu.SS; out->ES = cpu.ES;
    out->IP = cpu.IP;
    out->physical_address = get_physical_address();
}

int set_register(const char *name, uint16_t value) {
    if (!name) return 0;
    if (strcmp(name, "AX") == 0) { cpu.AX = value; return 1; }
    if (strcmp(name, "BX") == 0) { cpu.BX = value; return 1; }
    if (strcmp(name, "CX") == 0) { cpu.CX = value; return 1; }
    if (strcmp(name, "DX") == 0) { cpu.DX = value; return 1; }
    if (strcmp(name, "SI") == 0) { cpu.SI = value; return 1; }
    if (strcmp(name, "DI") == 0) { cpu.DI = value; return 1; }
    if (strcmp(name, "BP") == 0) { cpu.BP = value; return 1; }
    if (strcmp(name, "SP") == 0) { cpu.SP = value; return 1; }
    if (strcmp(name, "CS") == 0) { cpu.CS = value; return 1; }
    if (strcmp(name, "DS") == 0) { cpu.DS = value; return 1; }
    if (strcmp(name, "SS") == 0) { cpu.SS = value; return 1; }
    if (strcmp(name, "ES") == 0) { cpu.ES = value; return 1; }
    if (strcmp(name, "IP") == 0) { cpu.IP = value; return 1; }
    return 0;
}

int get_register(const char *name, uint16_t *out_value) {
    if (!name || !out_value) return 0;
    if (strcmp(name, "AX") == 0) { *out_value = cpu.AX; return 1; }
    if (strcmp(name, "BX") == 0) { *out_value = cpu.BX; return 1; }
    if (strcmp(name, "CX") == 0) { *out_value = cpu.CX; return 1; }
    if (strcmp(name, "DX") == 0) { *out_value = cpu.DX; return 1; }
    if (strcmp(name, "SI") == 0) { *out_value = cpu.SI; return 1; }
    if (strcmp(name, "DI") == 0) { *out_value = cpu.DI; return 1; }
    if (strcmp(name, "BP") == 0) { *out_value = cpu.BP; return 1; }
    if (strcmp(name, "SP") == 0) { *out_value = cpu.SP; return 1; }
    if (strcmp(name, "CS") == 0) { *out_value = cpu.CS; return 1; }
    if (strcmp(name, "DS") == 0) { *out_value = cpu.DS; return 1; }
    if (strcmp(name, "SS") == 0) { *out_value = cpu.SS; return 1; }
    if (strcmp(name, "ES") == 0) { *out_value = cpu.ES; return 1; }
    if (strcmp(name, "IP") == 0) { *out_value = cpu.IP; return 1; }
    return 0;
}

int post_check_memory(int size_kb, int simulate_failure) {
    if (size_kb < 0) return 0;
    if ((uint32_t)size_kb > MAX_MEMORY_KB) {
        size_kb = (int)MAX_MEMORY_KB;
    }

    uint32_t total_bytes = (uint32_t)size_kb * 1024u;

    for (uint32_t addr = 0; addr < total_bytes; addr++) {
        memory[addr] = (uint8_t)(addr & 0xFF);
    }

    if (simulate_failure && total_bytes > 0) {
        memory[total_bytes / 2] ^= 0xFF;
    }

    for (uint32_t addr = 0; addr < total_bytes; addr++) {
        if (memory[addr] != (uint8_t)(addr & 0xFF)) {
            return 0;
        }
    }
    return 1;
}

uint8_t peek_memory(uint32_t address) {
    if (address >= MEMORY_SIZE) return 0;
    return memory[address];
}

int poke_memory(uint32_t address, uint8_t value) {
    if (address >= MEMORY_SIZE) return 0;
    memory[address] = value;
    return 1;
}