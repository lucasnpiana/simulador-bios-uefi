# Makefile do simulador de BIOS

CC = gcc
CFLAGS = -shared -fPIC -O2 -Wall -Wextra

all: registers.so

registers.so: registers.c registers.h
	$(CC) $(CFLAGS) -o registers.so registers.c

boot.bin: boot.asm
	nasm -f bin boot.asm -o boot.bin

run: registers.so
	python3 main.py

run-gui: registers.so
	python3 bios_gui.py

run-boot: boot.bin
	qemu-system-x86_64 -fda boot.bin

clean:
	rm -f registers.so registers.dll registers.dylib boot.bin cmos_config.json

.PHONY: all run run-gui run-boot clean