#!/usr/bin/env python3
"""
Persistencia atómica y quirúrgica de decisiones técnicas de arquitectura (ADRs) y soluciones a trampas no triviales.

Estrategia concurrente (v1.2):
- 'harness/memory/details.jsonl' utiliza merge=union de Git (append-only sin marcas de conflicto).
- 'harness/memory/index.md' se autogenera deterministamente a partir del JSONL para evitar
  conflictos en tablas Markdown.
- Soporta '--reindex' para reconstruir el índice bajo demanda y normalizar IDs duplicados
  en caso de merges concurrentes.
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
    if not DETAILS_FILE.exists():
        DETAILS_FILE.touch()
    if not INDEX_FILE.exists():
        header = "# Índice de Memoria Técnica\n\n| ID | Fecha | Módulo | Título |\n| :--- | :--- | :--- | :--- |\n"
        INDEX_FILE.write_text(header, encoding="utf-8")


def clean_markdown_cell(text):
    """Escapa pipes y elimina saltos de línea para mantener la integridad de la tabla Markdown."""
    return str(text).replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def load_records():
    """Carga y valida todos los registros desde details.jsonl."""
    records = []
    if not DETAILS_FILE.exists():
        return records

    with DETAILS_FILE.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                record = json.loads(line_str)
                if isinstance(record, dict) and "id" in record:
                    records.append(record)
            except json.JSONDecodeError:
                continue
    return records


def rebuild_index():
    """Reconstruye index.md a partir de details.jsonl y resuelve colisiones de IDs."""
    init_memory_storage()
    records = load_records()

    # Detectar si hay IDs duplicados (ej. tras un union merge de Git)
    seen_ids = set()
    has_duplicates = False
    for r in records:
        rec_id = str(r.get("id", ""))
        if rec_id in seen_ids:
            has_duplicates = True
            break
        seen_ids.add(rec_id)

    renumbered_count = 0
    if has_duplicates:
        # Renumerar secuencialmente conservando el orden cronológico
        for idx, r in enumerate(records, start=1):
            expected_id = f"MEM-{idx:03d}"
            if r.get("id") != expected_id:
                r["id"] = expected_id
                renumbered_count += 1
        # Reescribir details.jsonl normalizado
        with DETAILS_FILE.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Generar tabla Markdown en index.md
    lines = [
        "# Índice de Memoria Técnica",
        "",
        "| ID | Fecha | Módulo | Título |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for r in records:
        r_id = r.get("id", "MEM-???")
        r_date = r.get("date", "")
        r_mod = clean_markdown_cell(r.get("module", ""))
        r_title = clean_markdown_cell(r.get("title", "Sin título"))
        lines.append(f"| `{r_id}` | {r_date} | `{r_mod}` | {r_title} |")

    lines.append("")  # Salto de línea final
    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")

    return len(records), renumbered_count


def get_next_id():
    """Calcula el siguiente identificador MEM-XXX basado en los registros existentes."""
    records = load_records()
    max_num = 0
    for r in records:
        rec_id = str(r.get("id", ""))
        if rec_id.startswith("MEM-"):
            try:
                num = int(rec_id.replace("MEM-", ""))
                max_num = max(max_num, num)
            except ValueError:
                continue
    return f"MEM-{max_num + 1:03d}"


def main():
    if len(sys.argv) == 2 and sys.argv[1].strip() == "--reindex":
        total, renumbered = rebuild_index()
        print(f"✅ [MEMORY] Índice '{INDEX_FILE.name}' regenerado exitosamente ({total} registros).")
        if renumbered > 0:
            print(f"   ℹ️  Se normalizaron {renumbered} IDs duplicados tras merge de Git.")
        sys.exit(0)

    if len(sys.argv) < 5:
        print("Uso: python harness/scripts/save-memory.py <modulo> <titulo> <contexto> <solucion>")
        print("     python harness/scripts/save-memory.py --reindex")
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

    # 1. Guardar registro en details.jsonl (append)
    with DETAILS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 2. Reconstruir index.md automáticamente a partir de details.jsonl
    rebuild_index()

    print(f"✅ Memoria técnica registrada exitosamente:")
    print(f"   ID:     {record_id}")
    print(f"   Módulo: {module}")
    print(f"   Título: {title}")
    print(f"   Índice: {INDEX_FILE.relative_to(HARNESS_DIR.parent)} actualizado automáticamente.")


if __name__ == "__main__":
    main()
