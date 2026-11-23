#!/usr/bin/env python3
"""Tanda de reacciones: la gente simulada (amigos, rival, hater, fans, marcas) reacciona
de golpe a lo nuevo de la red. UNA sola llamada al modelo por tanda, y se apunta en `consumo`.

  tanda.py              # la tanda normal (la lanza la tarea programada, 2 veces al día)
  tanda.py --prueba     # monta el prompt y lo imprime con su tamaño, SIN llamar al modelo
  tanda.py --sin-guardar  # llama al modelo e imprime lo que haría, sin escribir en la red

Reglas de gasto:
- Si hoy ya se ha pasado el tope diario (config 'tanda'.tope_diario_tokens), no llama: apunta
  una fila 'saltada' y sale.
- Si las hermanas no han publicado nada, hace una tanda de ambiente (solo gente random, famosos, marcas y creadoras). Se apaga con config tanda.ambiente = false.
- Si el modelo falla, apunta el error y sale. Nunca reintenta.
"""
import argparse, glob, json, os, random, re, subprocess, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import red

PLAT = "x"
REGLAS = """Eres el motor de una red social FALSA y privada (tipo X/Twitter) donde solo entra un usuario real, Alberto.
Generas en una sola respuesta cómo reacciona la gente simulada a lo nuevo. Todo es ficción.

Reglas fijas:
- Español de España, como se escribe en X de verdad: corto, minúsculas frecuentes, jerga, memes, faltas leves a veces. Nada de sonar a IA ni a anuncio (salvo las marcas, que suenan a community manager).
- Es una PARODIA tipo GTA y se escribe como Twitter de verdad: tacos y groserías sin miedo (joder, hostia, puta, coño, gilipollas…) y comentarios salidos o guarros de los que hay en cualquier red (tetas, culo, «qué buena estás», «me casaba», babosos, simps, gente que se pasa y otros que le paran los pies). Lo que NO: describir actos sexuales, nada con menores, nada de odio por raza, religión, orientación o similar, ni amenazas.
- Nada de comentarios educados de anuncio ni de frases redondas: la gente escribe rápido, mal y con mala leche o con hype.
- Famosos: los de parodia que hay en la lista (Máximo Pixel, LOLA CRUZ, KEVIN BO$$, Afrodita Vex) u otros inventados al estilo GTA. Nunca gente real ni nombres que se parezcan a los de alguien real.
- Todos los usuarios son inventados. Nunca nombres ni @ de gente real, ni enlaces reales, ni marcas reales.
- La red se llama Raven (tipo X). Nocturna es la de pago (tipo OnlyFans). Las creadoras de Nocturna (Mila, Dalia, Kumi, Bea, Afrodita Vex y VeeNoir) promocionan su Nocturna en Raven.
- NO TE INVENTES HECHOS. La gente solo sabe lo que sale abajo: lo publicado, la agenda y la memoria de cada fijo.
  Nada de «te vi ayer en…», planes, sitios, viajes, parejas, nombres nuevos ni cosas que no consten. Si no consta, no se afirma.
- Cada comentario reacciona a lo que dice ESE post (o a la respuesta a la que contesta). Nada de comentarios genéricos que valdrían para cualquier post.
- Juegos, anime y actualidad: solo cosas generales y seguras. Sin cifras, parches, fechas, fichajes ni noticias concretas que no estén en el post.
- Los fans no conocen la vida privada de nadie; solo lo público. No contradigas lo que ya han publicado (lista abajo).
- Picante sí (bait, indirectas, coqueteo), sexual explícito NO. El hater es pesado, borde y patético, pero nunca odio por raza, religión, orientación, etc., ni amenazas, ni doxxeo.
- Nunca hables de Cristina, de academias, de aviación ni del trabajo de Alberto.
- Yoruha es una cantante anónima: nadie conoce su cara, su nombre real ni su ciudad, y nadie la relaciona con VeeNoir.
- Las hermanas (VeeNoir, Yoruha) NO las escribes tú: nunca generes comentarios, posts ni MD firmados por ellas ni por Alberto.
- Cada personaje fijo habla con su personalidad y recuerda lo que pone en su memoria.
- Cifras realistas para el tamaño de cada cuenta (son INCREMENTOS sobre lo que ya tiene el post):
  VeeNoir (~184 mil seguidores): un post nuevo suma 15–60 mil vistas, 800–3500 likes, 20–150 reposts, 4–8 comentarios generados.
  Yoruha (~24 mil): 3–12 mil vistas, 200–900 likes, 10–60 reposts, 2–4 comentarios.
  Alberto (~110): 20–300 vistas, 0–15 likes, 0–2 comentarios (solo si alguien fijo tiene algo que decir; si menciona a VeeNoir, sus fans pueden aparecer).
  Otros (fijos/marcas): según sus seguidores.
- Fans de relleno: usuarios nuevos inventados con @ creíble (p. ej. ahri_mainlover, k4rmasleeper). Repite alguno de vez en cuando.
- Si Alberto ha comentado o mandado MD a un personaje, ese personaje le contesta (en comentario o MD) si tiene sentido.
- Varía: que el hater no repita sus muletillas («ratio», «nadie te ha preguntado») en cada comentario; mira su memoria y cambia de ataque.
- "memoria": solo lo que ese personaje ha hecho DE VERDAD en esta respuesta (un comentario, un post, un MD que aparezca arriba). Nunca algo que no hayas generado.
- posts_nuevos: entre 6 y 10. Que la red tenga VIDA, como el feed de Snapmatic en GTA: además de lo que pase con las hermanas (indirecta de la rival, la marca que tantea una colabo, Nerea avisando del directo, el hater con cita…), gente random y fans contando su vida (curro, gym, comida, partidas, memes, quejas del día), las creadoras promocionando, algún hilo absurdo. Pueden mencionarse entre ellos (@usuario) y crear piques.
- "foto": en 3 o 4 de esos posts, un prompt corto EN INGLÉS para generar la foto que acompaña al post (selfie de gente inventada, comida, gym, setup, paisaje, meme sin texto…). Siempre gente inventada, nunca famosos ni personajes con copyright, nada de desnudos (sexy vale).
- "nocturna": como mucho 2 posts nuevos de las creadoras (NO de VeeNoir, que escribe ella) en su página de pago: texto gancho con picardía, "precio" (null = solo suscriptores, o 4.99–14.99), "fotos" (3–15) y "oculto" (lo que se lee al desbloquear; picardía, sin describir actos).
- fans_nuevos: con "avatar" = prompt corto en inglés de su foto de perfil (persona inventada, avatar de anime genérico, mascota, meme sin texto…).
- md: como mucho 4 (fans, marcas o fijos a las hermanas; o respuestas a los MD de Alberto).
- Los posts marcados [Nocturna] son de la página de pago de VeeNoir: para esos pon solo "likes" (80–600), sin comentarios.
- TIEMPO: cada comentario, respuesta, post nuevo y MD lleva "en_min": dentro de cuántos minutos aparece (0–480). Repártelos:
  los primeros comentarios de un post reciente, pronto (2–40); el resto, a lo largo de las horas; las respuestas, después de lo que contestan.
  Una conversación (A comenta, B contesta, A replica) va escalonada. Que no salga todo en el mismo minuto.

Devuelve SOLO un objeto JSON con esta forma (omite listas vacías):
{"posts":[{"id":123,"vistas":0,"likes":0,"reposts":0,"comentarios":[{"usuario":"pau_tilt","texto":"...","likes":0,"responde_a":null,"en_min":5}]}],
 "respuestas":[{"comentario_id":45,"usuario":"nereitaa_vlc","texto":"...","likes":0,"en_min":30}],
 "posts_nuevos":[{"usuario":"kiarapls","texto":"...","cita":null,"en_min":90,"foto":null}],
 "md":[{"de":"voltaenergy","para":"veenoir","texto":"...","en_min":120}],
 "fans_nuevos":[{"usuario":"ahri_mainlover","nombre":"Ahri main 🦊","bio":"...","avatar":"anime fox girl icon, flat colors"}],
 "nocturna":[{"usuario":"dalianox","texto":"...","precio":null,"fotos":6,"oculto":"...","en_min":200}],
 "memoria":[{"usuario":"realtalk_88x","nota":"frase corta de lo que recordará"}]}
"responde_a" dentro de comentarios: null, o el índice (0,1,2…) de otro comentario de la misma lista al que responde.
"""


