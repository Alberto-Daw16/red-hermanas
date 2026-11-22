#!/usr/bin/env python3
"""Genera las imágenes pendientes de la red (avatares, banners y fotos de posts) y las enlaza.

La cola está en la tabla `imagenes`, la llenan la semilla y la tanda. Este script NO llama a ningún
modelo de texto: solo genera imágenes, como mucho `config.imagenes.max_por_ronda` por ejecución.

  imagenes.py            # una ronda
  imagenes.py --prueba   # enseña lo que haría, sin generar

Cómo se genera cada imagen (por orden):
1) IMAGEN_CMD (en ~/.hermes/red-social.env): un comando que recibe por stdin
   {"prompt": "...", "tamano": "1024x1024", "referencia": "/ruta/hoja.jpg" | null, "salida": "/tmp/x.png"}
   y deja el PNG en "salida" (código 0 = bien). Aquí se engancha gpt-image-2 como lo hace escenas-hermanas.
2) Si no hay IMAGEN_CMD pero sí OPENAI_API_KEY, la API de imágenes de OpenAI (modelo IMAGEN_MODELO, por defecto gpt-image-2).
Dos errores seguidos y para la ronda. Nunca reintenta en bucle.
"""
import argparse, base64, json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import red

REFS = os.path.expanduser(os.environ.get("REFS_DIR", "~/.hermes/profiles/valeria/projects/four-girls-director-v1/references/canonical"))
TAMANO = {"avatar": "1024x1024", "banner": "1536x1024", "post": "1024x1024", "md": "1024x1536"}
ESTILO = " No text, no watermark, no logos of real brands."


def referencia(nombre):
    if not nombre:
        return None
    for ext in ("jpg", "png", "jpeg", "webp"):
        f = os.path.join(REFS, f"{nombre}_reference_sheet.{ext}")
        if os.path.exists(f):
            return f
    return None


def generar(prompt, tamano, ref, salida):
    cmd = os.environ.get("IMAGEN_CMD")
    if cmd:
        p = subprocess.run(cmd, shell=True, input=json.dumps({"prompt": prompt, "tamano": tamano, "referencia": ref, "salida": salida}),
                           capture_output=True, text=True, timeout=600)
        if p.returncode != 0 or not os.path.exists(salida):
            raise RuntimeError(f"IMAGEN_CMD falló: {(p.stderr or p.stdout)[-400:]}")
        return
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("No hay IMAGEN_CMD ni OPENAI_API_KEY en el .env")
    modelo = os.environ.get("IMAGEN_MODELO", "gpt-image-2")
    if ref:
        # edición con la hoja de referencia (multipart)
        limite = "----redhermanas" + str(int(time.time()))
        partes = []
        def campo(n, v):
            partes.append(f"--{limite}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
        campo("model", modelo); campo("prompt", prompt); campo("size", tamano)
        with open(ref, "rb") as f:
            partes.append(f"--{limite}\r\nContent-Disposition: form-data; name=\"image[]\"; filename=\"ref.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode() + f.read() + b"\r\n")
        partes.append(f"--{limite}--\r\n".encode())
        req = urllib.request.Request("https://api.openai.com/v1/images/edits", data=b"".join(partes), method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={limite}"})
    else:
        req = urllib.request.Request("https://api.openai.com/v1/images/generations", method="POST",
                                     data=json.dumps({"model": modelo, "prompt": prompt, "size": tamano}).encode(),
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"OpenAI {e.code}: {e.read().decode(errors='replace')[:300]}") from None
    with open(salida, "wb") as f:
        f.write(base64.b64decode(d["data"][0]["b64_json"]))


def enlazar(item, ruta):
    if item["tipo"] in ("avatar", "banner") and item.get("cuenta_id"):
        red.upd("cuentas", {f"{item['tipo']}_url": ruta}, id=f"eq.{item['cuenta_id']}")
    elif item["tipo"] == "post" and item.get("post_id"):
        red.upd("posts", {"imagen_url": ruta}, id=f"eq.{item['post_id']}")
    elif item["tipo"] == "md" and item.get("mensaje_id"):
        red.upd("mensajes", {"imagen_url": ruta}, id=f"eq.{item['mensaje_id']}")


def copiar_a_nocturna():
    """Las creadoras usan en Nocturna el mismo avatar y banner que en Cuervo si allí no tienen."""
    xs = {c["quien"]: c for c in red.sel("cuentas", plataforma="eq.x", quien="like.creadora_*", select="quien,avatar_url,banner_url")}
    for c in red.sel("cuentas", plataforma="eq.of", quien="like.creadora_*", select="id,quien,avatar_url,banner_url"):
        x = xs.get(c["quien"]) or {}
        cambios = {k: x[k] for k in ("avatar_url", "banner_url") if not c.get(k) and x.get(k)}
        if cambios:
            red.upd("cuentas", cambios, id=f"eq.{c['id']}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--prueba", action="store_true"); a = ap.parse_args()
    cfg = red.config("imagenes", {}) or {}
    if cfg.get("activa") is False and not a.prueba:
        print("Imágenes paradas en config."); return
    lote = red.sel("imagenes", estado="eq.pendiente", select="*", order="creado.asc", limit=int(cfg.get("max_por_ronda", 8)))
    if not lote:
        print("Nada pendiente."); copiar_a_nocturna(); return
    seguidos = 0
    for it in lote:
        ref = referencia(it.get("referencia"))
        if it.get("referencia") and not ref:
            red.upd("imagenes", {"estado": "saltada", "error": f"sin hoja de referencia de {it['referencia']} en {REFS}"}, id=f"eq.{it['id']}")
            print(f"#{it['id']} saltada: falta la hoja de {it['referencia']}"); continue
        tam = TAMANO.get(it["tipo"], "1024x1024")
        if a.prueba:
            print(f"#{it['id']} {it['tipo']} {tam} ref={bool(ref)} · {it['prompt'][:90]}"); continue
        t0 = time.time()
        try:
            with tempfile.TemporaryDirectory() as d:
                salida = os.path.join(d, "img.png")
                generar(it["prompt"] + ESTILO, tam, ref, salida)
                ruta = red.subir_imagen(salida, f"gen/{it['tipo']}-{it['id']}.png")
            enlazar(it, ruta)
            red.upd("imagenes", {"estado": "hecha", "ruta": ruta, "hecha": red.ahora_iso(), "error": None}, id=f"eq.{it['id']}")
            red.apuntar_consumo(quien="imagenes", para=f"imagen:{it['tipo']}", modelo=os.environ.get("IMAGEN_MODELO", "gpt-image-2"),
                                duracion_ms=int((time.time() - t0) * 1000), nota=it["prompt"][:120])
            print(f"#{it['id']} hecha → {ruta}"); seguidos = 0
        except Exception as e:
            seguidos += 1
            red.upd("imagenes", {"estado": "error", "error": str(e)[:400]}, id=f"eq.{it['id']}")
            red.apuntar_consumo(quien="imagenes", para=f"imagen:{it['tipo']}", modelo="gpt-image-2",
                                duracion_ms=int((time.time() - t0) * 1000), error=str(e)[:400])
            print(f"#{it['id']} ERROR: {e}", file=sys.stderr)
            if seguidos >= 2:
                print("Dos errores seguidos: paro la ronda.", file=sys.stderr); break
    copiar_a_nocturna()


if __name__ == "__main__":
    main()
