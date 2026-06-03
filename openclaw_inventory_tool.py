import argparse
import json
import re
import sys

from env_loader import env_flag_enabled, load_env
from main import preguntar

load_env()


MUTATING_PREFIXES = (
    "vender ",
    "registrar venta ",
    "agregar stock ",
    "agregar unidades ",
    "iniciar dia",
    "abrir dia",
    "empezar dia",
    "cerrar dia",
    "cerrar día",
)


def is_mutating(texto):
    texto = texto.lower().strip()
    if any(texto.startswith(prefix) for prefix in MUTATING_PREFIXES):
        return True
    return bool(
        re.search(
            r"\b(?:quiero\s+)?(?:(?:registrar|hacer|anotar|crear)\s+(?:una\s+)?venta|vender)\b\s+(?:de\s+)?\d+\b",
            texto,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="OpenClaw adapter for Mundo Materno inventory commands.")
    parser.add_argument("command", nargs="*", help="Inventory command text. If omitted, JSON is read from stdin.")
    parser.add_argument("--allow-mutations", action="store_true", help="Allow sales, stock changes, and day closing.")
    args = parser.parse_args()

    if args.command:
        command = " ".join(args.command).strip()
    else:
        payload = json.load(sys.stdin)
        command = str(payload.get("command", "")).strip()

    allow_mutations = args.allow_mutations or env_flag_enabled("MUNDO_MATERNO_ALLOW_MUTATIONS")
    if is_mutating(command) and not allow_mutations:
        result = {
            "ok": False,
            "mutating": True,
            "response": "Comando bloqueado: esta accion modifica inventario o ventas. Reintenta con autorizacion explicita.",
        }
    else:
        result = {
            "ok": True,
            "mutating": is_mutating(command),
            "response": preguntar(command),
        }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
