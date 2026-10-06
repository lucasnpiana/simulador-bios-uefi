; boot.asm
; Bootloader mínimo real, roda em modo real 16-bit (o mesmo modo em que
; uma BIOS de verdade executa logo após o POST).
; Compilar com NASM e rodar num emulador (QEMU) como demonstração
; do que acontece "por baixo" do simulador em Python/C.

[org 0x7c00]          ; BIOS carrega o setor de boot sempre neste endereço

mov si, msg
call print_string

jmp $                 ; trava a execução aqui (loop infinito)

print_string:
    lodsb              ; carrega o próximo caractere de [SI] em AL
    or al, al
    jz done
    mov ah, 0x0e        ; função da BIOS: escrever caractere na tela (int 10h)
    int 0x10
    jmp print_string
done:
    ret

msg db 'Boot simulado carregado! (bootloader real via NASM/QEMU)', 0

times 510-($-$$) db 0  ; preenche o setor até 510 bytes
dw 0xaa55               ; assinatura de boot: é isso que faz a BIOS
                         ; reconhecer este setor como bootável
