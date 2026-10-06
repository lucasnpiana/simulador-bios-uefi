#ifndef REGISTERS_H
#define REGISTERS_H

#include <stdint.h>

/*
 * Struct exposta ao Python via ctypes (Structure).
 * IMPORTANTE: a ordem e o tipo dos campos aqui precisa bater exatamente
 * com a classe RegistersSnapshot definida em bios_core.py.
 */
typedef struct {
    uint16_t AX, BX, CX, DX;
    uint16_t SI, DI, BP, SP;
    uint16_t CS, DS, SS, ES;
    uint16_t IP;
    uint32_t physical_address; /* endereço físico real = (CS << 4) + IP */
} RegistersSnapshot;

void reset_cpu(void);
void get_registers(RegistersSnapshot *out);
uint32_t get_physical_address(void);

int set_register(const char *name, uint16_t value);
int get_register(const char *name, uint16_t *out_value);

int post_check_memory(int size_kb, int simulate_failure);

uint8_t peek_memory(uint32_t address);
int poke_memory(uint32_t address, uint8_t value);

#endif