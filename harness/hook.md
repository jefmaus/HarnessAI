# Contrato Operativo del Pre-Commit

Este proyecto cuenta con una barrera física de validación configurada en `harness/.githooks/pre-commit`.

Antes de realizar cualquier commit mediante `git commit`, el agente debe tener presente:

1. **Ejecución Determinista Automática:** Git ejecutará automáticamente el runner universal `python harness/scripts/verify.py`. Si el linter detecta problemas de formato, si una sola prueba unitaria falla, o si la compilación se interrumpe en cualquiera de los módulos activos, el commit será rechazado inmediatamente con código de salida `1`.
2. **Prevención de Fuga de Credenciales:** El hook realiza un escaneo estático sobre los archivos en *staging* buscando claves privadas, tokens, certificados o archivos `.env`.
3. **Prohibición Constitucional de Bypass:** Está terminantemente prohibido utilizar el parámetro `--no-verify`. Si el commit es rechazado, el agente debe:
   - Leer atentamente la salida de error del runner.
   - Corregir el código fuente o la prueba correspondiente en el módulo afectado.
   - Re-ejecutar `python harness/scripts/verify.py <modulo>` para confirmar la solución.
   - Reintentar el commit.