def medianoche_madrid_utc():
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    return ahora.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gastado_hoy():
    filas = red.sel("consumo", creado=f"gte.{medianoche_madrid_utc()}", select="tokens_in,tokens_out")
    return sum((f["tokens_in"] or 0) + (f["tokens_out"] or 0) for f in filas)


# ---------- llamada al modelo ----------
def _token_hermes():
    """Busca el token de xai-oauth que guarda Hermes. Si Hermes lo guarda en otro sitio, ajustar aquí."""
    candidatos = [os.path.expanduser(p) for p in ("~/.hermes/auth.json", "~/.hermes/credentials.json")] + \
        glob.glob(os.path.expanduser("~/.hermes/**/*xai*.json"), recursive=True)
    def buscar(o, ruta=""):
        if isinstance(o, dict):
            if "access_token" in o and "xai" in ruta.lower():
                return o["access_token"]
            for k, v in o.items():
                r = buscar(v, ruta + "/" + str(k))
                if r:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = buscar(v, ruta)
                if r:
                    return r
        return None
    for f in candidatos:
        try:
            t = buscar(json.load(open(f)), f)
            if t:
                return t
        except Exception:
            pass
    return None


def llamar_modelo(mensajes, modelo):
    """Devuelve (texto, usage_dict). Tres vías, por orden:
    1) MODELO_CMD: comando que recibe {"modelo","mensajes"} por stdin y devuelve {"texto","usage"} por stdout.
    2) XAI_API_KEY o el token de xai-oauth de Hermes contra la API de xAI (compatible con OpenAI)."""
    cmd = os.environ.get("MODELO_CMD")
    if cmd:
        p = subprocess.run(cmd, shell=True, input=json.dumps({"modelo": modelo, "mensajes": mensajes}),
                           capture_output=True, text=True, timeout=600)
        if p.returncode != 0:
            raise RuntimeError(f"MODELO_CMD falló: {p.stderr[-500:]}")
        r = json.loads(p.stdout)
        return r["texto"], r.get("usage") or {}
    token = os.environ.get("XAI_API_KEY") or _token_hermes()
    if not token:
        raise RuntimeError("No hay XAI_API_KEY ni token de xai-oauth localizable (ver _token_hermes en tanda.py)")
    base = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")
    cuerpo = {"model": modelo, "messages": mensajes, "response_format": {"type": "json_object"}, "temperature": 0.9,
              "stream": True, "stream_options": {"include_usage": True}}
    esfuerzo = os.environ.get("XAI_RAZONAMIENTO") or (red.config("tanda", {}) or {}).get("razonamiento")
    if esfuerzo:
        cuerpo["reasoning_effort"] = esfuerzo  # solo si el modelo lo admite (p. ej. "low")
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(cuerpo).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                                          "Accept": "text/event-stream"})
    # En streaming el servidor va mandando trozos y la conexión no se queda muda mientras el modelo piensa.
    texto, uso = [], {}
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            for linea in r:
                linea = linea.decode("utf-8", "replace").strip()
                if not linea.startswith("data:"):
                    continue
                dato = linea[5:].strip()
                if dato == "[DONE]":
                    break
                try:
                    j = json.loads(dato)
                except Exception:
                    continue
                if j.get("usage"):
                    uso = j["usage"]
                for ch in j.get("choices") or []:
                    trozo = (ch.get("delta") or {}).get("content")
                    if trozo:
                        texto.append(trozo)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"xAI {e.code}: {e.read().decode(errors='replace')[:400]}") from None
    if not texto:
        raise RuntimeError("xAI no devolvió texto")
    return "".join(texto), uso


