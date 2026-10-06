"""
main.py
Simulador de BIOS - interface de terminal (Python + rich).
Toda a lógica de CPU/memória (C) e de configuração fica em bios_core.py;
este arquivo cuida só da apresentação e do fluxo de telas.
"""

import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import bios_core

console = Console()


def run_post(config: dict) -> bool:
    console.rule("[bold blue]Simulador de BIOS[/bold blue]")
    console.print("[bold]Iniciando POST (Power-On Self Test)...[/bold]\n")

    bios_core.reset_cpu()
    time.sleep(0.4)
    regs = bios_core.get_registers()
    console.print(
        f"[green]OK[/green] CPU resetada. "
        f"CS:IP = {regs['CS']:04X}:{regs['IP']:04X}  "
        f"(endereço físico 0x{regs['physical_address']:05X})"
    )

    time.sleep(0.4)
    console.print(f"Testando memória ({config['memory_kb']} KB)...", end=" ")
    if bios_core.post_check_memory(config["memory_kb"]):
        console.print("[green]OK[/green]")
    else:
        console.print("[red]FALHA[/red] - memória não passou no teste")
        return False

    bios_core.set_register("AX", 0x1234)
    time.sleep(0.3)
    console.print(f"[green]OK[/green] Registrador AX inicializado: [yellow]0x{bios_core.get_register('AX'):04X}[/yellow]")

    time.sleep(0.3)
    console.print("[green]OK[/green] Dispositivos detectados: teclado, disco, rede (simulado)")

    time.sleep(0.4)
    console.print("\n[bold green]POST concluído com sucesso.[/bold green]")
    console.print("Pressione [bold]DEL[/bold] para entrar no Setup ou aguarde para continuar o boot...\n")
    time.sleep(1.0)
    return True


def show_setup(config: dict) -> dict:
    working = dict(config)  # edita uma cópia; só persiste se o usuário salvar

    while True:
        console.clear()
        table = Table(title="BIOS Setup Utility", show_lines=True)
        table.add_column("Opção", style="cyan")
        table.add_column("Valor atual", style="yellow")

        table.add_row("1) Ordem de boot", " -> ".join(working["boot_order"]))
        table.add_row("2) Memória simulada (KB)", str(working["memory_kb"]))
        table.add_row("3) Data do sistema", working["date"])
        table.add_row("4) Salvar e sair", "")
        table.add_row("5) Sair sem salvar", "")

        console.print(Panel(table, title="[bold blue]Main / Advanced / Boot[/bold blue]"))
        choice = console.input("Escolha uma opção: ").strip()

        if choice == "1":
            raw = console.input(
                f"Nova ordem separada por vírgula (opções: {', '.join(bios_core.VALID_BOOT_DEVICES)}): "
            )
            candidate = [x.strip().upper() for x in raw.split(",") if x.strip()]
            errors = bios_core.validate_config({**working, "boot_order": candidate})
            if errors:
                console.print(f"[red]{'; '.join(errors)}[/red]")
                time.sleep(1.5)
            else:
                working["boot_order"] = candidate

        elif choice == "2":
            raw = console.input(f"Nova quantidade de memória (KB, máx {bios_core.MAX_MEMORY_KB}): ")
            try:
                candidate = int(raw)
            except ValueError:
                console.print("[red]Valor inválido, precisa ser um número inteiro.[/red]")
                time.sleep(1.5)
                continue
            errors = bios_core.validate_config({**working, "memory_kb": candidate})
            if errors:
                console.print(f"[red]{'; '.join(errors)}[/red]")
                time.sleep(1.5)
            else:
                working["memory_kb"] = candidate

        elif choice == "3":
            working["date"] = console.input("Nova data (AAAA-MM-DD): ")

        elif choice == "4":
            bios_core.save_config(working)
            console.print("[green]Configurações salvas.[/green]")
            time.sleep(1)
            return working

        elif choice == "5":
            return config  # descarta as edições, devolve a config original

        else:
            console.print("[red]Opção inválida.[/red]")
            time.sleep(1)


def run_boot(config: dict) -> None:
    console.rule("[bold blue]Boot[/bold blue]")
    for device in config["boot_order"]:
        console.print(f"Procurando dispositivo de boot: {device}...", end=" ")
        time.sleep(0.5)
        if device == "HDD":
            console.print("[green]encontrado![/green]")
            console.print("\nCarregando sistema a partir do HDD...\n")
            time.sleep(0.6)
            console.print("[bold green]Sistema iniciado com sucesso (simulado).[/bold green]")
            return
        console.print("[red]não encontrado[/red]")

    console.print("\n[bold red]Nenhum dispositivo de boot encontrado.[/bold red]")


def main():
    config = bios_core.load_config()

    try:
        if not run_post(config):
            return

        key = console.input("[bold]Pressione ENTER para continuar ou digite 'setup': [/bold]")
        if key.strip().lower() == "setup":
            config = show_setup(config)

        run_boot(config)

    except KeyboardInterrupt:
        console.print("\n[yellow]Simulação interrompida pelo usuário.[/yellow]")


if __name__ == "__main__":
    main()