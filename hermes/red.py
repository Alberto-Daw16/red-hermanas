"""Acceso a la base de datos de la red social de las hermanas (Supabase, API REST).

Solo librería estándar. La configuración se lee de ~/.hermes/red-social.env
(o de la ruta en la variable RED_ENV):

    SUPABASE_URL=https://wtxiqvzercgharibvubw.supabase.co
    SUPABASE_SERVICE_KEY=...   # clave secreta (service_role). Nunca en un chat ni en el repo.
    XAI_API_KEY=...            # opcional: si no está, tanda.py busca el token de xai-oauth de Hermes

Ningún script de esta carpeta llama a un modelo salvo tanda.py.
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

ENV = os.environ.get("RED_ENV", os.path.expanduser("~/.hermes/red-social.env"))


def _cargar_env():
    if os.path.exists(ENV):
        for linea in open(ENV, encoding="utf-8"):
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_cargar_env()
URL = os.environ.get("SUPABASE_URL", "https://wtxiqvzercgharibvubw.supabase.co").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


class ErrorRed(Exception):
    pass


def _pedir(metodo, ruta, cuerpo=None, cabeceras=None, crudo=False, tipo="application/json"):
    if not KEY:
        raise ErrorRed(f"Falta SUPABASE_SERVICE_KEY en {ENV}")
    h = {"apikey": KEY}
    if not KEY.startswith("sb_"):  # la service_role antigua (JWT) va también como Bearer; las sb_secret_ no
        h["Authorization"] = f"Bearer {KEY}"
    if cuerpo is not None and not crudo:
        cuerpo = json.dumps(cuerpo).encode()
    if cuerpo is not None:
        h["Content-Type"] = tipo
    h.update(cabeceras or {})
    req = urllib.request.Request(URL + ruta, data=cuerpo, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else None
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        try:
            msg = json.loads(msg).get("message", msg)
        except Exception:
            pass
        raise ErrorRed(f"{e.code} {msg}") from None


def sel(tabla, **filtros):
    """sel('cuentas', quien='eq.valeria', select='*', order='creado.desc', limit=5)"""
    return _pedir("GET", f"/rest/v1/{tabla}?" + urllib.parse.urlencode(filtros))


def ins(tabla, filas):
    return _pedir("POST", f"/rest/v1/{tabla}", filas, {"Prefer": "return=representation"})


def upd(tabla, cambios, **filtros):
    return _pedir("PATCH", f"/rest/v1/{tabla}?" + urllib.parse.urlencode(filtros), cambios, {"Prefer": "return=representation"})


def config(clave, defecto=None):
    r = sel("config", clave=f"eq.{clave}", select="valor")
    return r[0]["valor"] if r else defecto


def poner_config(clave, valor):
    return _pedir("POST", "/rest/v1/config", {"clave": clave, "valor": valor},
                  {"Prefer": "resolution=merge-duplicates,return=representation"})


def lado_max(destino):
    """Tamaño al que se sirve cada imagen: un avatar se ve a 40 px, no hace falta subir 1024."""
    d = destino.lower()
    if "icono" in d:
        return 320
    if "avatar" in d:
        return 720  # se abre en grande al tocar la foto de perfil
    if "banner" in d:
        return 1500
    return 1280


def comprimir(datos, destino, bucket="media"):
    """Devuelve (bytes, tipo) más ligeros: WebP calidad 90 y como mucho lado_max px.
    Los iconos del bucket público se quedan en PNG (transparencia). Si no hay Pillow, se sube tal cual."""
    try:
        from PIL import Image
        import io
    except ImportError:
        return datos, None
    try:
        im = Image.open(io.BytesIO(datos))
        im.load()
    except Exception:
        return datos, None
    lado = lado_max(destino)
    if max(im.size) > lado:
        im.thumbnail((lado, lado), Image.LANCZOS)
    out = io.BytesIO()
    if bucket == "publico":
        im.save(out, "PNG", optimize=True)
        tipo = "image/png"
    else:
        if im.mode in ("RGBA", "LA", "P"):
            fondo = Image.new("RGB", im.size, (0, 0, 0))
            im = im.convert("RGBA")
            fondo.paste(im, mask=im.split()[-1])
            im = fondo
        elif im.mode != "RGB":
            im = im.convert("RGB")
        # WebP: el anime (colores planos y líneas) con JPEG se llena de manchas al ampliar; WebP 90 queda limpio y pesa poco
        im.save(out, "WEBP", quality=90, method=6)
        tipo = "image/webp"
    nuevo = out.getvalue()
    return (nuevo, tipo) if len(nuevo) < len(datos) else (datos, None)


def subir_imagen(ruta_local, destino, bucket="media"):
    """Sube a storage (bucket privado 'media', o 'publico' para los iconos) y devuelve la ruta.
    Antes la comprime (JPEG ligero): los PNG de 1,6 MB hacían que Raven fuera a tirones en el móvil."""
    ext = os.path.splitext(ruta_local)[1].lower().lstrip(".") or "png"
    tipo = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/png")
    with open(ruta_local, "rb") as f:
        datos = f.read()
    datos, tipo_nuevo = comprimir(datos, destino, bucket)
    _pedir("POST", f"/storage/v1/object/{bucket}/{destino}", datos, {"x-upsert": "true"}, crudo=True, tipo=tipo_nuevo or tipo)
    return destino


def cuenta(quien, plataforma="x"):
    r = sel("cuentas", quien=f"eq.{quien}", plataforma=f"eq.{plataforma}", select="*")
    if not r:
        raise ErrorRed(f"No hay cuenta de '{quien}' en {plataforma}")
    return r[0]


def apuntar_consumo(**kw):
    """Cada llamada a un modelo de la red se apunta aquí (tabla consumo)."""
    try:
        ins("consumo", kw)
    except Exception as e:  # que apuntar nunca tumbe el trabajo
        print(f"[aviso] no se pudo apuntar el consumo: {e}", file=sys.stderr)


def ahora_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