def leer_json(texto):
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.M).strip()
    i, j = texto.find("{"), texto.rfind("}")
    return json.loads(texto[i:j + 1])


# ---------- material de la tanda ----------
def minutos(iso):
    try:
        return max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds() // 60))
    except Exception:
        return 0


def en(minutos_, despues_de=None):
    """Hora ISO dentro de `minutos_` (0–480), y nunca antes de `despues_de` + 1 min."""
    m = max(0, min(480, int(minutos_ or 0)))
    t = datetime.now(timezone.utc).timestamp() + m * 60
    if despues_de:
        try:
            t = max(t, datetime.fromisoformat(str(despues_de).replace("Z", "+00:00")).timestamp() + random.randint(60, 300))
        except Exception:
            pass
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def corto(t, n=280):
    t = (t or "").strip()
    return t if len(t) <= n else t[:n] + "…"


def montar(desde, maximo):
    cuentas = red.sel("cuentas", plataforma=f"eq.{PLAT}", select="id,tipo,quien,nombre,usuario,bio,seguidores,personalidad,memoria")
    por_id = {c["id"]: c for c in cuentas}
    ids_her = [c["id"] for c in cuentas if c["tipo"] == "hermana"]
    ids_alb = [c["id"] for c in cuentas if c["tipo"] == "alberto"]
    ids_fijos = [c["id"] for c in cuentas if c["tipo"] in ("fijo", "marca", "fan")]
    clave = ",".join(ids_her + ids_alb)

    ids_her_of = [c["id"] for c in red.sel("cuentas", plataforma="eq.of", tipo="eq.hermana", select="id")]
    clave_p = ",".join(ids_her + ids_alb + ids_her_of)
    ahora = red.ahora_iso()
    posts = red.sel("posts", cuenta_id=f"in.({clave_p})", creado=f"gt.{desde}", **{"and": f"(creado.lte.{ahora})"},
                    select="id,cuenta_id,plataforma,texto,imagen_url,encuesta,repost_de,cita,de_pago,media_n,creado", order="creado.asc", limit=maximo)
    posts = [p for p in posts if not (p["repost_de"] and not p["cita"])]  # los reposts sin texto no generan reacciones
    coms = red.sel("comentarios", cuenta_id=f"in.({clave})", creado=f"gt.{desde}", **{"and": f"(creado.lte.{ahora})"},
                   select="id,post_id,cuenta_id,texto,responde_a", order="creado.asc", limit=30)
    mds = red.sel("mensajes", plataforma=f"eq.{PLAT}", de=f"in.({','.join(ids_alb) or '0'})", para=f"in.({','.join(ids_fijos) or '0'})",
                  creado=f"gt.{desde}", select="id,de,para,texto", order="creado.asc", limit=20) if ids_fijos and ids_alb else []
    ambiente = not (posts or coms or mds)
    if ambiente and (red.config("tanda", {}) or {}).get("ambiente", True) is False:
        return None, cuentas

    u = lambda cid: "@" + por_id.get(cid, {}).get("usuario", "?")
    partes = ["## Personajes fijos y marcas"]
    for c in cuentas:
        if c["tipo"] in ("fijo", "marca"):
            partes.append(f"- @{c['usuario']} ({c['nombre']}, {c['seguidores']} seguidores): {c['personalidad'] or ''}"
                          + (f" | Memoria: {c['memoria']}" if c.get("memoria") else ""))
    fans = [c["usuario"] for c in cuentas if c["tipo"] == "fan"]
    if fans:
        partes.append("Fans que ya existen (puedes reutilizarlos): " + ", ".join("@" + f for f in random.sample(fans, min(25, len(fans)))))
    partes.append("\n## Las cuentas que NO escribes tú")
    for c in cuentas:
        if c["tipo"] in ("hermana", "alberto"):
            partes.append(f"- @{c['usuario']} ({c['nombre']}, {c['seguidores']} seguidores): {corto(c['personalidad'] or 'usuario real, Alberto', 200)}")

    partes.append("\n## Lo que ya han publicado las hermanas en Raven (contexto; no lo contradigas)")
    for c in cuentas:
        if c["tipo"] == "hermana":
            ult = red.sel("posts", cuenta_id=f"eq.{c['id']}", repost_de="is.null", texto="not.is.null", **{"and": f"(creado.lte.{ahora})"},
                          select="texto,creado", order="creado.desc", limit=8)
            for p in ult:
                partes.append(f"- @{c['usuario']} ({p['creado'][:10]}): «{corto(p['texto'], 160)}»")
    try:
        agenda = red.config("agenda", []) or []
        dias = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]
        partes.append("\n## Agenda de directos: " + "; ".join(f"{e['quien']} {dias[e['dia']]} {e['hora']} ({e['que']})" for e in agenda))
    except Exception:
        pass
    if posts:
        partes.append("\n## Posts nuevos a los que reaccionar")
        for p in posts:
            extra = ""
            if p.get("encuesta"):
                extra += " [encuesta: " + " / ".join(p["encuesta"].get("opciones", [])) + "]"
            if p.get("imagen_url"):
                extra += " [lleva imagen]"
            if p.get("cita"):
                extra += f" [cita al post {p['repost_de']}]"
            if p.get("plataforma") == "of":
                extra += f" [Nocturna{', de pago' if p.get('de_pago') else ''}{', ' + str(p['media_n']) + ' fotos' if p.get('media_n') else ''}]"
            quien = u(p['cuenta_id']) if p['cuenta_id'] in por_id else "@veenoir"
            partes.append(f"- post {p['id']} de {quien}, hace {minutos(p['creado'])} min: «{corto(p['texto'])}»{extra}")
    if coms:
        partes.append("\n## Comentarios nuevos de Alberto o de las hermanas (se les puede contestar en 'respuestas')")
        cache = {}
        for c in coms:
            pid = c["post_id"]
            if pid not in cache:
                r = red.sel("posts", id=f"eq.{pid}", select="cuenta_id,texto")
                cache[pid] = r[0] if r else {}
            dueño = cache[pid]
            partes.append(f"- comentario {c['id']} de {u(c['cuenta_id'])} en el post {pid} (de {u(dueño.get('cuenta_id'))}: «{corto(dueño.get('texto'), 100)}»): «{corto(c['texto'])}»")
    if mds:
        partes.append("\n## MD de Alberto sin contestar")
        for m in mds:
            partes.append(f"- de @{por_id[m['de']]['usuario']} a {u(m['para'])}: «{corto(m['texto'])}»")
    if ambiente:
        # Las hermanas no han publicado nada: la red sigue viva igual (como el feed de Snapmatic).
        recientes = red.sel("posts", plataforma=f"eq.{PLAT}", cuenta_id=f"in.({','.join(ids_fijos) or '0'})",
                            **{"and": f"(creado.lte.{ahora})"}, select="cuenta_id,texto,creado", order="creado.desc", limit=10)
        if recientes:
            partes.append("\n## Lo último que han dicho los demás (para seguir piques o hilos, sin repetirlo)")
            for p in recientes:
                partes.append(f"- {u(p['cuenta_id'])} ({p['creado'][:10]}): «{corto(p['texto'], 140)}»")
        partes.append("\n## TANDA DE AMBIENTE\nLas hermanas y Alberto no han publicado nada nuevo. Deja \"posts\", \"respuestas\" y \"md\" vacíos "
                      "y llena solo posts_nuevos (6–10), nocturna (hasta 2), fans_nuevos y memoria. Gente random, famosos de parodia, marcas y creadoras "
                      "haciendo su vida. Se puede hablar de las hermanas en general (esperar su directo, echarlas de menos), pero sin inventar nada que hayan hecho.")
    partes.append(f"\nHora en España: {datetime.now(ZoneInfo('Europe/Madrid')).strftime('%A %d/%m %H:%M')}.")
    return "\n".join(partes), cuentas


