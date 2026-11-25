#!/usr/bin/env python3
"""Recomprime las imágenes que ya están en storage (una vez). Misma ruta, contenido JPEG ligero.
Uso: python3 comprimir_todo.py [--seco]      (--seco: solo cuenta lo que haría)
Usa la clave de servicio del .env, como el resto de scripts. No borra nada: sobrescribe cada archivo con su versión ligera."""
import json, sys, urllib.request
import red

SECO = "--seco" in sys.argv


def listar(bucket, prefijo=""):
    r = red._pedir("POST", f"/storage/v1/object/list/{bucket}", {"prefix": prefijo, "limit": 1000, "offset": 0}) or []
    for o in r:
        ruta = (prefijo + "/" if prefijo else "") + o["name"]
        if o.get("id") is None:          # carpeta
            yield from listar(bucket, ruta)
        else:
            yield ruta, (o.get("metadata") or {}).get("size", 0)


def bajar(bucket, ruta):
    h = {"apikey": red.KEY}
    if not red.KEY.startswith("sb_"):
        h["Authorization"] = f"Bearer {red.KEY}"
    with urllib.request.urlopen(urllib.request.Request(f"{red.URL}/storage/v1/object/{bucket}/{ruta}", headers=h), timeout=60) as r:
        return r.read()


antes = despues = n = 0
for bucket in ("media", "publico"):
    for ruta, tam in list(listar(bucket)):
        if tam and tam < 350_000:
            continue
        datos = bajar(bucket, ruta)
        nuevo, tipo = red.comprimir(datos, ruta, bucket)
        if not tipo:
            continue
        antes += len(datos); despues += len(nuevo); n += 1
        if not SECO:
            red._pedir("PUT", f"/storage/v1/object/{bucket}/{ruta}", nuevo, {"x-upsert": "true"}, crudo=True, tipo=tipo)
        print(f"{bucket}/{ruta}: {len(datos)//1024} KB → {len(nuevo)//1024} KB")
print(f"{'(seco) ' if SECO else ''}{n} imágenes: {antes//1048576} MB → {despues//1048576} MB")
