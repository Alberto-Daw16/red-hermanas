#!/usr/bin/env python3
"""Puente entre tanda.py (MODELO_CMD / config tanda.modelo_cmd) y la CLI de Antigravity (`agy`).

Entrada por stdin:  {"modelo": "<slug de agy models>", "mensajes": [{"role": "system"|"user", "content": "..."}]}
Salida por stdout:  {"texto": "<respuesta>", "usage": {"prompt_tokens": n, "completion_tokens": n, ...}}

- Usa la sesión de Google que se dejó iniciada en `agy` (Google AI Pro). Aquí no hay claves.
- Se ejecuta en una carpeta temporal vacía: el modelo solo tiene que contestar, no tocar archivos.
- Si algo falla, sale con código distinto de 0 y el motivo en stderr (tanda.py repite entonces con Grok).
"""
import json, os, shutil, subprocess, sys, tempfile

AGY = os.environ.get("AGY_BIN") or shutil.which("agy") or os.path.expanduser("~/.local/bin/agy")
LIMITE_S = int(os.environ.get("AGY_LIMITE_S", "900"))


def main():
    pedido = json.load(sys.stdin)
    modelo = pedido.get("modelo") or ""
    partes = []
    for m in pedido.get("mensajes", []):
        if m.get("role") == "system":
            partes.append("=== INSTRUCCIONES (síguelas al pie de la letra) ===\n" + m["content"].strip())
        else:
            partes.append("=== MATERIAL ===\n" + m["content"].strip())
    partes.append("Contesta SOLO con el objeto JSON que piden las instrucciones: sin texto antes ni después, sin ``` y sin usar herramientas.")
    prompt = "\n\n".join(partes)

    cmd = [AGY, "-p", prompt, "--output-format", "json"]
    if modelo:
        cmd += ["--model", modelo]
    if os.environ.get("AGY_EFFORT"):
        cmd += ["--effort", os.environ["AGY_EFFORT"]]
    with tempfile.TemporaryDirectory(prefix="tanda-agy-") as vacia:
        try:
            p = subprocess.run(cmd, cwd=vacia, capture_output=True, text=True, timeout=LIMITE_S)
        except FileNotFoundError:
            sys.exit("agy no está instalado o no está en el PATH (AGY_BIN)")
        except subprocess.TimeoutExpired:
            sys.exit(f"agy tardó más de {LIMITE_S} s")
    sobre = None
    for linea in reversed(p.stdout.strip().splitlines()):
        try:
            sobre = json.loads(linea); break
        except Exception:
            continue
    if p.returncode != 0 or not sobre or sobre.get("status") != "SUCCESS" or not (sobre.get("response") or "").strip():
        motivo = (sobre or {}).get("error") or (sobre or {}).get("status") or p.stderr.strip()[-400:] or f"código {p.returncode}"
        sys.exit(f"agy falló: {motivo}")
    u = sobre.get("usage") or {}
    salida = int(u.get("output_tokens") or 0) + int(u.get("thinking_tokens") or 0)
    json.dump({"texto": sobre["response"], "usage": {
        "prompt_tokens": int(u.get("input_tokens") or 0),
        "completion_tokens": salida,
        "total_tokens": int(u.get("total_tokens") or 0) or int(u.get("input_tokens") or 0) + salida,
        "reasoning_tokens": int(u.get("thinking_tokens") or 0),
        "prompt_tokens_details": {"cached_tokens": int(u.get("cache_read_tokens") or 0)},
    }}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