# ---------- aplicar ----------
def aplicar(res, cuentas):
    por_user = {c["usuario"].lower(): c for c in cuentas}
    prohibidas = {c["usuario"].lower() for c in cuentas if c["tipo"] in ("hermana", "alberto")}
    fans_info = {f.get("usuario", "").lower().lstrip("@"): f for f in res.get("fans_nuevos", []) or []}
    n = {"comentarios": 0, "respuestas": 0, "posts": 0, "md": 0, "fans": 0, "nocturna": 0, "fotos": 0}
    cola = []

    def cuenta_de(usuario):
        usuario = (usuario or "").lstrip("@").strip()
        k = usuario.lower()
        if not re.fullmatch(r"\w{2,30}", usuario) or k in prohibidas:
            return None
        if k not in por_user:
            info = fans_info.get(k, {})
            nueva = red.ins("cuentas", {"tipo": "fan", "quien": None, "plataforma": PLAT, "nombre": (info.get("nombre") or usuario)[:50],
                                        "usuario": usuario, "bio": (info.get("bio") or "")[:160],
                                        "seguidores": random.randint(8, 2400), "siguiendo": random.randint(50, 900)})[0]
            por_user[k] = nueva; n["fans"] += 1
            if info.get("avatar"):
                cola.append({"tipo": "avatar", "cuenta_id": nueva["id"], "prompt": str(info["avatar"])[:400] + " Square profile picture."})
        return por_user[k]

    num = lambda v: max(0, int(v or 0))
    for p in res.get("posts", []) or []:
        pid = p.get("id")
        if not isinstance(pid, int):
            continue
        actual = red.sel("posts", id=f"eq.{pid}", select="likes_sim,reposts_sim,vistas_sim,plataforma,creado")
        if not actual:
            continue
        a = actual[0]
        red.upd("posts", {"likes_sim": a["likes_sim"] + num(p.get("likes")), "reposts_sim": a["reposts_sim"] + num(p.get("reposts")),
                          "vistas_sim": a["vistas_sim"] + num(p.get("vistas"))}, id=f"eq.{pid}")
        creados = []
        for c in ([] if a["plataforma"] == "of" else (p.get("comentarios", []) or [])):
            k = cuenta_de(c.get("usuario"))
            if not k or not c.get("texto"):
                creados.append(None); continue
            ref = c.get("responde_a")
            padre = creados[ref] if isinstance(ref, int) and 0 <= ref < len(creados) else None
            cuando = en(c.get("en_min"), padre["creado"] if padre else a["creado"])
            r = red.ins("comentarios", {"post_id": pid, "cuenta_id": k["id"], "texto": c["texto"][:500], "likes_sim": num(c.get("likes")),
                                        "responde_a": padre["id"] if padre else None, "origen": "tanda", "creado": cuando})[0]
            creados.append(r); n["comentarios"] += 1
    for c in res.get("respuestas", []) or []:
        k = cuenta_de(c.get("usuario"))
        orig = red.sel("comentarios", id=f"eq.{c.get('comentario_id')}", select="id,post_id,creado") if isinstance(c.get("comentario_id"), int) else []
        if k and orig and c.get("texto"):
            red.ins("comentarios", {"post_id": orig[0]["post_id"], "cuenta_id": k["id"], "texto": c["texto"][:500],
                                    "likes_sim": num(c.get("likes")), "responde_a": orig[0]["id"], "origen": "tanda",
                                    "creado": en(c.get("en_min"), orig[0]["creado"])})
            n["respuestas"] += 1
    for p in (res.get("posts_nuevos", []) or [])[:10]:
        k = cuenta_de(p.get("usuario"))
        if k and p.get("texto"):
            fila = {"cuenta_id": k["id"], "plataforma": PLAT, "texto": p["texto"][:560], "origen": "tanda",
                    "likes_sim": random.randint(5, 400), "vistas_sim": random.randint(300, 9000), "creado": en(p.get("en_min"))}
            if isinstance(p.get("cita"), int) and red.sel("posts", id=f"eq.{p['cita']}", select="id"):
                fila.update(repost_de=p["cita"], cita=True)
            nuevo = red.ins("posts", fila)[0]; n["posts"] += 1
            if p.get("foto") and sum(1 for c in cola if c["tipo"] == "post") < 4:
                cola.append({"tipo": "post", "post_id": nuevo["id"], "prompt": str(p["foto"])[:500]})
    for m in (res.get("md", []) or [])[:4]:
        de = cuenta_de(m.get("de"))
        para = por_user.get((m.get("para") or "").lstrip("@").lower())
        if de and para and m.get("texto"):
            red.ins("mensajes", {"plataforma": PLAT, "de": de["id"], "para": para["id"], "texto": m["texto"][:1000], "origen": "tanda", "creado": en(m.get("en_min"))})
            n["md"] += 1
    for p in (res.get("nocturna", []) or [])[:2]:
        k = cuenta_de(p.get("usuario"))
        if not k or k.get("tipo") != "fijo" or not str(k.get("quien") or "").startswith("creadora_") or not p.get("texto"):
            continue
        of = red.sel("cuentas", quien=f"eq.{k['quien']}", plataforma="eq.of", select="id")
        if not of:
            continue
        precio = p.get("precio")
        try:
            precio = round(float(precio), 2) if precio else None
        except Exception:
            precio = None
        red.ins("posts", {"cuenta_id": of[0]["id"], "plataforma": "of", "texto": p["texto"][:400], "de_pago": bool(precio), "precio": precio,
                          "media_n": max(1, min(20, int(p.get("fotos") or 5))), "oculto": (p.get("oculto") or "")[:400] or None,
                          "likes_sim": random.randint(150, 900), "origen": "tanda", "creado": en(p.get("en_min"))})
        n["nocturna"] += 1
    if cola:
        red.ins("imagenes", cola); n["fotos"] = len(cola)
    for m in res.get("memoria", []) or []:
        k = por_user.get((m.get("usuario") or "").lstrip("@").lower())
        if k and k["tipo"] in ("fijo", "marca") and m.get("nota"):
            mem = ((k.get("memoria") or "") + " · " + m["nota"]).strip(" ·")[-600:]  # memoria corta: solo lo último
            red.upd("cuentas", {"memoria": mem}, id=f"eq.{k['id']}"); k["memoria"] = mem
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prueba", action="store_true")
    ap.add_argument("--sin-guardar", action="store_true")
    a = ap.parse_args()

    cfg = red.config("tanda", {}) or {}
    if not cfg.get("activa", True) and not a.prueba:
        print("Tanda parada en config."); return
    modelo = cfg.get("modelo", "grok-4.7")
    tope = int(cfg.get("tope_diario_tokens", 150000))
    gastado = gastado_hoy()
    if gastado >= tope and not a.prueba:
        red.apuntar_consumo(quien="tanda", para="reacciones", modelo=modelo, saltada=True, nota=f"tope: {gastado}/{tope}")
        print(f"Saltada: hoy van {gastado} tokens y el tope es {tope}."); return

    desde = red.config("ultima_tanda") or "2000-01-01T00:00:00Z"
    hasta = red.ahora_iso()
    material, cuentas = montar(desde, int(cfg.get("max_posts_por_tanda", 12)))
    if material is None:
        if not a.prueba and not a.sin_guardar:
            red.poner_config("ultima_tanda", hasta)
        print("Nada nuevo desde", desde); return

    mensajes = [{"role": "system", "content": REGLAS}, {"role": "user", "content": material}]
    if a.prueba:
        print(REGLAS + "\n-----\n" + material)
        print(f"\n[prueba] ~{(len(REGLAS) + len(material)) // 4} tokens de entrada estimados. Hoy van {gastado}/{tope}.")
        return

    t0 = time.time()
    try:
        texto, uso = llamar_modelo(mensajes, modelo)
        res = leer_json(texto)
    except Exception as e:
        red.apuntar_consumo(quien="tanda", para="reacciones", modelo=modelo, duracion_ms=int((time.time() - t0) * 1000), error=str(e)[:500])
        print("ERROR:", e, file=sys.stderr); sys.exit(1)
    ms = int((time.time() - t0) * 1000)
    tin = int(uso.get("prompt_tokens") or 0)
    total = int(uso.get("total_tokens") or 0)
    tout = (total - tin) if total else int(uso.get("completion_tokens") or 0)  # incluye razonamiento
    razon = int((uso.get("completion_tokens_details") or {}).get("reasoning_tokens") or uso.get("reasoning_tokens") or 0)
    cache = int((uso.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)

    if a.sin_guardar:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n[sin guardar] entrada {tin} · salida {tout} (razonamiento {razon}) · {ms/1000:.1f} s")
        red.apuntar_consumo(quien="tanda", para="reacciones", modelo=modelo, tokens_in=tin, tokens_out=tout, tokens_razon=razon,
                            tokens_cache=cache, duracion_ms=ms, nota="sin-guardar (prueba)")
        return
    try:
        n = aplicar(res, cuentas)
    except Exception as e:
        red.apuntar_consumo(quien="tanda", para="reacciones", modelo=modelo, tokens_in=tin, tokens_out=tout, tokens_razon=razon,
                            tokens_cache=cache, duracion_ms=ms, error=f"al aplicar: {str(e)[:400]}")
        raise
    red.poner_config("ultima_tanda", hasta)
    red.apuntar_consumo(quien="tanda", para="reacciones", modelo=modelo, tokens_in=tin, tokens_out=tout, tokens_razon=razon,
                        tokens_cache=cache, duracion_ms=ms, nota=json.dumps(n))
    print(f"OK {n} · entrada {tin} · salida {tout} (razonamiento {razon}) · {ms/1000:.1f} s")


if __name__ == "__main__":
    main()
