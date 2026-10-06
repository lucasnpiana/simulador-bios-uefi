"""
bios_gui.py
Simulador de BIOS - Interface Gráfica Estilo UEFI ASUS GURI (Funcional).
"""
import os

# Força o Python a encontrar o QEMU do MSYS2
qemu_bin = r"C:\msys64\ucrt64\bin"
if qemu_bin not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + qemu_bin
import subprocess
import threading
import time
import os
import platform
import shutil
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk
import bios_core

# Força visual escuro padrão, tema GURI
ctk.set_appearance_mode("dark")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BOOT_DEVICE_LABELS = {
    "HDD": "HDD (Disco Rígido)",
    "USB": "USB (Pendrive)",
    "FLOPPY": "Floppy (Disquete)",
    "NETWORK": "Rede (PXE)",
}
LABEL_TO_DEVICE = {v: k for k, v in BOOT_DEVICE_LABELS.items()}

# Cores Modernas de UEFI BIOS ASUS GURI
COLOR_GURI_BLACK = "#0A0A0A"
COLOR_GURI_RED = "#CC0000"
COLOR_GURI_DARK_RED = "#880000"
COLOR_GURI_WHITE = "#FFFFFF"
COLOR_GURI_YELLOW = "#FFFF00"
COLOR_POST_BLACK = "#000000"
COLOR_POST_GREEN = "#55FF55"
COLOR_POST_RED = "#FF5555"

FONT_GURI_MAIN = "Arial"
FONT_MONO = "Courier New"


class BiosSimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("UEFI BIOS Utility - Advanced Mode (Simulador)")
        self.geometry("960x640")
        self.configure(fg_color=COLOR_GURI_BLACK)

        self.config_data = bios_core.load_config()

        self._build_layout()
        self._refresh_registers_display()

    def _build_layout(self):
        header_frame = ctk.CTkFrame(
            self, fg_color=COLOR_GURI_BLACK, corner_radius=0, height=50
        )
        header_frame.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header_frame, text=" [GURI] ", font=(FONT_GURI_MAIN, 20, "bold"), text_color=COLOR_GURI_RED
        ).pack(side="left", padx=(5, 10))

        ctk.CTkLabel(
            header_frame, text=" UEFI BIOS Utility - Advanced Mode ", font=(FONT_GURI_MAIN, 16, "bold"), text_color=COLOR_GURI_WHITE
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            header_frame, text=datetime.now().strftime("%d/%m/%Y   %H:%M"), font=(FONT_GURI_MAIN, 12), text_color=COLOR_GURI_WHITE
        ).pack(side="right", padx=(10, 5))

        main_frame = ctk.CTkFrame(self, fg_color=COLOR_GURI_BLACK, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        central_panel = ctk.CTkFrame(main_frame, fg_color=COLOR_GURI_BLACK, corner_radius=0)
        central_panel.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)

        self._build_side_panel(main_frame)
        self._build_setup_panel(central_panel)
        self._build_post_panel(central_panel)
        self._build_footer()

    def _build_side_panel(self, parent):
        side_panel = ctk.CTkFrame(
            parent, fg_color=COLOR_GURI_BLACK, corner_radius=0, width=220, border_width=1, border_color=COLOR_GURI_RED
        )
        side_panel.pack(side="right", fill="y", padx=(5, 0), pady=0, ipadx=10)

        ctk.CTkLabel(
            side_panel, text=" [ Hardware Monitor ] ", 
            font=(FONT_GURI_MAIN, 14, "bold"), text_color=COLOR_GURI_RED
        ).pack(anchor="w", padx=10, pady=(15, 10))

        ctk.CTkLabel(
            side_panel, text=" [ CPU ] ", 
            font=(FONT_GURI_MAIN, 12, "bold"), text_color=COLOR_GURI_RED
        ).pack(anchor="w", padx=10, pady=(5, 2))

        self.register_vars = {}
        for reg in ("AX", "BX", "CX", "DX"):
            var = ctk.StringVar(value=f"{reg} : 0x0000")
            self.register_vars[reg] = var
            ctk.CTkLabel(
                side_panel, textvariable=var, 
                font=(FONT_GURI_MAIN, 12), text_color=COLOR_GURI_WHITE
            ).pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(
            side_panel, text=" [ Memory ] ", 
            font=(FONT_GURI_MAIN, 12, "bold"), text_color=COLOR_GURI_RED
        ).pack(anchor="w", padx=10, pady=(10, 2))

        for reg in ("CS", "IP"):
            var = ctk.StringVar(value=f"{reg} : 0x0000")
            self.register_vars[reg] = var
            ctk.CTkLabel(
                side_panel, textvariable=var, 
                font=(FONT_GURI_MAIN, 12), text_color=COLOR_GURI_WHITE
            ).pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(
            side_panel, text=" [ Voltage ] ", 
            font=(FONT_GURI_MAIN, 12, "bold"), text_color=COLOR_GURI_RED
        ).pack(anchor="w", padx=10, pady=(10, 2))

        self.label_physical_addr = ctk.CTkLabel(
            side_panel, text="PHY ADDR : 0x00000", 
            font=(FONT_GURI_MAIN, 11), text_color=COLOR_GURI_YELLOW
        )
        self.label_physical_addr.pack(anchor="w", padx=20, pady=5)

        self._build_action_buttons(side_panel)

    def _build_setup_panel(self, parent):
        frame_setup = ctk.CTkFrame(
            parent, fg_color=COLOR_GURI_BLACK, corner_radius=0, border_width=1, border_color=COLOR_GURI_DARK_RED
        )
        frame_setup.pack(pady=0, padx=0, fill="x")

        ctk.CTkLabel(
            frame_setup, text=" [ CMOS SETUP ] ", 
            font=(FONT_GURI_MAIN, 14, "bold"), text_color=COLOR_GURI_RED
        ).pack(anchor="w", padx=15, pady=10)

        grid_frame = ctk.CTkFrame(frame_setup, fg_color="transparent")
        grid_frame.pack(fill="x", padx=15)

        ctk.CTkLabel(
            grid_frame, text="First Boot Device :", 
            font=(FONT_GURI_MAIN, 12), text_color=COLOR_GURI_WHITE
        ).grid(row=0, column=0, sticky="w", pady=5)

        self.combo_boot = ctk.CTkComboBox(
            grid_frame, values=list(BOOT_DEVICE_LABELS.values()), width=200,
            corner_radius=0, font=(FONT_GURI_MAIN, 12), fg_color=COLOR_GURI_BLACK,
            button_color=COLOR_GURI_DARK_RED, text_color=COLOR_GURI_YELLOW, dropdown_font=(FONT_GURI_MAIN, 12)
        )
        self.combo_boot.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        first_device = self.config_data["boot_order"][0]
        self.combo_boot.set(BOOT_DEVICE_LABELS.get(first_device, BOOT_DEVICE_LABELS["HDD"]))

        self.simulate_failure_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            frame_setup, text="Simulate RAM Failure on next POST",
            variable=self.simulate_failure_var, font=(FONT_GURI_MAIN, 11),
            text_color=COLOR_GURI_WHITE, corner_radius=0, checkbox_width=16, checkbox_height=16,
            fg_color=COLOR_GURI_RED, hover_color=COLOR_GURI_DARK_RED
        ).pack(anchor="w", padx=15, pady=10)

        btn_save = ctk.CTkButton(
            frame_setup, text="[ SAVE CMOS ]", command=self._salvar_cmos,
            corner_radius=0, fg_color=COLOR_GURI_DARK_RED, hover_color=COLOR_GURI_RED,
            font=(FONT_GURI_MAIN, 11, "bold"), text_color=COLOR_GURI_WHITE, height=28
        )
        btn_save.pack(anchor="w", padx=15, pady=5)

        self.label_status = ctk.CTkLabel(frame_setup, text="", font=(FONT_GURI_MAIN, 11))
        self.label_status.pack(anchor="w", padx=15, pady=2)

    def _build_post_panel(self, parent):
        frame_post = ctk.CTkFrame(
            parent, fg_color=COLOR_GURI_BLACK, corner_radius=0, border_width=1, border_color=COLOR_GURI_DARK_RED
        )
        frame_post.pack(fill="both", expand=True, padx=0, pady=10)

        header_frame = ctk.CTkFrame(frame_post, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(
            header_frame, text=" [ POST TERMINAL ] ", 
            font=(FONT_GURI_MAIN, 14, "bold"), text_color=COLOR_GURI_RED
        ).pack(side="left", pady=10)

        ctk.CTkButton(
            header_frame, text="Save Log", width=80, font=(FONT_GURI_MAIN, 10, "bold"),
            command=self._salvar_log, corner_radius=0, fg_color=COLOR_GURI_DARK_RED, hover_color=COLOR_GURI_RED
        ).pack(side="right", padx=15)

        self.caixa_logs = ctk.CTkTextbox(
            frame_post, height=130, font=(FONT_MONO, 11),
            fg_color=COLOR_POST_BLACK, text_color=COLOR_POST_GREEN,
            corner_radius=0, border_width=1, border_color="#444444"
        )
        self.caixa_logs.pack(fill="both", expand=True, padx=15, pady=5)
        self._escrever_log("System Halted. Press 'POWER ON' to initiate POST sequence...")
        self.caixa_logs.configure(state="disabled")

        self.barra_progresso = ctk.CTkProgressBar(
            frame_post, mode="determinate", corner_radius=0, 
            height=12, progress_color=COLOR_GURI_YELLOW, fg_color=COLOR_POST_BLACK
        )
        self.barra_progresso.pack(fill="x", padx=15, pady=10)
        self.barra_progresso.set(0)

    def _build_action_buttons(self, parent):
        ctk.CTkLabel(
            parent, text=" [ Action ] ", 
            font=(FONT_GURI_MAIN, 12, "bold"), text_color=COLOR_GURI_RED
        ).pack(anchor="w", padx=10, pady=(15, 2))

        self.btn_ligar = ctk.CTkButton(
            parent, text="[ POWER ON (POST) ]", command=self._iniciar_post,
            fg_color=COLOR_GURI_RED, hover_color=COLOR_GURI_DARK_RED, font=(FONT_GURI_MAIN, 12, "bold"),
            corner_radius=0, height=35
        )
        self.btn_ligar.pack(side="bottom", pady=10, fill="x", padx=10)

        self.btn_qemu = ctk.CTkButton(
            parent, text="[ BOOT EXECUTE ]", command=self._rodar_qemu, state="disabled",
            fg_color="#444444", hover_color="#666666", font=(FONT_GURI_MAIN, 12, "bold"),
            corner_radius=0, height=35
        )
        self.btn_qemu.pack(side="bottom", pady=(0, 5), fill="x", padx=10)

    def _build_footer(self):
        footer_frame = ctk.CTkFrame(
            self, fg_color=COLOR_GURI_BLACK, corner_radius=0, height=30
        )
        footer_frame.pack(fill="x", side="bottom", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            footer_frame, text=" [GURI] ASUS UEFI BIOS Utility | Advanced Mode ", font=(FONT_GURI_MAIN, 11), text_color=COLOR_GURI_WHITE
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            footer_frame, text=" v1.1 GURI Simulator ", font=(FONT_GURI_MAIN, 11), text_color=COLOR_GURI_RED
        ).pack(side="right", padx=(10, 5))

    def _escrever_log(self, texto: str):
        self.caixa_logs.configure(state="normal")
        self.caixa_logs.insert("end", texto + "\n")
        self.caixa_logs.see("end")
        self.caixa_logs.configure(state="disabled")

    def _salvar_log(self):
        conteudo = self.caixa_logs.get("1.0", "end").strip()
        if not conteudo:
            self.label_status.configure(text="> Log is empty.", text_color=COLOR_POST_RED)
            return

        sugestao_nome = f"uefi_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        caminho = filedialog.asksaveasfilename(
            initialdir=BASE_DIR,
            initialfile=sugestao_nome,
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("All Files", "*.*")],
            title="Save POST Log",
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("ASUS UEFI BIOS (C) 1984-2026 ASUSTeK Computer Inc.\n")
                f.write(f"Log Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(conteudo + "\n")
            self.label_status.configure(
                text="> Log saved successfully.", text_color=COLOR_POST_GREEN
            )
        except OSError as exc:
            self.label_status.configure(text=f"> Error: {exc}", text_color=COLOR_POST_RED)

    def _refresh_registers_display(self):
        regs = bios_core.get_registers()
        for reg, var in self.register_vars.items():
            var.set(f"{reg} : 0x{regs[reg]:04X}")
        self.label_physical_addr.configure(
            text=f"PHY ADDR : 0x{regs['physical_address']:05X}"
        )

    def _salvar_cmos(self):
        device = LABEL_TO_DEVICE.get(self.combo_boot.get())
        if device is None:
            self.label_status.configure(text="> Invalid Device", text_color=COLOR_POST_RED)
            return

        new_config = dict(self.config_data)
        new_config["boot_order"] = [device] + [
            d for d in self.config_data["boot_order"] if d != device
        ]

        try:
            bios_core.save_config(new_config)
            self.config_data = new_config
            self.label_status.configure(
                text=f"> CMOS Saved: {device}", text_color=COLOR_POST_GREEN
            )
        except ValueError as exc:
            self.label_status.configure(text=f"> Error: {exc}", text_color=COLOR_POST_RED)

    def _iniciar_post(self):
        self.btn_ligar.configure(state="disabled")
        self.btn_qemu.configure(state="disabled")
        threading.Thread(target=self._simular_post_thread, daemon=True).start()

    def _simular_post_thread(self):
        def log(texto):
            self.after(0, self._escrever_log, texto)

        def progress(value):
            self.after(0, self.barra_progresso.set, value)

        log(" [GURI] ASUS UEFI BIOS Utility | Advanced Mode ")
        log("American Megatrends UEFI v2.17, Inc. An Ally Ally")
        log("Copyright (C) ASUSTeK Computer Inc.\n")
        log("Main Processor : x86 Architecture")
        
        bios_core.reset_cpu()
        time.sleep(0.6)

        log("Memory Testing : [ Check ]")
        progress(0.25)
        simulate_failure = self.simulate_failure_var.get()
        memory_ok = bios_core.post_check_memory(
            self.config_data["memory_kb"], simulate_failure=simulate_failure
        )
        if not memory_ok:
            log("[FALHA] Memory Test FAIL! System Halted.")
            self.after(0, lambda: self.btn_ligar.configure(state="normal"))
            return
            
        log(f"Memory Test : {self.config_data['memory_kb']}K [OK]")
        time.sleep(0.5)

        log("Initializing CPU Registers (C Core)...")
        bios_core.set_register("AX", 0x0E00)
        bios_core.set_register("BX", 0x0007)
        bios_core.set_register("CX", 0x1234)
        bios_core.set_register("DX", 0xABCD)
        self.after(0, self._refresh_registers_display)
        progress(0.6)
        time.sleep(0.8)

        log("Reading NVRAM / CMOS Settings... [OK]")
        progress(0.9)
        time.sleep(0.5)

        primeiro_dispositivo = self.config_data["boot_order"][0]
        log(f"Executing EFI Boot Service (Booting from {primeiro_dispositivo})...")
        progress(1.0)
        time.sleep(0.5)

        log("\n> POST Complete. Control transfer to OS Bootloader.")
        self.after(0, lambda: self.btn_ligar.configure(state="normal"))
        self.after(0, lambda: self.btn_qemu.configure(state="normal"))

    def _rodar_qemu(self):
        self._escrever_log("> Solicitando compilação no container Docker...")
        
        comando_docker = [
            "docker", "run", "--rm",
            "-v", f"{BASE_DIR}:/codigo",
            "sys-compilador",
            "make", "boot.bin"
        ]

        def executar_boot():
            try:
                resultado = subprocess.run(comando_docker, cwd=BASE_DIR, capture_output=True, text=True)
                
                if resultado.returncode != 0:
                    self.after(0, self._escrever_log, f"> [ERRO DE COMPILAÇÃO]: {resultado.stderr}\n{resultado.stdout}")
                    return

                self.after(0, self._escrever_log, "> Compilação concluída com sucesso! Iniciando QEMU...")

                # CORREÇÃO: o "make" não existe no PATH do Windows (só dentro do Docker),
                # por isso o QEMU é chamado diretamente, sem passar pelo make.
                qemu_exe = shutil.which("qemu-system-i386") or os.path.join(
                    qemu_bin, "qemu-system-i386.exe"
                )

                if not os.path.isfile(os.path.join(BASE_DIR, "boot.bin")):
                    self.after(0, self._escrever_log, "> [ERRO] boot.bin não foi encontrado na pasta do projeto.")
                    return

                subprocess.Popen(
                    [qemu_exe, "-drive", "format=raw,file=boot.bin"],
                    cwd=BASE_DIR
                )
                
            except FileNotFoundError:
                self.after(
                    0, self._escrever_log,
                    "> [ERRO] qemu-system-i386 não encontrado. Instale no MSYS2 UCRT64 com: "
                    "pacman -S mingw-w64-ucrt-x86_64-qemu"
                )
            except Exception as exc:
                self.after(0, self._escrever_log, f"> [ERRO] {exc}")

        threading.Thread(target=executar_boot, daemon=True).start()

# O if TEM que ficar totalmente encostado na margem esquerda!
if __name__ == "__main__":
    app = BiosSimulatorApp()
    app.mainloop()