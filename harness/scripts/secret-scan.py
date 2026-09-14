#!/usr/bin/env python3
"""
Escanner determinista de secretos sobre el staging de Git (logica del hook pre-commit).

Diseno v1.1:
- Revisa SOLO archivos agregados/copiados/modificados (--diff-filter=ACM --no-renames).
  Los BORRADOS se permiten a proposito: eliminar un secreto comprometido del repo debe
  poder commitearse sin violar la constitucion (--no-verify esta vetado).
- Nombre: patrones de archivos sensibles, con excepciones de plantillas inofensivas
  (.env.example, claves publicas *.pub).
- Contenido: solo las LINEAS ANADIDAS del diff staged, contra patrones de alta senal
  (claves privadas, AWS, GitHub, Slack). Sin deteccion por entropia para evitar
  falsos positivos.
- Nunca imprime el secreto detectado, solo archivo + patron.
"""
import re
import subprocess
import sys

# Asegurar compatibilidad UTF-8 en consolas Windows (cp1252 / cp850)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

NAME_PATTERNS = [
    (re.compile(r"(?:^|/)\.env($|\.)(?![/\\]?example$)", re.IGNORECASE),
     "archivo .env o variante de entorno"),
    (re.compile(r"\.(pem|key|p12|pfx|jks|keystore)$", re.IGNORECASE),
     "archivo de clave o certificado"),
    (re.compile(r"(?:^|/)id_(rsa|dsa|ecdsa|ed25519)$"),
     "par de claves SSH"),
]

CONTENT_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"), "bloque de clave privada"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "access key de AWS"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "token personal de GitHub"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{22,}"), "token fine-grained de GitHub"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "token de Slack"),
]


def run_git(args):
    try:
        res = subprocess.run(["git"] + args, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"❌ [SECRET-SCAN] No se pudo ejecutar git: {e}")
        sys.exit(1)
    if res.returncode != 0:
        print(f"❌ [SECRET-SCAN] 'git {' '.join(args)}' fallo: {(res.stderr or '').strip()}")
        sys.exit(1)
    return res.stdout


def staged_files():
    out = run_git(["diff", "--cached", "--name-only", "--no-renames", "--diff-filter=ACM", "-z"])
    return [f for f in out.split("\x00") if f]


def added_lines():
    """Itera (archivo, linea_anadida) sobre el diff staged en contexto minimo."""
    out = run_git(["diff", "--cached", "-U0", "--no-renames", "--diff-filter=ACM"])
    current = None
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            yield current or "<desconocido>", line[1:]


def main():
    findings = []

    for f in staged_files():
        for rx, label in NAME_PATTERNS:
            if rx.search(f):
                findings.append(f"  - nombre: '{f}'  ({label})")

    for f, line in added_lines():
        for rx, label in CONTENT_PATTERNS:
            if rx.search(line):
                findings.append(f"  - contenido: '{f}' contiene un patron de {label}")

    if findings:
        print("❌ [SECRET-SCAN] Se detectaron posibles credenciales en el staging:")
        for finding in findings:
            print(finding)
        print("Excluye el secreto del commit (git restore --staged <archivo> y edita el archivo).")
        print("Si es un borrado lo que falla: los borrados NO se escanean; revisa que no haya renames implicados.")
        sys.exit(1)

    print("✅ [SECRET-SCAN] Staging limpio: sin secretos por nombre ni por contenido.")
    sys.exit(0)


if __name__ == "__main__":
    main()
