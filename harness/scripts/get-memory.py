#!/usr/bin/env python3
"""
Recuperador JIT (Just-In-Time) de registros de memoria técnica por su identificador único.
Permite consultar el contexto profundo de una decisión sin sobrecargar los tokens del modelo.
"""
import json
import sys
from pathlib import Path

# Asegurar compatibilidad UTF-8 en consolas Windows (cp1252 / cp850)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HARNESS_DIR = Path(__file__).resolve().parent.parent
DETAILS_FILE = HARNESS_DIR / "memory" / "details.jsonl"

def main():
    if len(sys.argv) < 2:
        print("Uso: python harness/scripts/get-memory.py <ID_REGISTRO>")
        print("Ejemplo: python harness/scripts/get-memory.py MEM-001")
        sys.exit(1)

    target_id = sys.argv[1].strip().upper()

    if not DETAILS_FILE.exists():
        print(f"❌ Error: El almacén '{DETAILS_FILE}' no existe.")
        sys.exit(1)

    found = False
    with DETAILS_FILE.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                record = json.loads(line_str)
            except json.JSONDecodeError:
                continue

            if record.get("id", "").upper() == target_id:
                found = True
                print("=" * 60)
                print(f"📌 [{record['id']}] {record.get('title', 'Sin título')}")
                print(f"📅 Fecha:   {record.get('date', 'N/A')}")
                print(f"📦 Módulo:  {record.get('module', 'N/A')}")
                print("-" * 60)
                print(f"🔍 Contexto y Problema:\n{record.get('context', '')}\n")
                print(f"💡 Decisión de Diseño / Solución Técnica:\n{record.get('solution', '')}")
                print("=" * 60)
                break

    if not found:
        print(f"⚠️ No se encontró ningún registro con ID: {target_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()
