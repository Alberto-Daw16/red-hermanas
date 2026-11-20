#!/usr/bin/env python3
"""Publicar en la red de las hermanas. Sin modelo: solo HTTP a la base de datos.

  publicar.py post      --quien valeria --texto "..." [--imagen f.png] [--encuesta "a|b|c" --horas 24] [--cita ID] [--origen noche]
  publicar.py responder --quien valeria --post ID [--a-comentario ID] --texto "..."
  publicar.py md        --quien valeria --para usuario --texto "..."
  publicar.py like      --quien valeria --post ID
  publicar.py repost    --quien valeria --post ID

Topes (los aplica la base de datos): Valeria 3 posts al día, Shiro 1, Aika 2 a la semana.
Si se pasa del tope sale con código 3 y el mensaje TOPE: no reintentar.
"""
import argparse, os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import red

QUIEN = ["valeria", "shiro", "aika"]


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="accion", required=True)
    def base(n):
        p = sp.add_parser(n); p.add_argument("--quien", required=True, choices=QUIEN)
        p.add_argument("--plataforma", default="x", choices=["x", "ig", "of"]); return p
    p = base("post"); p.add_argument("--texto", default=""); p.add_argument("--imagen")
    p.add_argument("--encuesta"); p.add_argument("--horas", type=int, default=24)
    p.add_argument("--cita", type=int); p.add_argument("--origen", default="chat")
    p.add_argument("--precio", type=float, help="solo OnlyFans: post de pago")
    p = base("responder"); p.add_argument("--post", type=int, required=True); p.add_argument("--a-comentario", type=int); p.add_argument("--texto", required=True)
    p = base("md"); p.add_argument("--para", required=True); p.add_argument("--texto", required=True)
    p = base("like"); p.add_argument("--post", type=int, required=True)
    p = base("repost"); p.add_argument("--post", type=int, required=True)
    a = ap.parse_args()

    yo = red.cuenta(a.quien, a.plataforma)
    try:
        if a.accion == "post":
            if not (a.texto or a.imagen or a.encuesta):
                sys.exit("Falta texto, imagen o encuesta")
            fila = {"cuenta_id": yo["id"], "plataforma": a.plataforma, "texto": a.texto or None, "origen": a.origen}
            if a.imagen:
                fila["imagen_url"] = red.subir_imagen(a.imagen, f"{a.quien}/{int(time.time())}{os.path.splitext(a.imagen)[1] or '.png'}")
            if a.encuesta:
                ops = [o.strip() for o in a.encuesta.split("|") if o.strip()][:4]
                fila["encuesta"] = {"opciones": ops, "votos": [0] * len(ops),
                                    "cierra": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + a.horas * 3600))}
            if a.cita:
                fila.update(repost_de=a.cita, cita=True)
            if a.precio:
                fila.update(de_pago=True, precio=a.precio)
            r = red.ins("posts", fila)[0]
            print(json.dumps({"ok": True, "post": r["id"]}))
        elif a.accion == "responder":
            r = red.ins("comentarios", {"post_id": a.post, "cuenta_id": yo["id"], "responde_a": a.a_comentario, "texto": a.texto, "origen": "hermana"})[0]
            print(json.dumps({"ok": True, "comentario": r["id"]}))
        elif a.accion == "md":
            dest = red.sel("cuentas", plataforma=f"eq.{a.plataforma}", usuario=f"ilike.{a.para.lstrip('@')}", select="id")
            if not dest:
                sys.exit(f"No existe @{a.para} en {a.plataforma}")
            red.ins("mensajes", {"plataforma": a.plataforma, "de": yo["id"], "para": dest[0]["id"], "texto": a.texto, "origen": "hermana"})
            print(json.dumps({"ok": True}))
        elif a.accion == "like":
            red.ins("likes", {"cuenta_id": yo["id"], "post_id": a.post})
            print(json.dumps({"ok": True}))
        elif a.accion == "repost":
            red.ins("posts", {"cuenta_id": yo["id"], "plataforma": a.plataforma, "repost_de": a.post, "origen": "hermana"})
            print(json.dumps({"ok": True}))
    except red.ErrorRed as e:
        if "TOPE" in str(e):
            print(json.dumps({"ok": False, "tope": True, "error": str(e)}))
            sys.exit(3)
        if "duplicate" in str(e) or "23505" in str(e):
            print(json.dumps({"ok": True, "ya_estaba": True}))
            return
        raise


if __name__ == "__main__":
    main()
