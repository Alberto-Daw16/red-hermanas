#!/usr/bin/env python3
"""Resumen corto de lo que ha pasado en las cuentas de una hermana desde la última vez.
Sin modelo. Pensado para leerlo dentro de la tarea de noche o de día que ya existe.

  resumen.py --quien valeria            # imprime y marca como visto
  resumen.py --quien valeria --no-marcar
"""
import argparse, os, sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import red


def hora(iso):
    """Las fechas vienen en UTC; ellas viven en Madrid (si no, Valeria dice «a las once» de un mensaje de las doce y media)."""
    try:
        from zoneinfo import ZoneInfo
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return d.astimezone(ZoneInfo("Europe/Madrid")).strftime("%d/%m %H:%M")
    except Exception:
        return iso[5:16].replace("T", " ")


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
    md_alb = red.sel("mensajes", de=f"in.({ids_alb})", para=f"in.({ids_mias})", leido="eq.false", select="id,de,para,texto,plataforma,creado", order="creado")
    vistos = set()
    for m in md_alb:
        if (m["de"], m["para"]) in vistos:
            continue
        vistos.add((m["de"], m["para"]))
        lineas.append(f"- MD de Alberto ({m['plataforma']}) sin contestar. Vuestra conversación (lo último, abajo):")
        hilo = red.sel("mensajes", **{"or": f"(and(de.eq.{m['de']},para.eq.{m['para']}),and(de.eq.{m['para']},para.eq.{m['de']}))"},
                       select="de,texto,creado", order="creado.desc", limit=12)
        for h in reversed(hilo):
            quien = "Alberto" if h["de"] == m["de"] else "tú"
            lineas.append(f"    {hora(h['creado'])} {quien}: «{corto(h['texto'], 200)}»")
        lineas.append(f"    Contéstale con: publicar.py md --quien {a.quien} --para alberto_16 --texto \"...\" (acuérdate de lo de antes)")
    for c in mias:
        men = red.sel("posts", cuenta_id=f"in.({ids_alb})", texto=f"ilike.*@{c['usuario']}*", creado=f"gt.{desde}", select="id,texto")
        for p in men[:2]:
            lineas.append(f"- Alberto te menciona en el post #{p['id']}: «{corto(p['texto'])}»")
    # Posts de Alberto de los últimos 3 días: no hace falta contestar al momento, pero que no se queden sin respuesta
    hace3 = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    suyos = red.sel("posts", cuenta_id=f"in.({ids_alb})", repost_de="is.null", plataforma="eq.x", creado=f"gt.{hace3}",
                    select="id,texto,imagen_url,creado", order="creado.desc", limit=5)
    sin = []
    for p in suyos:
        mio = red.sel("comentarios", post_id=f"eq.{p['id']}", cuenta_id=f"in.({ids_mias})", select="id", limit=1)
        if not mio:
            sin.append(p)
    if sin:
        lineas.append("- Posts de Alberto que aún no le has contestado (no hace falta hoy; contesta a 1 si te sale algo, como harías tú):")
        for p in sin[:3]:
            lineas.append(f"    #{p['id']} ({hora(p['creado'])}){' [con foto]' if p.get('imagen_url') else ''}: «{corto(p['texto'])}»"
                          f" → publicar.py responder --quien {a.quien} --post {p['id']} --texto \"...\"")
    rp = red.sel("posts", cuenta_id=f"in.({ids_alb})", repost_de=f"in.({pids})", creado=f"gt.{desde}", select="repost_de,cita,texto")
    for r in rp[:2]:
        lineas.append(f"- Alberto ha {'citado' if r['cita'] else 'reposteado'} tu #{r['repost_de']}" + (f": «{corto(r['texto'])}»" if r['cita'] else ""))
    # Nocturna: lo que ha pagado Alberto (dinero de mentira)
    if any(c["plataforma"] == "of" for c in mias):
        ids_of = ",".join(c["id"] for c in mias if c["plataforma"] == "of")
        sus = red.sel("suscripciones", creadora=f"in.({ids_of})", creado=f"gt.{desde}", select="precio")
        if sus:
            lineas.append(f"- Alberto se ha suscrito a tu Nocturna ({sus[0]['precio']} €)")
        des = red.sel("desbloqueos", creado=f"gt.{desde}", select="post_id,mensaje_id,precio")
        for d in des[:4]:
            lineas.append(f"- Alberto ha desbloqueado {'tu post #' + str(d['post_id']) if d['post_id'] else 'un mensaje tuyo de pago'} ({d['precio']} €)")
        tips = red.sel("propinas", para=f"in.({ids_of})", creado=f"gt.{desde}", select="importe,mensaje")
        for t in tips[:4]:
            lineas.append(f"- Alberto te ha dado {t['importe']} € de propina" + (f": «{corto(t['mensaje'])}»" if t.get("mensaje") else ""))
    sg = red.sel("seguimientos", seguidor=f"in.({ids_alb})", seguido=f"in.({ids_mias})", creado=f"gt.{desde}", select="seguido")
    if sg:
        lineas.append("- Alberto ha empezado a seguirte en " + ", ".join(plat[s["seguido"]] for s in sg))

    # Lo más gordo del resto
    otros = red.sel("comentarios", post_id=f"in.({pids})", cuenta_id=f"not.in.({ids_alb},{ids_mias})", creado=f"gt.{desde}",
                    select="id,post_id,cuenta_id,texto,likes_sim", order="likes_sim.desc", limit=60)
    if otros:
        lineas.append(f"- {len(otros)} comentarios nuevos de otra gente en tus posts. Los más sonados (puedes contestar a 2–4 con publicar.py responder):")
        for c in otros[:6]:
            k = cuentas.get(c["cuenta_id"], {})
            lineas.append(f"    @{k.get('usuario')} en #{c['post_id']} (comentario {c['id']}): «{corto(c['texto'], 90)}»")
    md_otros = red.sel("mensajes", para=f"in.({ids_mias})", de=f"not.in.({ids_alb})", leido="eq.false", select="id,de,texto", order="creado.desc", limit=30)
    if md_otros:
        lineas.append(f"- {len(md_otros)} MD sin leer de otra gente, p. ej.: " + "; ".join(f"@{cuentas.get(m['de'], {}).get('usuario')}: «{corto(m['texto'], 60)}»" for m in md_otros[:2]))
    nuevos = red.sel("posts", cuenta_id=f"not.in.({ids_alb},{ids_mias})", texto=f"ilike.*{mias[0]['usuario']}*", creado=f"gt.{desde}", select="id,cuenta_id,texto", limit=3)
    for p in nuevos:
        lineas.append(f"- @{cuentas.get(p['cuenta_id'], {}).get('usuario')} habla de ti en #{p['id']}: «{corto(p['texto'], 90)}»")

    cron = (red.config("cronica", {}) or {}).get("lineas") or []
    if cron:
        lineas.append("- Lo que se mueve en Raven ahora (hilos abiertos; si algo va contigo, puedes reaccionar):")
        for l in cron[:10]:
            lineas.append(f"    {l}")
    print(f"RED · {a.quien} · desde {desde[:16].replace('T', ' ')} UTC")
    print("\n".join(lineas) if lineas else "- Nada nuevo.")
    print("Para contestar: publicar.py responder/md/like (ver SKILL). Si no te apetece, no hace falta.")

    if not a.no_marcar:
        red.upd("estado_hermana", {"visto_hasta": red.ahora_iso()}, quien=f"eq.{a.quien}")
        if md_alb:
            red.upd("mensajes", {"leido": True}, id=f"in.({','.join(str(m['id']) for m in md_alb)})")


if __name__ == "__main__":
    main()
