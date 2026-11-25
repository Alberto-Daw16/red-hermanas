#!/usr/bin/env python3
"""Captura de pantalla REAL de Raven para que una hermana se la pase a Alberto (en vez de inventarse la imagen).

  captura.py post 130                     # un post con sus respuestas
  captura.py perfil veenoir               # cabecera del perfil y sus últimos posts
  captura.py md valeria [--con alberto_16] [--n 12]   # su conversación por MD
  … [--salida ruta.png]

Saca los datos de la base (con la clave del .env, sin login), monta una página con el aspecto de Raven
y la fotografía con Chrome/Chromium en modo headless. Imprime la ruta del PNG.
Sin modelo y sin escribir nada en la red.
"""
import argparse, html, json, os, re, shutil, subprocess, sys, tempfile, time
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import red

ANCHO = 393
NAVEGADORES = [
    os.environ.get("CHROME_BIN", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("chromium") or "", shutil.which("google-chrome") or "",
]
COLORES = ["#c2185b", "#7b1fa2", "#512da8", "#1976d2", "#0097a7", "#388e3c", "#f57c00", "#5d4037", "#455a64", "#d81b60"]

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000;color:#e7e9ea;font:15px/1.35 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,Helvetica,Arial,sans-serif;width:%dpx}
.bar{display:flex;align-items:center;gap:22px;padding:12px 16px;border-bottom:1px solid #2f3336;font-weight:800;font-size:19px}
.bar small{display:block;font-size:13px;color:#71767b;font-weight:400}
.post{display:flex;gap:10px;padding:12px 16px;border-bottom:1px solid #2f3336}
.det{padding:12px 16px;border-bottom:1px solid #2f3336}
.av{width:40px;height:40px;border-radius:50%%;flex:none;display:grid;place-items:center;font-weight:700;color:#fff;overflow:hidden;background-size:cover;background-position:center}
.av.g{width:48px;height:48px}
.cab{display:flex;gap:4px;align-items:baseline;flex-wrap:wrap}
.n{font-weight:700}.u,.t{color:#71767b}
.tx{margin-top:2px;white-space:pre-wrap;word-wrap:break-word}
.det .tx{font-size:17px;margin-top:12px}
.img{margin-top:10px;border-radius:16px;border:1px solid #2f3336;width:100%%;max-height:420px;object-fit:cover;display:block}
.cif{display:flex;gap:18px;color:#71767b;font-size:13px;margin-top:10px}
.cif b{color:#e7e9ea}
.resp{color:#71767b;font-size:13px}
.ban{height:130px;background:#333 center/cover}
.pf{padding:0 16px 12px;border-bottom:1px solid #2f3336}
.pf .av{width:80px;height:80px;border:4px solid #000;margin-top:-40px;font-size:30px}
.pf .n{font-size:20px;font-weight:800;margin-top:6px}
.bio{margin-top:8px}
.seg{margin-top:8px;color:#71767b;font-size:14px}.seg b{color:#e7e9ea}
.chat{padding:12px 12px 18px;display:flex;flex-direction:column;gap:6px}
.msg{max-width:78%%;padding:9px 13px;border-radius:20px;white-space:pre-wrap;word-wrap:break-word}
.yo{align-self:flex-end;background:#ff3d8b;color:#fff;border-bottom-right-radius:6px}
.el{align-self:flex-start;background:#2f3336;border-bottom-left-radius:6px}
.hora{align-self:center;color:#71767b;font-size:12px;margin:6px 0}
.msg img{display:block;max-width:100%%;border-radius:14px;margin-bottom:4px}
.verif{color:#ff3d8b;font-size:14px}
""" % ANCHO


def esc(t):
    return html.escape(str(t or ""))


def firmar(rutas):
    """URLs firmadas (1 h) de las imágenes del bucket privado."""
    out = {}
    for r in {x for x in rutas if x}:
        if r.startswith("http"):
            out[r] = r; continue
        try:
            res = red._pedir("POST", f"/storage/v1/object/sign/media/{r}", {"expiresIn": 3600})
            out[r] = red.URL + "/storage/v1" + res["signedURL"]
        except Exception:
            pass
    return out


def avatar(c, urls, cls="av"):
    url = urls.get(c.get("avatar_url") or "")
    if url:
        return f'<div class="{cls}" style="background-image:url(\'{esc(url)}\')"></div>'
    color = COLORES[sum(map(ord, c.get("usuario", "x"))) % len(COLORES)]
    return f'<div class="{cls}" style="background:{color}">{esc((c.get("nombre") or "?")[:1].upper())}</div>'


def hace(f):
    try:
        s = (datetime.now(timezone.utc) - datetime.fromisoformat(f.replace("Z", "+00:00"))).total_seconds()
    except Exception:
        return ""
    if s < 60: return "ahora"
    if s < 3600: return f"{int(s // 60)} min"
    if s < 86400: return f"{int(s // 3600)} h"
    return f"{int(s // 86400)} d"


def num(n):
    n = int(n or 0)
    return f"{n / 1000:.1f} mil".replace(".0 mil", " mil").replace(".", ",") if n >= 10000 else f"{n:,}".replace(",", ".")


def ahora():
    return red.ahora_iso()


def cuentas_por_id(ids):
    ids = [i for i in set(ids) if i]
    if not ids:
        return {}
    return {c["id"]: c for c in red.sel("cuentas", id=f"in.({','.join(ids)})", select="id,tipo,nombre,usuario,avatar_url,banner_url,bio,seguidores,siguiendo,verificada")}


def pag_post(pid):
    p = red.sel("posts", id=f"eq.{pid}", creado=f"lte.{ahora()}", select="*")
    if not p:
        sys.exit(f"No existe el post {pid} (o aún no ha salido)")
    p = p[0]
    coms = red.sel("comentarios", post_id=f"eq.{pid}", creado=f"lte.{ahora()}", select="*", order="creado.asc", limit=12)
    cu = cuentas_por_id([p["cuenta_id"]] + [c["cuenta_id"] for c in coms])
    urls = firmar([c.get("avatar_url") for c in cu.values()] + [p.get("imagen_url")])
    a = cu[p["cuenta_id"]]
    img = f'<img class="img" src="{esc(urls[p["imagen_url"]])}">' if p.get("imagen_url") in urls else ""
    h = [f'<div class="bar">←<div>Post</div></div><div class="det"><div style="display:flex;gap:10px;align-items:center">{avatar(a, urls)}'
         f'<div><div class="n">{esc(a["nombre"])}</div><div class="u">@{esc(a["usuario"])}</div></div></div>'
         f'<div class="tx">{esc(p.get("texto"))}</div>{img}'
         f'<div class="cif"><span><b>{num(p.get("reposts_sim"))}</b> reposts</span><span><b>{num(p.get("likes_sim"))}</b> me gusta</span>'
         f'<span><b>{num(p.get("vistas_sim"))}</b> vistas</span></div></div>']
    por_id = {c["id"]: c for c in coms}
    for c in coms:
        k = cu.get(c["cuenta_id"], {})
        padre = por_id.get(c.get("responde_a"))
        a_quien = cu.get(padre["cuenta_id"], {}).get("usuario") if padre else a["usuario"]
        h.append(f'<div class="post">{avatar(k, urls)}<div><div class="cab"><span class="n">{esc(k.get("nombre"))}</span>'
                 f'<span class="u">@{esc(k.get("usuario"))} · {hace(c["creado"])}</span></div>'
                 f'<div class="resp">Respondiendo a @{esc(a_quien)}</div><div class="tx">{esc(c["texto"])}</div></div></div>')
    return "".join(h)


def pag_perfil(usuario):
    c = red.sel("cuentas", usuario=f"eq.{usuario}", plataforma="eq.x", select="*")
    if not c:
        sys.exit(f"No existe @{usuario} en Raven")
    c = c[0]
    posts = red.sel("posts", cuenta_id=f"eq.{c['id']}", creado=f"lte.{ahora()}", texto="not.is.null", select="*", order="creado.desc", limit=4)
    urls = firmar([c.get("avatar_url"), c.get("banner_url")] + [p.get("imagen_url") for p in posts])
    ban = f' style="background-image:url(\'{esc(urls[c["banner_url"]])}\')"' if c.get("banner_url") in urls else ""
    h = [f'<div class="bar">←<div>{esc(c["nombre"])}<small>{len(posts)} posts recientes</small></div></div><div class="ban"{ban}></div>'
         f'<div class="pf">{avatar(c, urls, "av g")}<div class="n">{esc(c["nombre"])}{" 🔒" if c.get("privada") else ""}</div>'
         f'<div class="u">@{esc(c["usuario"])}</div><div class="bio">{esc(c.get("bio"))}</div>'
         f'<div class="seg"><b>{num(c.get("siguiendo"))}</b> siguiendo &nbsp; <b>{num(c.get("seguidores"))}</b> seguidores</div></div>']
    for p in posts:
        img = f'<img class="img" src="{esc(urls[p["imagen_url"]])}">' if p.get("imagen_url") in urls else ""
        h.append(f'<div class="post">{avatar(c, urls)}<div style="flex:1"><div class="cab"><span class="n">{esc(c["nombre"])}</span>'
                 f'<span class="u">@{esc(c["usuario"])} · {hace(p["creado"])}</span></div><div class="tx">{esc(p["texto"])}</div>{img}'
                 f'<div class="cif"><span>♥ {num(p.get("likes_sim"))}</span><span>⟲ {num(p.get("reposts_sim"))}</span></div></div></div>')
    return "".join(h)


def pag_md(quien, con, n):
    yo = red.sel("cuentas", quien=f"eq.{quien}", tipo="eq.hermana", plataforma="eq.x", select="id")
    otro = red.sel("cuentas", usuario=f"eq.{con}", plataforma="eq.x", select="*")
    if not yo or not otro:
        sys.exit("No encuentro una de las dos cuentas")
    a, b = yo[0]["id"], otro[0]["id"]
    msgs = red.sel("mensajes", **{"or": f"(and(de.eq.{a},para.eq.{b}),and(de.eq.{b},para.eq.{a}))"}, creado=f"lte.{ahora()}",
                   select="de,texto,imagen_url,creado", order="creado.desc", limit=n)[::-1]
    o = otro[0]
    urls = firmar([o.get("avatar_url")] + [m.get("imagen_url") for m in msgs])
    h = [f'<div class="bar">←{avatar(o, urls)}<div>{esc(o["nombre"])}<small>@{esc(o["usuario"])}</small></div></div><div class="chat">']
    ultimo = ""
    for m in msgs:
        dia = m["creado"][:10]
        if dia != ultimo:
            h.append(f'<div class="hora">{dia[8:10]}/{dia[5:7]} · {m["creado"][11:16]}</div>'); ultimo = dia
        img = f'<img src="{esc(urls[m["imagen_url"]])}">' if m.get("imagen_url") in urls else ""
        h.append(f'<div class="msg {"yo" if m["de"] == a else "el"}">{img}{esc(m.get("texto"))}</div>')
    h.append("</div>")
    return "".join(h)


def fotografiar(cuerpo, salida):
    nav = next((n for n in NAVEGADORES if n and os.path.exists(n)), None)
    if not nav:
        sys.exit("No hay Chrome/Chromium para hacer la captura (CHROME_BIN)")
    with tempfile.TemporaryDirectory(prefix="captura-") as d:
        pag = os.path.join(d, "p.html")
        open(pag, "w", encoding="utf-8").write(f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><body>{cuerpo}</body>')
        alto = 1400
        subprocess.run([nav, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={d}/perfil",
                        "--force-device-scale-factor=3", f"--window-size={ANCHO},{alto}", "--virtual-time-budget=8000",
                        f"--screenshot={salida}", "file://" + pag], capture_output=True, timeout=90)
    if not os.path.exists(salida):
        sys.exit("El navegador no generó la captura")
    try:  # recorta el negro sobrante de abajo si hay Pillow
        from PIL import Image, ImageChops
        im = Image.open(salida).convert("RGB")
        caja = ImageChops.difference(im, Image.new("RGB", im.size, (0, 0, 0))).getbbox()
        if caja:
            im.crop((0, 0, im.width, min(im.height, caja[3] + 30))).save(salida)
    except Exception:
        pass
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tipo", choices=["post", "perfil", "md"])
    ap.add_argument("que", help="id del post, @usuario del perfil, o la hermana (valeria/shiro/aika) en md")
    ap.add_argument("--con", default="alberto_16", help="con quién es la conversación (md)")
    ap.add_argument("--n", type=int, default=12, help="mensajes que salen (md)")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    if a.tipo == "post":
        cuerpo = pag_post(int(a.que))
    elif a.tipo == "perfil":
        cuerpo = pag_perfil(a.que.lstrip("@"))
    else:
        cuerpo = pag_md(a.que, a.con.lstrip("@"), a.n)
    limpio = re.sub(r"\W", "", a.que)
    salida = a.salida or os.path.join(tempfile.gettempdir(), "raven-%s-%s-%d.png" % (a.tipo, limpio, int(time.time())))
    print(fotografiar(cuerpo, salida))


if __name__ == "__main__":
    main()
