#!/usr/bin/env python3
"""Resumen corto de lo que ha pasado en las cuentas de una hermana desde la última vez.
Sin modelo. Pensado para leerlo dentro de la tarea de noche o de día que ya existe.

  resumen.py --quien valeria            # imprime y marca como visto
  resumen.py --quien valeria --no-marcar
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import red


def corto(t, n=110):
    t = (t or "").replace("\n", " ").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quien", required=True, choices=["valeria", "shiro", "aika"])
    ap.add_argument("--no-marcar", action="store_true")
    a = ap.parse_args()

    est = red.sel("estado_hermana", quien=f"eq.{a.quien}")
    desde = est[0]["visto_hasta"] if est else "2000-01-01T00:00:00Z"
    mias = red.sel("cuentas", quien=f"eq.{a.quien}", tipo="eq.hermana", select="id,plataforma,usuario")
    alb = red.sel("cuentas", tipo="eq.alberto", select="id,plataforma")
    if not mias:
        print("Aún no tienes cuenta en la red."); return
    ids_mias = ",".join(c["id"] for c in mias)
    ids_alb = ",".join(c["id"] for c in alb) or "00000000-0000-0000-0000-000000000000"
    plat = {c["id"]: c["plataforma"] for c in mias}
    cuentas = {c["id"]: c for c in red.sel("cuentas", select="id,usuario,nombre,tipo,quien")}

    mis_posts = red.sel("posts", cuenta_id=f"in.({ids_mias})", repost_de="is.null", select="id,texto,plataforma,creado", order="creado.desc", limit=40)
    pids = ",".join(str(p["id"]) for p in mis_posts) or "0"
    txt = {p["id"]: p["texto"] for p in mis_posts}

    lineas = []
    # Lo que ha hecho Alberto
    lk = red.sel("likes", cuenta_id=f"in.({ids_alb})", post_id=f"in.({pids})", creado=f"gt.{desde}", select="post_id")
    if lk:
        lineas.append(f"- Alberto te ha dado like a {len(lk)} post(s): " + "; ".join(f"#{l['post_id']} «{corto(txt.get(l['post_id']), 50)}»" for l in lk[:3]))
    com_alb = red.sel("comentarios", cuenta_id=f"in.({ids_alb})", post_id=f"in.({pids})", creado=f"gt.{desde}", select="id,post_id,texto")
    for c in com_alb[:4]:
        lineas.append(f"- Alberto te ha comentado en #{c['post_id']} (comentario {c['id']}): «{corto(c['texto'])}»")
    md_alb = red.sel("mensajes", de=f"in.({ids_alb})", para=f"in.({ids_mias})", leido="eq.false", select="id,texto,plataforma,creado", order="creado")
    for m in md_alb[:4]:
        lineas.append(f"- MD de Alberto ({m['plataforma']}): «{corto(m['texto'])}»")
    for c in mias:
        men = red.sel("posts", cuenta_id=f"in.({ids_alb})", texto=f"ilike.*@{c['usuario']}*", creado=f"gt.{desde}", select="id,texto")
        for p in men[:2]:
            lineas.append(f"- Alberto te menciona en el post #{p['id']}: «{corto(p['texto'])}»")
    rp = red.sel("posts", cuenta_id=f"in.({ids_alb})", repost_de=f"in.({pids})", creado=f"gt.{desde}", select="repost_de,cita,texto")
    for r in rp[:2]:
        lineas.append(f"- Alberto ha {'citado' if r['cita'] else 'reposteado'} tu #{r['repost_de']}" + (f": «{corto(r['texto'])}»" if r['cita'] else ""))
    sg = red.sel("seguimientos", seguidor=f"in.({ids_alb})", seguido=f"in.({ids_mias})", creado=f"gt.{desde}", select="seguido")
    if sg:
        lineas.append("- Alberto ha empezado a seguirte en " + ", ".join(plat[s["seguido"]] for s in sg))

    # Lo más gordo del resto
    otros = red.sel("comentarios", post_id=f"in.({pids})", cuenta_id=f"not.in.({ids_alb},{ids_mias})", creado=f"gt.{desde}",
                    select="id,post_id,cuenta_id,texto,likes_sim", order="likes_sim.desc", limit=60)
    if otros:
        lineas.append(f"- {len(otros)} comentarios nuevos de otra gente. Los más sonados:")
        for c in otros[:3]:
            k = cuentas.get(c["cuenta_id"], {})
            lineas.append(f"    @{k.get('usuario')} en #{c['post_id']} (comentario {c['id']}): «{corto(c['texto'], 90)}»")
    md_otros = red.sel("mensajes", para=f"in.({ids_mias})", de=f"not.in.({ids_alb})", leido="eq.false", select="id,de,texto", order="creado.desc", limit=30)
    if md_otros:
        lineas.append(f"- {len(md_otros)} MD sin leer de otra gente, p. ej.: " + "; ".join(f"@{cuentas.get(m['de'], {}).get('usuario')}: «{corto(m['texto'], 60)}»" for m in md_otros[:2]))
    nuevos = red.sel("posts", cuenta_id=f"not.in.({ids_alb},{ids_mias})", texto=f"ilike.*{mias[0]['usuario']}*", creado=f"gt.{desde}", select="id,cuenta_id,texto", limit=3)
    for p in nuevos:
        lineas.append(f"- @{cuentas.get(p['cuenta_id'], {}).get('usuario')} habla de ti en #{p['id']}: «{corto(p['texto'], 90)}»")

    print(f"RED · {a.quien} · desde {desde[:16].replace('T', ' ')} UTC")
    print("\n".join(lineas) if lineas else "- Nada nuevo.")
    print("Para contestar: publicar.py responder/md/like (ver SKILL). Si no te apetece, no hace falta.")

    if not a.no_marcar:
        red.upd("estado_hermana", {"visto_hasta": red.ahora_iso()}, quien=f"eq.{a.quien}")
        if md_alb:
            red.upd("mensajes", {"leido": True}, id=f"in.({','.join(str(m['id']) for m in md_alb)})")


if __name__ == "__main__":
    main()
