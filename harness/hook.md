# Contrato Operativo del Pre-Commit

Este proyecto cuenta con una barrera física de validación configurada en `harness/.githooks/pre-commit`.

El hook es un delegador delgado: localiza un intérprete Python disponible (en orden: `VIRTUAL_ENV`, lanzador `py -3` de Windows, `python3`, `python`) y delega dos validaciones deterministas, ambas en Python puro y sin dependencias externas:

1. **Escaneo de Secretos (`harness/scripts/secret-scan.py`):**
   - **Por nombre:** inspecciona el staging buscando archivos sensibles (`.env` y sus variantes, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, pares SSH `id_rsa`/`id_ed25519`/etc.). Se exceptúan deliberadamente las plantillas inofensivas: `.env.example` y las claves públicas `*.pub`.
   - **Por contenido:** revisa únicamente las **líneas añadidas** del diff staged contra patrones de alta señal (bloques `BEGIN ... PRIVATE KEY`, access keys de AWS `AKIA...`, tokens de GitHub `ghp_`/`github_pat_`, tokens de Slack `xox*`). No se usa detección por entropía para evitar falsos positivos.
   - **Los borrados NUNCA se escanean** (`--diff-filter=ACM`): retirar un secreto comprometido con `git rm` debe poder commitearse sin violar la constitución.

2. **Verificación de Calidad (`harness/scripts/verify.py`):** ejecuta linter, compilación/tipado y pruebas de cada módulo registrado en `harness/config.json`. Si algo falla o supera el timeout, el commit se aborta con código `1`.

## Si el commit es rechazado

El uso del parámetro `--no-verify` está **terminantemente vetado** por la Constitución (`AGENTS.md`). El agente debe:

1. Leer el mensaje del error (el scanner indica **qué archivo** y **qué patrón** detectó, jamás imprime el secreto; `verify.py` indica el módulo y el paso fallido).
2. Si es un secreto: sacarlo del staging (`git restore --staged <archivo>`) y eliminarlo del contenido. Nunca imprimir el valor detectado en el chat.
3. Si es un fallo de verificación: corregir el código o la prueba en el módulo afectado.
4. Re-ejecutar `python harness/scripts/verify.py <modulo>` para confirmar la solución.
5. Reintentar el commit.

> **Ventana de emergencia:** si necesitas retirar un secreto ya commiteado, `git rm` funciona porque los borrados no se escanean. Para purgar el valor del historial completo, usa una herramienta de reescritura de historia (`git filter-repo`) en coordinación con el usuario, y rota la credencial comprometida de inmediato.
