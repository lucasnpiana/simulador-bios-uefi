"""Interface CustomTkinter do simulador acadêmico BIOS/UEFI."""
import os
import threading
import time
import shutil
import subprocess
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk
import bios_core

ctk.set_appearance_mode("dark")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOT_DEVICE_LABELS = {"HDD": "HDD (Disco Rígido)", "USB": "USB (Pendrive)",
                      "FLOPPY": "Floppy (Disquete)", "NETWORK": "Rede (PXE)"}
LABEL_TO_DEVICE = {v: k for k, v in BOOT_DEVICE_LABELS.items()}
BG, RED, DARK_RED, WHITE, YELLOW = "#0A0A0A", "#CC0000", "#880000", "#FFFFFF", "#FFFF00"
GREEN, ERROR, MONO, FONT = "#55FF55", "#FF5555", "Courier New", "Arial"

# ---------------------------------------------------------------------------
# Conteúdo da aba "Documentação": (título, origem, parágrafos).
# Linhas iniciadas por "• " são exibidas como itens recuados.
# ---------------------------------------------------------------------------
DOC_PY = "Origem: simulação 100% Python"
DOC_QEMU = "Origem: QEMU (opcional) + simulação Python"

DOC_SECTIONS = [
    ("0. Visão geral: o que é simulado e o que depende do QEMU", DOC_PY, [
        "Todo o simulador funciona sem software externo. A RAM, os registradores, a CMOS, "
        "a IVT, o POST, o Secure Boot, a análise do MBR e o monitor de hardware são "
        "estruturas e funções Python (arquivo bios_core.py). Nenhuma instrução x86 é "
        "realmente executada por esta aplicação.",
        "Somente o botão [ BOOT EXECUTE ] pode usar o QEMU, e apenas se o executável "
        "qemu-system-x86_64 ou qemu-system-i386 estiver no PATH e existir um boot.bin. "
        "Nesse caso o QEMU abre uma janela separada e executa o setor de boot de verdade "
        "em uma CPU emulada. Sem o QEMU, o simulador apenas registra no log que o "
        "bootloader foi validado e entregue em 0x7C00.",
        "• Python: CMOS, fault injection, POST, memória, IVT, INT 10h/13h/16h, registradores, "
        "Secure Boot (SHA-256), inspeção e desmontagem do MBR, hardware monitor.",
        "• QEMU: execução real do código contido em boot.bin (opcional).",
    ]),
    ("1. CMOS / NVRAM", DOC_PY, [
        "Na placa-mãe real, a CMOS/NVRAM é uma pequena memória alimentada por bateria que "
        "guarda as configurações do Setup mesmo com o PC desligado. Aqui ela é o arquivo "
        "cmos_config.json, lido e gravado por load_config() e save_config().",
        "• 1st Boot Device: dispositivo preferencial (HDD, USB, Floppy ou Rede/PXE). É "
        "gravado e validado, mas o POST deste simulador sempre usa o arquivo boot.bin.",
        "• Boot Mode: UEFI (com verificação de Secure Boot) ou LEGACY (apenas valida a "
        "assinatura 55 AA do MBR).",
        "• Secure Boot: quando ativo no modo UEFI, calcula o SHA-256 do boot.bin. Na primeira "
        "execução a assinatura é gravada na CMOS (secure_boot_hash); nas seguintes, qualquer "
        "alteração do arquivo bloqueia o boot.",
        "• Simulate RAM Failure: vale só para a sessão atual e não é gravado no arquivo.",
        "Os valores são validados antes de salvar (dispositivo, modo e tamanho de memória). "
        "Configuração inválida é recusada e o erro aparece na linha de status.",
    ]),
    ("2. POST Fault Injection", DOC_PY, [
        "Injeção de falhas serve para mostrar como o firmware reage a erros de hardware. "
        "Marque a falha, clique em SAVE CMOS SETUP e depois em POWER ON.",
        "• CMOS Checksum Error: simula bateria fraca ou CMOS corrompida. As configurações "
        "são descartadas e os padrões de fábrica são carregados. O POST segue em frente.",
        "• Invalid MBR Signature: faz o simulador ignorar a assinatura 55 AA. Resultado: "
        "\"No Bootable Device Found\" e o boot é interrompido na etapa SecureBoot Check.",
        "• Keyboard Missing: o POST para com \"Keyboard Error - No Keyboard Present\", como "
        "em BIOSes clássicas, na etapa POST.",
        "• Simulate RAM Failure (opção da aba, fora do quadro de falhas): o teste de memória "
        "falha e o sistema fica \"Halted\".",
    ]),
    ("3. Power On / Boot Execute e terminal de logs", DOC_QEMU, [
        "POWER ON (POST) executa em uma thread separada, para a interface não travar, e "
        "percorre a sequência abaixo. Cada passo aparece no terminal e avança a barra de "
        "progresso e a Boot Timeline.",
        "• 1. Reset: CPU volta a CS:IP = F000:FFF0 (endereço físico 0xFFFF0).",
        "• 2. POST: lê o relógio RTC da CMOS pelas portas 70h (índice) e 71h (dado), "
        "verifica teclado e executa o teste de memória.",
        "• 3. IVT Setup: registra os 256 vetores de interrupção na RAM baixa.",
        "• 4. Secure Boot: só no modo UEFI. No modo LEGACY apenas valida o MBR.",
        "• 5. Handover: CS:IP passa para 0000:7C00 e o botão BOOT EXECUTE é habilitado.",
        "BOOT EXECUTE registra a leitura do setor (INT 13h, AH=02) e então: se o QEMU "
        "estiver instalado, abre o boot.bin em uma janela de máquina virtual real; "
        "se não estiver, conclui com \"SIMULADOR NATIVO\", sem executar o código.",
        "Observação: o simulador não copia o conteúdo do boot.bin para a RAM em 0x7C00; "
        "esse endereço é simbólico (aparece nos registradores e nos logs).",
    ]),
    ("4. Memory Viewer", DOC_PY, [
        "Mostra a RAM simulada: um bytearray de 1 MB (espaço de endereçamento do modo real "
        "x86, 20 bits). O formato é endereço | bytes em hexadecimal | ASCII.",
        "• Campo Start: endereço inicial em hexadecimal (ex.: 00040).",
        "• Campo Bytes: quantidade, também em HEXADECIMAL. O padrão \"400\" equivale a "
        "0x400 = 1024 bytes.",
        "• Quase toda a memória é zero. A única região preenchida é 0x00000-0x003FF (IVT), "
        "criada no reset da CPU. Por isso o dump só mostra dados após clicar em POWER ON.",
    ]),
    ("5. IVT (Interrupt Vector Table)", DOC_PY, [
        "Em modo real, os primeiros 1024 bytes da RAM guardam 256 vetores de 4 bytes. Cada "
        "vetor é OFFSET (2 bytes) seguido de SEGMENTO (2 bytes), ambos em little-endian. "
        "Endereço físico do tratador = segmento × 16 + offset. O vetor da interrupção N "
        "fica no endereço N × 4.",
        "• INT 10h (vídeo): AH=0Eh escreve um caractere na tela (teletype). Vetor em F000:0100.",
        "• INT 13h (disco): AH=02h lê setores. É o serviço usado para carregar o boot "
        "sector em 0x7C00. Vetor em F000:0200.",
        "• INT 16h (teclado): leitura de teclas. Vetor em F000:0300.",
        "• Demais vetores apontam para um stub único (F000:00F0).",
        "Neste simulador, handle_interrupt() apenas devolve uma mensagem de texto "
        "descrevendo o serviço; não há código x86 de BIOS sendo executado.",
    ]),
    ("6. MBR Inspector", DOC_PY, [
        "O MBR (Master Boot Record) é o setor 0 do disco, com exatamente 512 bytes:",
        "• Bytes 0-445: código do bootloader.",
        "• Bytes 446-509: tabela de partições (4 entradas de 16 bytes). Cada entrada tem a "
        "flag de boot (0x80 = ativa), o tipo, o LBA inicial e o número de setores.",
        "• Bytes 510-511: assinatura 0x55 0xAA. Sem ela a BIOS considera o disco não "
        "inicializável.",
        "Analyze boot.bin relê e mostra o arquivo. Select boot.bin copia outro arquivo .bin "
        "para a pasta do programa com o nome boot.bin. A desmontagem exibida cobre os "
        "primeiros 64 bytes e reconhece só alguns opcodes (NOP, CLI, STI, HLT, RET, INT, "
        "JMP, MOV). Os demais aparecem como DB 0xNN.",
    ]),
    ("7. Boot Timeline", DOC_PY, [
        "Painel visual com as cinco etapas da inicialização. A etapa atual fica vermelha, "
        "as concluídas ficam verdes-escuras e as pendentes cinzas.",
        "• 1. Reset Vector 0xFFFF0: primeira instrução executada pela CPU.",
        "• 2. POST: testes de CPU, RAM, teclado e CMOS.",
        "• 3. IVT Setup: construção da tabela de vetores.",
        "• 4. SecureBoot Check: verificação de integridade (UEFI) ou validação do MBR.",
        "• 5. Handover 0x7C00: controle passa ao bootloader.",
        "Se uma falha ocorrer, a timeline congela na etapa onde o erro aconteceu, e o texto "
        "de status abaixo informa o motivo.",
    ]),
    ("8. CPU Registers", DOC_PY, [
        "Painel lateral com os registradores de 16 bits do modo real:",
        "• AX, BX, CX, DX: registradores de uso geral.",
        "• CS: segmento de código. IP: ponteiro da próxima instrução.",
        "• PHY: endereço físico = (CS × 16 + IP) limitado a 20 bits.",
        "Antes do POST aparece 0xFFFF0, o endereço onde a CPU x86 começa a executar ao ligar "
        "(F000:FFF0). Após o handover o valor passa a 0x07C00 (0000:7C00), onde o "
        "bootloader é carregado. AX a DX permanecem em zero porque nenhum código é executado.",
    ]),
    ("9. Hardware Monitor", DOC_PY, [
        "Exibe CPU, temperatura, rotação da ventoinha e tensões de +3,3 V e +12 V. Os "
        "valores vêm do arquivo hardware_map.json (criado com valores-padrão se não existir).",
        "São dados estáticos e fictícios: não leem sensores reais. Edite o JSON e reinicie o "
        "programa para ver outros valores, por exemplo uma temperatura alta.",
    ]),
    ("10. Roteiro de aula: experimentos sugeridos", DOC_PY, [
        "• Experimento 1 (CMOS): troque o 1st Boot Device, salve e abra cmos_config.json. "
        "Discuta persistência e por que a BIOS real usa bateria.",
        "• Experimento 2 (falhas): ative uma falha por vez (teclado, RAM, MBR, checksum), "
        "execute o POST e compare logs e Boot Timeline.",
        "• Experimento 3 (Secure Boot): execute o POST em UEFI para gravar o hash. Altere "
        "um byte do boot.bin e execute de novo: o boot será bloqueado. Mude para LEGACY e "
        "veja que passa. Para reautorizar, apague secure_boot_hash do JSON.",
        "• Experimento 4 (IVT): após o POST, abra o Memory Viewer em 00040 com 10 bytes. "
        "Deve aparecer 00 01 00 F0, ou seja, INT 10h = F000:0100. Repita em 0004C (INT 13h) "
        "e 00058 (INT 16h).",
        "• Experimento 5 (MBR): com um editor hexadecimal, apague os bytes 55 AA do final do "
        "boot.bin e observe o erro no MBR Inspector.",
        "• Experimento 6 (disassembly): crie um boot.bin com FA B8 34 12 F4 e veja CLI, "
        "MOV AX 0x1234 e HLT na desmontagem.",
        "• Experimento 7 (registradores): compare CS:IP e PHY antes do POST, durante o "
        "reset e após o handover. Peça aos alunos para calcular CS×16+IP à mão.",
        "• Experimento 8 (monitor): edite hardware_map.json e discuta o papel dos sensores "
        "no controle térmico.",
        "• Experimento 9 (QEMU): instale o QEMU e compare o BOOT EXECUTE com e sem ele. "
        "Discuta a diferença entre simular a BIOS e emular uma CPU real.",
    ]),
]


class BiosSimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("UEFI BIOS Utility - Advanced Mode | GURI")
        self.geometry("1180x800")
        self.minsize(950, 650)
        self.configure(fg_color=BG)
        self.config_data = bios_core.load_config()
        self.hardware_data = bios_core.load_hardware_map()
        self.timeline_labels = []
        self.doc_labels = []
        self._build_layout()
        self._refresh_registers_display()
        self._refresh_memory_view()
        self._refresh_mbr_view()

    def _build_layout(self):
        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.pack(fill="x", padx=12, pady=(10, 5))
        ctk.CTkLabel(header, text="[GURI]", font=(FONT, 21, "bold"), text_color=RED).pack(side="left", padx=8)
        ctk.CTkLabel(header, text="UEFI BIOS Utility - Advanced Mode", font=(FONT, 17, "bold"), text_color=WHITE).pack(side="left")
        ctk.CTkLabel(header, text=datetime.now().strftime("%d/%m/%Y  %H:%M"), text_color=WHITE).pack(side="right", padx=8)
        body = ctk.CTkFrame(self, fg_color=BG)
        body.pack(fill="both", expand=True, padx=12, pady=5)
        self.tabs = ctk.CTkTabview(body, fg_color="#111111", segmented_button_selected_color=RED,
                                   segmented_button_selected_hover_color=DARK_RED)
        self.tabs.pack(side="left", fill="both", expand=True, padx=(0, 8))
        for name in ("CMOS & POST", "Memory & IVT Viewer", "MBR Inspector", "Boot Timeline", "Documentação"):
            self.tabs.add(name)
        self._build_setup_tab(self.tabs.tab("CMOS & POST"))
        self._build_memory_tab(self.tabs.tab("Memory & IVT Viewer"))
        self._build_mbr_tab(self.tabs.tab("MBR Inspector"))
        self._build_timeline_tab(self.tabs.tab("Boot Timeline"))
        self._build_docs_tab(self.tabs.tab("Documentação"))
        self._build_side_panel(body)
        footer = ctk.CTkFrame(self, fg_color=BG, height=28)
        footer.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(footer, text="GURI BIOS Simulator | Python Native | x86 Real Mode", text_color=WHITE).pack(side="left")
        ctk.CTkLabel(footer, text="v3.0 Academic", text_color=RED).pack(side="right")

    def _section(self, parent, title):
        ctk.CTkLabel(parent, text=f"[ {title} ]", font=(FONT, 14, "bold"), text_color=RED).pack(anchor="w", padx=12, pady=(10, 5))

    def _build_setup_tab(self, parent):
        # Divide a aba em duas colunas: controles na esquerda e terminal no meio
        left_col = ctk.CTkFrame(parent, fg_color="transparent")
        left_col.pack(side="left", fill="y", padx=(4, 10), pady=4)

        right_col = ctk.CTkFrame(parent, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)

        # --- COLUNA DA ESQUERDA (Configurações e Botões) ---
        self._section(left_col, "CMOS / NVRAM SETUP")
        form = ctk.CTkFrame(left_col, fg_color="transparent")
        form.pack(fill="x", padx=15)
        ctk.CTkLabel(form, text="1st Boot Device", text_color=WHITE).grid(row=0, column=0, sticky="w", pady=5)
        self.combo_boot = ctk.CTkComboBox(form, values=list(BOOT_DEVICE_LABELS.values()), width=230)
        self.combo_boot.grid(row=0, column=1, padx=12, pady=5, sticky="w")
        self.combo_boot.set(BOOT_DEVICE_LABELS.get(self.config_data.get("boot_order", ["HDD"])[0], BOOT_DEVICE_LABELS["HDD"]))
        ctk.CTkLabel(form, text="Boot Mode", text_color=WHITE).grid(row=1, column=0, sticky="w", pady=5)
        self.combo_mode = ctk.CTkComboBox(form, values=["UEFI", "LEGACY"], width=230)
        self.combo_mode.grid(row=1, column=1, padx=12, pady=5, sticky="w")
        self.combo_mode.set(self.config_data.get("boot_mode", "UEFI"))

        self.secure_var = ctk.BooleanVar(value=self.config_data.get("secure_boot", True))
        ctk.CTkCheckBox(left_col, text="Enable UEFI Secure Boot", variable=self.secure_var, text_color=WHITE, fg_color=RED).pack(anchor="w", padx=18, pady=5)
        self.ram_fail_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(left_col, text="Simulate RAM Failure (POST)", variable=self.ram_fail_var, text_color=WHITE, fg_color=RED).pack(anchor="w", padx=18, pady=5)

        faults = self.config_data.get("fault_injection", {})
        fault_frame = ctk.CTkFrame(left_col, fg_color="#171717")
        fault_frame.pack(fill="x", padx=12, pady=10)
        self.cmos_fault_var = ctk.BooleanVar(value=faults.get("cmos_checksum_error", False))
        self.mbr_fault_var = ctk.BooleanVar(value=faults.get("invalid_mbr_signature", False))
        self.keyboard_fault_var = ctk.BooleanVar(value=faults.get("keyboard_missing", False))
        self._section(fault_frame, "POST FAULT INJECTION")
        for label, var in (("CMOS Checksum Error (load defaults)", self.cmos_fault_var),
                           ("Invalid MBR Signature (55 AA)", self.mbr_fault_var),
                           ("Keyboard Missing", self.keyboard_fault_var)):
            ctk.CTkCheckBox(fault_frame, text=label, variable=var, text_color=WHITE, fg_color=RED).pack(anchor="w", padx=15, pady=4)

        ctk.CTkButton(left_col, text="[ SAVE CMOS SETUP ]", command=self._save_cmos, fg_color=DARK_RED, hover_color=RED).pack(anchor="w", padx=15, pady=8)
        self.status_label = ctk.CTkLabel(left_col, text="", text_color=GREEN, wraplength=350, justify="left")
        self.status_label.pack(anchor="w", padx=15)

        controls = ctk.CTkFrame(left_col, fg_color="transparent")
        controls.pack(fill="x", padx=12, pady=(12, 4))
        self.power_btn = ctk.CTkButton(
            controls, text="[ POWER ON (POST) ]", command=self._start_post,
            fg_color=RED, hover_color=DARK_RED, height=34
        )
        self.power_btn.pack(side="left", padx=5)
        self.boot_btn = ctk.CTkButton(
            controls, text="[ BOOT EXECUTE ]", command=self._execute_boot,
            state="disabled", fg_color="#444444", height=34
        )
        self.boot_btn.pack(side="left", padx=5)

        self.progress = ctk.CTkProgressBar(left_col, progress_color=YELLOW)
        self.progress.pack(fill="x", padx=12, pady=(6, 6))
        self.progress.set(0)

        # --- COLUNA CENTRAL (Terminal ocupando toda a altura e largura livre) ---
        self._section(right_col, "POST TERMINAL & BIOS LOG")
        self.logs = ctk.CTkTextbox(right_col, font=(MONO, 11), fg_color="#000000", text_color=GREEN)
        self.logs.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        self.logs.insert("end", "System Halted. Press POWER ON to start POST.\n")

    def _build_side_panel(self, parent):
        panel = ctk.CTkFrame(parent, width=210, fg_color=BG, border_width=1, border_color=RED)
        panel.pack(side="right", fill="y")
        self._section(panel, "CPU REGISTERS")
        self.reg_vars = {}
        for reg in ("AX", "BX", "CX", "DX", "CS", "IP"):
            var = ctk.StringVar(value=f"{reg}: 0000")
            self.reg_vars[reg] = var
            ctk.CTkLabel(panel, textvariable=var, font=(MONO, 11), text_color=WHITE).pack(anchor="w", padx=15, pady=2)
        self.phys_label = ctk.CTkLabel(panel, text="PHY: 0xFFFF0", font=(MONO, 11), text_color=YELLOW)
        self.phys_label.pack(anchor="w", padx=15, pady=5)
        self._section(panel, "HARDWARE MONITOR")
        hw, volts = self.hardware_data, self.hardware_data.get("voltages", {})
        for line in (f"CPU: {hw.get('cpu', 'x86 CPU')}", f"Temp: {hw.get('cpu_temp_celsius', 42)} C",
                     f"Fan: {hw.get('fan_rpm', 2200)} RPM", f"+3.3V: {volts.get('v3_3', 3.3)}V",
                     f"+12V: {volts.get('v12_0', 12.0)}V"):
            ctk.CTkLabel(panel, text=line, text_color=WHITE, wraplength=185, justify="left").pack(anchor="w", padx=12, pady=3)

    def _build_memory_tab(self, parent):
        self._section(parent, "PHYSICAL RAM HEX VIEWER")
        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.pack(fill="x", padx=10)
        self.mem_addr = ctk.CTkEntry(controls, width=130, placeholder_text="Start hex (00000)")
        self.mem_addr.pack(side="left", padx=5)
        self.mem_addr.insert(0, "00000")
        self.mem_size = ctk.CTkEntry(controls, width=90, placeholder_text="Bytes")
        self.mem_size.pack(side="left", padx=5)
        self.mem_size.insert(0, "400")
        ctk.CTkButton(controls, text="Refresh Dump", command=self._refresh_memory_view, fg_color=DARK_RED).pack(side="left", padx=5)
        self.mem_text = ctk.CTkTextbox(parent, font=(MONO, 11), wrap="none")
        self.mem_text.pack(fill="both", expand=True, padx=10, pady=8)
        self._section(parent, "IMPORTANT IVT VECTORS")
        self.ivt_text = ctk.CTkTextbox(parent, height=100, font=(MONO, 11))
        self.ivt_text.pack(fill="x", padx=10, pady=(0, 10))

    def _build_mbr_tab(self, parent):
        self._section(parent, "MASTER BOOT RECORD / SECTOR 0")
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=10)
        ctk.CTkButton(top, text="Analyze boot.bin", command=self._refresh_mbr_view, fg_color=DARK_RED).pack(side="left", padx=5)
        ctk.CTkButton(top, text="Select boot.bin", command=self._select_boot_file, fg_color="#444444").pack(side="left", padx=5)
        self.mbr_text = ctk.CTkTextbox(parent, font=(MONO, 11))
        self.mbr_text.pack(fill="both", expand=True, padx=10, pady=10)

    def _build_timeline_tab(self, parent):
        self._section(parent, "CPU BOOT STATE TRANSITIONS")
        self.timeline_frame = ctk.CTkFrame(parent, fg_color="#151515")
        self.timeline_frame.pack(fill="x", padx=15, pady=20)
        steps = ["Reset Vector 0xFFFF0", "POST", "IVT Setup", "SecureBoot Check", "Handover 0x7C00"]
        for i, step in enumerate(steps):
            box = ctk.CTkFrame(self.timeline_frame, fg_color="#333333", corner_radius=6)
            box.pack(fill="x", padx=12, pady=7)
            label = ctk.CTkLabel(box, text=f"{i + 1}.  {step}", font=(FONT, 13, "bold"), text_color="#AAAAAA")
            label.pack(anchor="w", padx=15, pady=10)
            self.timeline_labels.append((box, label))
        self.timeline_status = ctk.CTkLabel(parent, text="Aguardando início do POST.", text_color=YELLOW)
        self.timeline_status.pack(anchor="w", padx=18, pady=8)

    def _build_docs_tab(self, parent):
        """Aba de documentação: explica cada seção e o que é Python x QEMU."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self._section(scroll, "DOCUMENTAÇÃO DO SIMULADOR")
        intro = ctk.CTkLabel(scroll, text="Guia de cada seção da aplicação, indicando o que é "
                             "simulado em Python e o que depende do QEMU.",
                             text_color="#AAAAAA", justify="left", anchor="w", wraplength=600)
        intro.pack(anchor="w", padx=12, pady=(0, 6))
        self.doc_labels.append(intro)
        for title, origin, paragraphs in DOC_SECTIONS:
            card = ctk.CTkFrame(scroll, fg_color="#171717", corner_radius=6)
            card.pack(fill="x", padx=6, pady=6)
            ctk.CTkLabel(card, text=title, font=(FONT, 14, "bold"), text_color=WHITE,
                         anchor="w").pack(anchor="w", padx=12, pady=(10, 0))
            ctk.CTkLabel(card, text=origin, font=(MONO, 11),
                         text_color=YELLOW if "QEMU" in origin else GREEN,
                         anchor="w").pack(anchor="w", padx=12, pady=(0, 4))
            for text in paragraphs:
                label = ctk.CTkLabel(card, text=text, text_color="#DDDDDD", justify="left",
                                     anchor="w", wraplength=600)
                label.pack(anchor="w", padx=(22 if text.startswith("•") else 12, 12), pady=2)
                self.doc_labels.append(label)
            ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

        def rewrap(event):
            width = max(300, event.width - 80)
            for lbl in self.doc_labels:
                lbl.configure(wraplength=width)

        parent.bind("<Configure>", rewrap)

    def _timeline(self, index, status=None):
        def update():
            for i, (box, label) in enumerate(self.timeline_labels):
                color = RED if i == index else ("#244424" if i < index else "#333333")
                box.configure(fg_color=color)
                label.configure(text_color=WHITE if i <= index else "#AAAAAA")
            if status:
                self.timeline_status.configure(text=status)
        self.after(0, update)

    def _log(self, message):
        def append():
            self.logs.insert("end", message + "\n")
            self.logs.see("end")
        self.after(0, append)

    def _save_cmos(self):
        device = LABEL_TO_DEVICE.get(self.combo_boot.get(), "HDD")
        faults = {"cmos_checksum_error": self.cmos_fault_var.get(),
                  "invalid_mbr_signature": self.mbr_fault_var.get(),
                  "keyboard_missing": self.keyboard_fault_var.get()}
        updated = dict(self.config_data)
        updated.update(boot_order=[device] + [d for d in updated.get("boot_order", []) if d != device],
                       boot_mode=self.combo_mode.get(), secure_boot=self.secure_var.get(),
                       fault_injection=faults)
        try:
            bios_core.save_config(updated)
            self.config_data = updated
            if faults["cmos_checksum_error"]:
                self.status_label.configure(text="> CMOS checksum fault armed: defaults will load on next config read.", text_color=YELLOW)
            else:
                self.status_label.configure(text="> CMOS settings saved.", text_color=GREEN)
        except ValueError as exc:
            self.status_label.configure(text=f"> {exc}", text_color=ERROR)

    def _refresh_registers_display(self):
        regs = bios_core.get_registers()
        for reg, var in self.reg_vars.items():
            var.set(f"{reg}: 0x{regs[reg]:04X}")
        self.phys_label.configure(text=f"PHY: 0x{regs['physical_address']:05X}")

    def _refresh_memory_view(self):
        if not hasattr(self, "mem_text"):
            return
        try:
            start = int(self.mem_addr.get().strip(), 16)
            size = int(self.mem_size.get().strip(), 16)
            dump = bios_core.get_memory_hex_dump(start, size)
        except (ValueError, TypeError) as exc:
            dump = f"Erro: {exc}"
        self.mem_text.delete("1.0", "end")
        self.mem_text.insert("end", dump)
        entries = bios_core.get_ivt_entries()
        lines = [f"INT {n:02X}h -> {e['segment']:04X}:{e['offset']:04X}  (phys 0x{e['physical']:05X})"
                 for n in (0x10, 0x13, 0x16) for e in entries if e["interrupt"] == n]
        self.ivt_text.delete("1.0", "end")
        self.ivt_text.insert("end", "\n".join(lines))

    def _refresh_mbr_view(self):
        if not hasattr(self, "mbr_text"):
            return
        result = bios_core.inspect_mbr("boot.bin")
        lines = [f"Arquivo encontrado: {result['exists']}", f"Tamanho lido: {result.get('size', 0)} bytes",
                 f"Setor de 512 bytes: {result['valid_size']}", f"Assinatura final: {result['signature']}",
                 f"Assinatura 0x55AA válida: {result['signature_valid']}"]
        if result.get("error"):
            lines.append("Erro: " + result["error"])
        lines += ["", "TABELA DE PARTIÇÕES (offsets 446-509):"]
        for p in result["partitions"]:
            lines.append(f"Partição {p['index']}: boot=0x{p['boot_flag']:02X} ({'ativa' if p['bootable'] else 'não ativa'}), tipo=0x{p['type']:02X}, início LBA={p['start_lba']}, setores={p['sectors']}")
        lines += ["", "DESMONTAGEM SIMPLIFICADA (primeiros 64 bytes):"]
        lines.extend(f"{d['offset']:04X}: {d['bytes']:<8} {d['instruction']}" for d in result["disassembly"])
        self.mbr_text.delete("1.0", "end")
        self.mbr_text.insert("end", "\n".join(lines))

    def _select_boot_file(self):
        path = filedialog.askopenfilename(initialdir=BASE_DIR, filetypes=[("Boot image", "*.bin"), ("All files", "*.*")])
        if path:
            target = os.path.join(BASE_DIR, "boot.bin")
            try:
                if os.path.abspath(path) != os.path.abspath(target):
                    shutil.copy2(path, target)
                self._refresh_mbr_view()
            except OSError as exc:
                self.status_label.configure(text=f"> Não foi possível copiar: {exc}", text_color=ERROR)

    def _start_post(self):
        self.power_btn.configure(state="disabled")
        self.boot_btn.configure(state="disabled")
        # Captura os controles na thread da GUI; a rotina de POST usa somente o snapshot.
        self.post_faults = {
            "cmos_checksum_error": self.cmos_fault_var.get(),
            "invalid_mbr_signature": self.mbr_fault_var.get(),
            "keyboard_missing": self.keyboard_fault_var.get(),
            "ram_failure": self.ram_fail_var.get(),
        }
        threading.Thread(target=self._post_worker, daemon=True).start()

    def _post_worker(self):
        try:
            self._timeline(0, "CPU iniciada no Reset Vector 0xFFFF0")
            self._log("[GURI] BIOS x86/UEFI - Power On Self Test")
            bios_core.reset_cpu()
            self.after(0, self._refresh_registers_display)
            self._log("Reset Vector: CS:IP = F000:FFF0 (physical 0xFFFF0)")
            time.sleep(.25)
            self._timeline(1, "POST: verificando hardware e CMOS")
            self._log("POST: inicializando CPU, RAM e dispositivos...")
            if self.post_faults["cmos_checksum_error"]:
                self._log("[CMOS] Checksum Error! Parâmetros inválidos; carregando padrões de fábrica.")
                defaults = bios_core.DEFAULT_CONFIG.copy()
                self.config_data.update({k: v for k, v in defaults.items() if k != "fault_injection"})
            # Exercita I/O real-mode: seleciona registrador RTC via 70h e lê via 71h.
            seconds = bios_core.read_cmos_register(0x00)
            self._log(f"RTC CMOS: segundos BCD=0x{seconds:02X} (OUT 70h, índice; IN 71h, dado)")
            if self.post_faults["keyboard_missing"]:
                self._log("[ERRO] Keyboard Error - No Keyboard Present")
                self._timeline(1, "POST interrompido: teclado ausente")
                return
            if not bios_core.post_check_memory(self.config_data.get("memory_kb", 64), self.post_faults["ram_failure"]):
                self._log("[FALHA] RAM Memory Test Failure. System Halted.")
                self._timeline(1, "POST falhou no teste de memória")
                return
            self._log(f"Memory Test: {self.config_data.get('memory_kb', 64)} KB [OK]")
            self.after(0, self.progress.set, .35)
            self._timeline(2, "IVT Setup: vetores BIOS registrados na RAM baixa")
            bios_core.reset_cpu()
            for n in (0x10, 0x13, 0x16):
                entry = bios_core.get_ivt_entries(n, 1)[0]
                self._log(f"INT {n:02X}h -> {entry['segment']:04X}:{entry['offset']:04X}")
            self._log(bios_core.handle_interrupt(0x10, 0x0E, "BIOS POST")["message"])
            self.after(0, self.progress.set, .55)
            self._timeline(3, "SecureBoot Check: verificando política de boot")
            mode = self.config_data.get("boot_mode", "UEFI")
            if mode == "UEFI":
                ok, message = bios_core.verify_secure_boot("boot.bin")
                self._log("Secure Boot: " + message)
                if not ok:
                    self._timeline(3, "Boot bloqueado pela política Secure Boot")
                    return
            else:
                self._log("Legacy BIOS: Secure Boot não aplicável; validando MBR 55AA.")
            mbr = bios_core.inspect_mbr("boot.bin")
            if not mbr["signature_valid"]:
                self._log("[ERRO] No Bootable Device Found - assinatura MBR 0x55AA inválida ou setor ausente.")
                self._timeline(3, "Boot interrompido: MBR inválido")
                return
            self.after(0, self.progress.set, .85)
            self._timeline(4, "Handover: setor de boot carregado no endereço 0x7C00")
            bios_core.set_register("CS", 0x0000)
            bios_core.set_register("IP", 0x7C00)
            self.after(0, self._refresh_registers_display)
            self._log("POST Complete. Handover para bootloader em 0000:7C00.")
            self.after(0, self.progress.set, 1)
            self.after(0, lambda: self.boot_btn.configure(state="normal"))
        except Exception as exc:
            self._log(f"[EXCEÇÃO POST] {type(exc).__name__}: {exc}")
        finally:
            self.after(0, lambda: self.power_btn.configure(state="normal"))
            self.after(0, self._refresh_memory_view)
            self.after(0, self._refresh_mbr_view)

    def _execute_boot(self):
        result = bios_core.inspect_mbr("boot.bin")
        if not result["signature_valid"]:
            self._log("No Bootable Device Found")
            return
        self._log("INT 13h AH=02: setor lido para 0x7C00 (simulação).")
        boot_path = os.path.join(BASE_DIR, "boot.bin")
        qemu = shutil.which("qemu-system-x86_64") or shutil.which("qemu-system-i386")
        if qemu and os.path.isfile(boot_path):
            try:
                subprocess.Popen([qemu, "-drive", f"file={boot_path},format=raw"])
                self._log(f"[QEMU] Executando boot.bin via {os.path.basename(qemu)}...")
            except OSError as exc:
                self._log(f"[ERRO QEMU] Falha ao iniciar emulador: {exc}")
        else:
            self._log("[SIMULADOR NATIVO] Bootloader validado e entregue em 0x7C00 (QEMU não encontrado).")


if __name__ == "__main__":
    app = BiosSimulatorApp()
    app.mainloop()