#!/usr/bin/env python3
"""Ajustes de la red sin modelo.

  ajustes.py nombre "Nombre de la red"              # lo elige Valeria
  ajustes.py cuenta --quien rival --nombre "..." --usuario "..." [--bio "..."] [--personalidad "..."] [--seguidores N]
  ajustes.py tanda [--tope 150000] [--modelo grok-4.7] [--max-posts 12] [--activa si|no]
  ajustes.py ver                                    # config actual y cuentas fijas
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import red

ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="q", required=True)
p = sp.add_parser("nombre"); p.add_argument("valor")
p = sp.add_parser("cuenta"); p.add_argument("--quien", required=True); p.add_argument("--plataforma", default="x")
for k in ("nombre", "usuario", "bio", "personalidad", "ubicacion"):
    p.add_argument("--" + k)
p.add_argument("--seguidores", type=int)
p = sp.add_parser("tanda"); p.add_argument("--tope", type=int); p.add_argument("--modelo"); p.add_argument("--max-posts", type=int); p.add_argument("--activa", choices=["si", "no"])
sp.add_parser("ver")
a = ap.parse_args()

if a.q == "nombre":
    red.poner_config("nombre_red", a.valor); print("ok")
elif a.q == "cuenta":
    cambios = {k: getattr(a, k) for k in ("nombre", "usuario", "bio", "personalidad", "ubicacion", "seguidores") if getattr(a, k) is not None}
    r = red.upd("cuentas", cambios, quien=f"eq.{a.quien}", plataforma=f"eq.{a.plataforma}")
    print(json.dumps([{"usuario": x["usuario"], "nombre": x["nombre"]} for x in r], ensure_ascii=False))
elif a.q == "tanda":
    c = red.config("tanda", {}) or {}
    if a.tope: c["tope_diario_tokens"] = a.tope
    if a.modelo: c["modelo"] = a.modelo
    if a.max_posts: c["max_posts_por_tanda"] = a.max_posts
    if a.activa: c["activa"] = a.activa == "si"
    red.poner_config("tanda", c); print(json.dumps(c))
else:
    for f in red.sel("config", select="*"):
        print(f["clave"], "=", json.dumps(f["valor"], ensure_ascii=False))
    for c in red.sel("cuentas", tipo="in.(hermana,alberto,fijo,marca)", select="quien,plataforma,usuario,nombre", order="tipo"):
        print(f"  {c['quien']:<18} {c['plataforma']}  @{c['usuario']}  ({c['nombre']})")
