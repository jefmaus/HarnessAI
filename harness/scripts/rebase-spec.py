#!/usr/bin/env python3
"""
Sincronizador y Rebaser determinista de specs para entornos multi-desarrollador.

Detecta si los IDs numericos de las specs introducidas en la rama local
colisionan con las specs existentes en la rama remota base (por defecto origin/main).
Si detecta colision, renumera de forma segura las carpetas (en active/, done/ o backlog/),
actualiza spec.md y tasks.md, y crea el commit de ajuste localmente.

USO:
    python harness/scripts/rebase-spec.py [--remote <remote>] [--target <branch>] [--check] [--hook]

MODOS:
    (default): Verifica colisiones; si existen, renumera y commitea el cambio.
    --check:   Solo verifica sin aplicar cambios (exit 0 si limpio, 1 si hay colisiones).
    --hook:    Modo invocado por el hook pre-push. Si aplica cambios, sale con codigo 1
               para abortar el push en vuelo e instruir al desarrollador a reintentar el push.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

# Compatibilidad UTF-8 en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HARNESS_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = HARNESS_DIR.parent
SPECS_DIR = HARNESS_DIR / "specs"
TASKS_FILE = SPECS_DIR / "tasks.md"
SUB_DIRS = ["done", "active", "backlog"]

SPEC_RE = re.compile(r"^(\d{3})-(.+)$")


def run_git(args, check=False, timeout=15):
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ROOT_DIR),
            timeout=timeout,
        )
        if check and res.returncode != 0:
            raise subprocess.CalledProcessError(res.returncode, args, res.stdout, res.stderr)
        return res
    except (subprocess.SubprocessError, OSError) as e:
        if check:
            raise
        return subprocess.CompletedProcess(["git"] + args, 1, "", str(e))


def detect_target_branch(remote):
    """Detecta la rama base remota: main o master."""
    for candidate in ["main", "master"]:
        res = run_git(["rev-parse", "--verify", f"{remote}/{candidate}"])
        if res.returncode == 0:
            return candidate
    return "main"


def fetch_remote(remote, target_branch):
    """Realiza un fetch rapido de la rama remota con timeout para evitar cuelgues."""
    res = run_git(["fetch", remote, target_branch, "--quiet"], timeout=10)
    return res.returncode == 0


def get_remote_specs(remote, target_branch):
    """Extrae {id: (folder_name, sub_folder)} de la rama remota sin hacer checkout."""
    specs = {}
    for sub in SUB_DIRS:
        res = run_git(["ls-tree", "-d", "--name-only", f"{remote}/{target_branch}:harness/specs/{sub}"])
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                name = line.strip()
                match = SPEC_RE.match(name)
                if match:
                    spec_id = int(match.group(1))
                    specs[spec_id] = (name, sub)
    return specs


def get_ancestor_specs(ancestor_commit):
    """Extrae {id: folder_name} del commit ancestro comun."""
    specs = {}
    if not ancestor_commit:
        return specs
    for sub in SUB_DIRS:
        res = run_git(["ls-tree", "-d", "--name-only", f"{ancestor_commit}:harness/specs/{sub}"])
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                name = line.strip()
                match = SPEC_RE.match(name)
                if match:
                    specs[int(match.group(1))] = name
    return specs


def get_local_specs():
    """Escanea las carpetas de specs en el arbol de trabajo local."""
    local = []
    for sub in SUB_DIRS:
        p = SPECS_DIR / sub
        if not p.is_dir():
            continue
        for entry in p.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            match = SPEC_RE.match(entry.name)
            if match:
                local.append({
                    "id": int(match.group(1)),
                    "slug": match.group(2),
                    "name": entry.name,
                    "path": entry,
                    "sub": sub,
                })
    return local


def sync_memory():
    """Ejecuta la normalización y reconstrucción del índice de memoria técnica."""
    save_mem = HARNESS_DIR / "scripts" / "save-memory.py"
    if save_mem.is_file():
        subprocess.run([sys.executable, str(save_mem), "--reindex"], capture_output=True, text=True, cwd=str(ROOT_DIR))


def renumber_spec(spec, new_id):
    """Renombra la carpeta de la spec, actualiza spec.md y tasks.md."""
    old_name = spec["name"]
    slug = spec["slug"]
    new_name = f"{new_id:03d}-{slug}"
    old_path = spec["path"]
    new_path = old_path.parent / new_name

    if new_path.exists():
        raise FileExistsError(f"El destino '{new_path}' ya existe.")

    # 1. Renombrar directorio
    old_path.rename(new_path)

    # 2. Actualizar encabezado en spec.md si coincide
    spec_md = new_path / "spec.md"
    if spec_md.is_file():
        content = spec_md.read_text(encoding="utf-8-sig")
        new_content = re.sub(
            r"^#\s*" + re.escape(old_name),
            f"# {new_name}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        spec_md.write_text(new_content, encoding="utf-8")

    # 3. Actualizar vinculo en tasks.md si aplica
    if TASKS_FILE.is_file():
        tasks_content = TASKS_FILE.read_text(encoding="utf-8-sig")
        target_header = f"> Feature: {old_name}"
        if target_header in tasks_content:
            tasks_content = tasks_content.replace(target_header, f"> Feature: {new_name}")
            TASKS_FILE.write_text(tasks_content, encoding="utf-8")

    return old_name, new_name, old_path, new_path


def main():
    parser = argparse.ArgumentParser(description="Rebaser determinista de IDs de specs contra remoto.")
    parser.add_argument("--remote", default="origin", help="Nombre del remote Git (por defecto 'origin')")
    parser.add_argument("--target", default="", help="Rama remota base (por defecto autodeteccion de main/master)")
    parser.add_argument("--check", action="store_true", help="Solo verificar colisiones sin modificar nada")
    parser.add_argument("--hook", action="store_true", help="Modo invocado desde el hook pre-push")
    args, unknown = parser.parse_known_args()

    # 1. Comprobar que git remote exista
    remotes_res = run_git(["remote"])
    if remotes_res.returncode != 0 or args.remote not in remotes_res.stdout.split():
        # No hay remote configurado o no existe 'origin'. Permitir push local.
        sys.exit(0)

    target_branch = args.target.strip() if args.target else detect_target_branch(args.remote)
    remote_ref = f"{args.remote}/{target_branch}"

    # 2. Fetch rapido
    fetch_ok = fetch_remote(args.remote, target_branch)
    ref_check = run_git(["rev-parse", "--verify", remote_ref])
    if ref_check.returncode != 0:
        # La rama remota todavia no existe (ej. repo recien creado)
        sys.exit(0)

    # 3. Identificar ancestro comun
    mb_res = run_git(["merge-base", remote_ref, "HEAD"])
    merge_base = mb_res.stdout.strip() if mb_res.returncode == 0 else ""

    # 4. Obtener catalogo de specs remotas y de ancestro
    remote_specs = get_remote_specs(args.remote, target_branch)
    ancestor_specs = get_ancestor_specs(merge_base)
    local_specs = get_local_specs()

    # 5. Filtrar specs introducidas o modificadas en esta rama
    introduced_specs = []
    for spec in local_specs:
        s_id = spec["id"]
        s_name = spec["name"]
        # Si ya existia exactamente igual en el ancestro comun, es historia compartida
        if ancestor_specs.get(s_id) == s_name:
            continue
        introduced_specs.append(spec)

    if not introduced_specs:
        if not args.hook:
            print(f"✅ [REBASE-SPEC] Sin specs locales nuevas que verificar contra {remote_ref}.")
        sys.exit(0)

    # 6. Detectar colisiones
    # Hay colision si el ID de una spec introducida localmente ya esta usado en el remote
    # por una spec distinta, o si en el remote sufrio cambios independientes.
    collisions = []
    for spec in introduced_specs:
        s_id = spec["id"]
        if s_id in remote_specs:
            remote_name, remote_sub = remote_specs[s_id]
            if remote_name != spec["name"]:
                collisions.append((spec, remote_name))
            else:
                # Mismo nombre: verificar si hubo divergencia de arbol
                diff_res = run_git(["diff", "--quiet", remote_ref, "HEAD", "--", str(spec["path"])])
                if diff_res.returncode != 0:
                    collisions.append((spec, remote_name))

    if not collisions:
        if not args.hook:
            print(f"✅ [REBASE-SPEC] Verificacion exitosa: sin colisiones de specs con {remote_ref}.")
        sys.exit(0)

    # Si estamos en modo solo chequeo, reportar y salir con 1
    if args.check:
        print(f"❌ [REBASE-SPEC] Se detectaron {len(collisions)} colisiones de IDs con {remote_ref}:")
        for local_s, r_name in collisions:
            print(f"   - Local: {local_s['name']}  <-->  Remoto: {r_name}")
        sys.exit(1)

    # 7. Aplicar Auto-Rebase determinista
    # Calcular IDs ocupados (remotos + locales no colisionados)
    colliding_ids = {s["id"] for s, _ in collisions}
    all_taken_ids = set(remote_specs.keys()) | {s["id"] for s in local_specs if s["id"] not in colliding_ids}
    next_id = (max(all_taken_ids) if all_taken_ids else 0) + 1

    renamed_items = []
    # Ordenar colisiones por su ID original para conservar el orden relativo
    collisions.sort(key=lambda x: x[0]["id"])

    for spec, remote_name in collisions:
        old_name, new_name, old_path, new_path = renumber_spec(spec, next_id)
        renamed_items.append((old_name, new_name, old_path, new_path, remote_name))
        all_taken_ids.add(next_id)
        next_id += 1

    # 8. Sincronizar memoria técnica y commitear ajuste en Git
    sync_memory()
    for old_name, new_name, old_path, new_path, _ in renamed_items:
        run_git(["add", str(new_path)])
        run_git(["add", "-u", str(old_path)])
    if TASKS_FILE.is_file():
        run_git(["add", str(TASKS_FILE)])
    run_git(["add", str(HARNESS_DIR / "memory" / "details.jsonl")])
    run_git(["add", str(HARNESS_DIR / "memory" / "index.md")])

    summary_renames = ", ".join(f"{o} -> {n}" for o, n, _, _, _ in renamed_items)
    commit_msg = f"chore(specs): auto-rebase spec IDs por colision con {remote_ref} ({summary_renames})"
    commit_res = run_git(["commit", "-m", commit_msg])

    # 9. Notificar al usuario o hook
    print("=" * 65)
    print(f"❌ [PRE-PUSH] Se detecto colision de ID(s) de specs con '{remote_ref}':")
    for old_name, new_name, _, _, remote_name in renamed_items:
        print(f"   • Tu spec:   {old_name}")
        print(f"     En remote: {remote_name}")
        print(f"     Ajustada:  {new_name}")
    print("-" * 65)
    print(f"🔄 Auto-rebase aplicado: se creo commit local de ajuste:")
    print(f"   \"{commit_msg}\"")
    print("=" * 65)
    print("👉 VUELVE A EJECUTAR 'git push' para enviar tus cambios actualizados.")
    print("=" * 65)

    if args.hook:
        # Abortar el push en curso para que el desarrollador reintente con el nuevo commit
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
