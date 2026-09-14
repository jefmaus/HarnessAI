#!/usr/bin/env python3
"""
Persistencia atómica y quirúrgica de decisiones técnicas de arquitectura (ADRs) y soluciones a trampas no triviales.
"""
import datetime
import json
import re
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
MEMORY_DIR = HARNESS_DIR / "memory"
INDEX_FILE = MEMORY_DIR / "index.md"
DETAILS_FILE = MEMORY_DIR / "details.jsonl"

def init_memory_storage():
    """Garantiza la existencia del directorio y los archivos base de memoria."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        header = "# Índice de Memoria Técnica\n\n| ID | Fecha | Módulo | Título |\n| :--- | :--- | :--- | :--- |\n"
        INDEX_FILE.write_text(header, encoding="utf-8")
    if not DETAILS_FILE.exists():
        DETAILS_FILE.touch()

def get_next_id():
    """Calcula el siguiente identificador MEM-XXX como max(details.jsonl, index.md) + 1.

    Leer TAMBIEN index.md evita IDs duplicados si el JSONL se corrompio, se borro
    o si el indice fue editado a mano (v1.1).
    """
    max_num = 0
    if DETAILS_FILE.exists():
        with DETAILS_FILE.open("r", encoding="utf-8-sig") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    record = json.loads(line_str)
                    rec_id = str(record.get("id", ""))
                    if rec_id.startswith("MEM-"):
                        num = int(rec_id.replace("MEM-", ""))
                        max_num = max(max_num, num)
                except (ValueError, json.JSONDecodeError):
                    continue
    if INDEX_FILE.exists():
        with INDEX_FILE.open("r", encoding="utf-8-sig") as f:
            for match in re.finditer(r"MEM-(\d+)", f.read()):
                max_num = max(max_num, int(match.group(1)))
    return f"MEM-{max_num + 1:03d}"

def clean_markdown_cell(text):
    """Escapa pipes y elimina saltos de línea para mantener la integridad de la tabla Markdown."""
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()

def main():
    if len(sys.argv) < 5:
        print("Uso: python harness/scripts/save-memory.py <modulo> <titulo> <contexto> <solucion>")
        print("Ejemplo: python harness/scripts/save-memory.py \"auth\" \"Uso de Argon2id\" \"Seguridad passwords\" \"Configuración con costo 3\"")
        sys.exit(1)

    init_memory_storage()

    module = sys.argv[1].strip()
    title = sys.argv[2].strip()
    context = sys.argv[3].strip()
    solution = sys.argv[4].strip()
    today = datetime.date.today().isoformat()
    record_id = get_next_id()

    record = {
        "id": record_id,
        "date": today,
        "module": module,
        "title": title,
        "context": context,
        "solution": solution
    }

    # 1. Guardar en details.jsonl
    with DETAILS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 2. Actualizar index.md asegurando formato Markdown tabular válido
    safe_module = clean_markdown_cell(module)
    safe_title = clean_markdown_cell(title)
    index_row = f"| `{record_id}` | {today} | `{safe_module}` | {safe_title} |\n"

    with INDEX_FILE.open("a", encoding="utf-8") as f:
        f.write(index_row)

    print(f"✅ Memoria técnica registrada exitosamente:")
    print(f"   ID:     {record_id}")
    print(f"   Módulo: {module}")
    print(f"   Título: {title}")

if __name__ == "__main__":
    main()
