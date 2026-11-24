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
- Aika (@aika_kurenai) tiene una cuenta PRIVADA y elegante: casi nadie la ve y nadie la relaciona con VeeNoir ni con Yoruha. Sus posts solo llevan "likes" (5–40) y como mucho 1 comentario de alguien fijo que encaje; nunca fans, haters ni marcas. Nadie la menciona en otros posts.
- Las hermanas (VeeNoir, Yoruha, Aika) NO las escribes tú: nunca generes comentarios, posts ni MD firmados por ellas ni por Alberto.
- Cada personaje fijo habla con su personalidad y recuerda lo que pone en su memoria.
- Cifras realistas para el tamaño de cada cuenta (son INCREMENTOS sobre lo que ya tiene el post):
  VeeNoir (~184 mil seguidores): un post nuevo suma 15–60 mil vistas, 800–3500 likes, 20–150 reposts, 4–8 comentarios generados.
  Yoruha (~24 mil): 3–12 mil vistas, 200–900 likes, 10–60 reposts, 2–4 comentarios.
  Alberto (~110): 20–300 vistas, 0–15 likes, 0–2 comentarios (solo si alguien fijo tiene algo que decir; si menciona a VeeNoir, sus fans pueden aparecer).
  Otros (fijos/marcas): según sus seguidores.
- Fans de relleno: usuarios nuevos inventados con @ creíble (p. ej. ahri_mainlover, k4rmasleeper). Repite alguno de vez en cuando.
- Si Alberto ha comentado o mandado MD a un personaje, ese personaje le contesta (en comentario o MD) si tiene sentido.
- Varía: que el hater no repita sus muletillas («ratio», «nadie te ha preguntado») en cada comentario; mira su memoria y cambia de ataque.
- CONTINUIDAD: Raven es un mundo que sigue. Lee los «Hilos de Raven» de abajo: cada uno dice qué ha pasado y qué viene después. Los hilos son cosas ENTRE gente o que importan a varios (piques, colabos, sorteos, anuncios, el directo, una votación), no la cena de un fan: lo cotidiano de cada uno no es un hilo y no hay que continuarlo. En cada tanda AVANZA al menos 2 hilos (un paso nuevo, no repetir el mismo) y, si toca, cierra alguno. Que lo de ayer se note hoy y lo de hoy se note mañana. No reinicies nada ni lo contradigas.
- "cronica": devuelve SIEMPRE los hilos actualizados, de 6 a 12 líneas, cada una con la forma «tema: lo último que ha pasado → lo que viene / falta». Quita lo cerrado o viejo. Añade 1 o 2 líneas que empiecen por «MAÑANA:» con algo que alguien ha anunciado o dejado a medias para la próxima tanda. Solo hechos que consten (publicados arriba o generados por ti ahora).
- NO TE REPITAS: cada personaje tiene abajo sus últimos posts. No repitas su tema, su chiste ni su frase con otras palabras; si vuelve a un tema, que sea con algo NUEVO (otro paso, otro giro). El código descarta los posts que se parecen a los anteriores.
- CONVERSACIONES: cuando alguien contesta a otro (abajo, «Conversaciones abiertas»), el aludido puede replicar en "respuestas" con el comentario_id; que se note que ha leído lo que le han dicho. Hilos de 2 o 3 turnos, no más.
- La gente también se comenta ENTRE ELLA: en "posts" puedes meter comentarios a los «Posts recientes de la gente» de abajo (con su id; ahí "likes" pequeños y sin "vistas"). Reparte 4–8 comentarios entre varios de esos posts: risas, piques, «a mí me pasa igual», alguien que corrige a otro. Es lo que hace que la red parezca viva.
- Los comentarios de un post ven lo que ya se ha dicho en él (abajo, debajo de cada post): no digas lo mismo que otro; contesta, apoya o lleva la contraria.
- MD: abajo va la conversación ENTERA con Alberto (lo anterior y lo nuevo). Contesta a lo último recordando lo de antes, como en un chat de verdad.
- "memoria": solo lo que ese personaje ha hecho DE VERDAD en esta respuesta (un comentario, un post, un MD que aparezca arriba). Nunca algo que no hayas generado.
- posts_nuevos: entre {MIN_POSTS} y {MAX_POSTS}. VARIEDAD: como mucho 2 posts por tanda sobre el mismo tema (el próximo directo, un mismo pique…); el resto, de otras cosas. Que la red tenga VIDA, como el feed de Snapmatic en GTA: además de lo que pase con las hermanas (indirecta de la rival, la marca que tantea una colabo, Nerea avisando del directo, el hater con cita…), gente random y fans contando su vida (curro, gym, comida, partidas, memes, quejas del día), las creadoras promocionando, algún hilo absurdo. Pueden mencionarse entre ellos (@usuario) y crear piques.
- "foto": en 3 o 4 de esos posts, un prompt corto EN INGLÉS para generar la foto que acompaña al post (selfie de gente inventada, comida, gym, setup, paisaje, meme sin texto…). Siempre gente inventada, nunca famosos ni personajes con copyright, nada de desnudos (sexy vale).
  "sale": true si en la foto aparece el propio autor del post (selfie, foto suya); false si es comida, paisaje, setup, meme… Si sale, describe la escena y la ropa, no su cara: la cara la pone su hoja de referencia.
- "nocturna": como mucho 2 posts nuevos de las creadoras (NO de VeeNoir, que escribe ella) en su página de pago: texto gancho con picardía, "precio" (null = solo suscriptores, o 4.99–14.99), "fotos" (3–15) y "oculto" (lo que se lee al desbloquear; picardía, sin describir actos).
- fans_nuevos: con "avatar" = prompt corto en inglés de su foto de perfil (persona inventada, avatar de anime genérico, mascota, meme sin texto…).
- md: como mucho 4 (fans, marcas o fijos a las hermanas; o respuestas a los MD de Alberto).
- Los posts marcados [Nocturna] son de la página de pago de VeeNoir: para esos pon solo "likes" (80–600), sin comentarios.
- TIEMPO: cada comentario, respuesta, post nuevo y MD lleva "en_min": dentro de cuántos minutos aparece (0–{MAX_MIN}). Reparte los posts_nuevos por TODO ese tramo (hasta la próxima tanda), no los amontones al principio:
  los primeros comentarios de un post reciente, pronto (2–40); el resto, a lo largo de las horas; las respuestas, después de lo que contestan.
  Una conversación (A comenta, B contesta, A replica) va escalonada. Que no salga todo en el mismo minuto.

Devuelve SOLO un objeto JSON con esta forma (omite listas vacías):
{"posts":[{"id":123,"vistas":0,"likes":0,"reposts":0,"comentarios":[{"usuario":"pau_tilt","texto":"...","likes":0,"responde_a":null,"en_min":5}]}],
 "respuestas":[{"comentario_id":45,"usuario":"nereitaa_vlc","texto":"...","likes":0,"en_min":30}],
 "posts_nuevos":[{"usuario":"kiarapls","texto":"...","cita":null,"en_min":90,"foto":null,"sale":false}],
 "md":[{"de":"voltaenergy","para":"veenoir","texto":"...","en_min":120}],
 "fans_nuevos":[{"usuario":"ahri_mainlover","nombre":"Ahri main 🦊","bio":"...","avatar":"anime fox girl icon, flat colors"}],
 "nocturna":[{"usuario":"dalianox","texto":"...","precio":null,"fotos":6,"oculto":"...","en_min":200}],
 "memoria":[{"usuario":"realtalk_88x","nota":"frase corta de lo que recordará"}],
 "cronica":["hilo abierto en una frase corta", "..."]}
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


def proveedor_local():
    """Modelo local (Ollama / LM Studio, API compatible con OpenAI). Se activa con LLM_LOCAL_URL
    o con config tanda.proveedor = "local" (+ local_url y modelo_local). Devuelve (url, modelo) o None."""
    cfg = red.config("tanda", {}) or {}
    url = os.environ.get("LLM_LOCAL_URL") or (cfg.get("local_url", "http://127.0.0.1:11434/v1") if cfg.get("proveedor") == "local" else None)
    if not url:
        return None
    return url.rstrip("/"), os.environ.get("LLM_LOCAL_MODELO") or cfg.get("modelo_local") or "huihui_ai/qwen3-abliterated:14b-v2"


def proveedor_gemini():
    """Gemini por su acceso compatible con OpenAI. Se activa con config tanda.proveedor = "gemini"
    (o LLM_PROVEEDOR=gemini). La clave va en GEMINI_API_KEY, dentro de ~/.hermes/red-social.env.
    Devuelve (url, clave, modelo, esfuerzo) o None."""
    cfg = red.config("tanda", {}) or {}
    if (os.environ.get("LLM_PROVEEDOR") or cfg.get("proveedor")) != "gemini":
        return None
    clave = os.environ.get("GEMINI_API_KEY")
    if not clave:
        raise RuntimeError("Proveedor gemini sin GEMINI_API_KEY en el .env")
    base = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
    modelo = os.environ.get("GEMINI_MODELO") or cfg.get("modelo_gemini") or "gemini-4-neon"
    esfuerzo = os.environ.get("GEMINI_RAZONAMIENTO") or cfg.get("razonamiento_gemini") or "low"
    return base, clave, modelo, esfuerzo


def llamar_modelo(mensajes, modelo):
    """Como _llamar, pero si el modelo principal (Gemini o un MODELO_CMD) falla y config tanda.respaldo_grok
    no es false, repite con Grok."""
    try:
        return _llamar(mensajes, modelo)
    except Exception as e:
        cfg = red.config("tanda", {}) or {}
        if os.environ.get("LLM_PROVEEDOR") == "xai" or not (proveedor_gemini_activo() or os.environ.get("MODELO_CMD") or cfg.get("modelo_cmd")) \
                or cfg.get("respaldo_grok", True) is False:
            raise
        print(f"El modelo principal falló ({str(e)[:200]}); repito con Grok.", file=sys.stderr)
        os.environ["LLM_PROVEEDOR"] = "xai"
        try:
            return _llamar(mensajes, cfg.get("modelo", "grok-4.7"))
        finally:
            os.environ.pop("LLM_PROVEEDOR", None)


def proveedor_gemini_activo():
    cfg = red.config("tanda", {}) or {}
    return not os.environ.get("MODELO_CMD") and not proveedor_local() and (os.environ.get("LLM_PROVEEDOR") or cfg.get("proveedor")) == "gemini"


def _llamar(mensajes, modelo):
    """Devuelve (texto, usage_dict). Tres vías, por orden:
    1) MODELO_CMD (o config tanda.modelo_cmd): comando que recibe {"modelo","mensajes"} por stdin y devuelve
       {"texto","usage"} por stdout. Sirve para usar un modelo a través de la conexión de Hermes (p. ej. Gemini).
    2) Modelo local (proveedor_local): Ollama o LM Studio en el propio Mac, sin clave.
    3) XAI_API_KEY o el token de xai-oauth de Hermes contra la API de xAI (compatible con OpenAI)."""
    cmd = None if os.environ.get("LLM_PROVEEDOR") == "xai" else (os.environ.get("MODELO_CMD") or (red.config("tanda", {}) or {}).get("modelo_cmd"))
    if cmd:
        p = subprocess.run(cmd, shell=True, input=json.dumps({"modelo": modelo, "mensajes": mensajes}),
                           capture_output=True, text=True, timeout=600)
        if p.returncode != 0:
            raise RuntimeError(f"MODELO_CMD falló: {p.stderr[-500:]}")
        r = json.loads(p.stdout)
        return r["texto"], r.get("usage") or {}
    local = proveedor_local()
    gem = None if local else proveedor_gemini()
    if local:
        base, modelo = local
        token = "local"
    elif gem:
        base, token, modelo, esfuerzo_gem = gem
    else:
        token = os.environ.get("XAI_API_KEY") or _token_hermes()
        if not token:
            raise RuntimeError("No hay XAI_API_KEY ni token de xai-oauth localizable (ver _token_hermes en tanda.py)")
        base = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")
    cuerpo = {"model": modelo, "messages": mensajes, "response_format": {"type": "json_object"}, "temperature": 0.9,
              "stream": True, "stream_options": {"include_usage": True}}
    if local and os.environ.get("LLM_LOCAL_EXTRA"):
        cuerpo.update(json.loads(os.environ["LLM_LOCAL_EXTRA"]))  # p. ej. {"reasoning_effort":"none"} para apagar el pensamiento
    esfuerzo = None if local else esfuerzo_gem if gem else (os.environ.get("XAI_RAZONAMIENTO") or (red.config("tanda", {}) or {}).get("razonamiento"))
    if esfuerzo:
        cuerpo["reasoning_effort"] = esfuerzo  # solo si el modelo lo admite (p. ej. "low")
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(cuerpo).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                                          "Accept": "text/event-stream"})
    # En streaming el servidor va mandando trozos y la conexión no se queda muda mientras el modelo piensa.
    quien = "local" if local else "Gemini" if gem else "xAI"
    texto, uso = [], {}
    try:
        try:
            r = urllib.request.urlopen(req, timeout=900)
        except urllib.error.HTTPError as e:
            if not (gem and e.code == 400):
                raise
            # Si Gemini no acepta response_format json_object, se repite sin él (el prompt ya pide solo JSON)
            cuerpo.pop("response_format", None)
            req = urllib.request.Request(base + "/chat/completions", data=json.dumps(cuerpo).encode(), method="POST",
                                         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                                                  "Accept": "text/event-stream"})
            r = urllib.request.urlopen(req, timeout=900)
        with r:
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
        raise RuntimeError(f"{quien} {e.code}: {e.read().decode(errors='replace')[:400]}") from None
    if not texto:
        raise RuntimeError(f"{quien} no devolvió texto")
    if not uso:  # algunos servidores locales no mandan el recuento: se estima (~4 caracteres por token)
        uso = {"prompt_tokens": sum(len(m["content"]) for m in mensajes) // 4, "completion_tokens": len("".join(texto)) // 4, "estimado": True}
    return "".join(texto), uso


def leer_json(texto):
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.S).strip()  # modelos locales que «piensan» en voz alta
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.M).strip()
    i, j = texto.find("{"), texto.rfind("}")
    return json.loads(texto[i:j + 1])


# ---------- material de la tanda ----------
def minutos(iso):
    try:
        return max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds() // 60))
    except Exception:
        return 0


def hoja_de(usuario):
    """¿Tiene este personaje hoja de referencia en el Mac? (~/.hermes/red-social/hojas/<usuario>.png)"""
    d = os.path.expanduser(os.environ.get("HOJAS_DIR", "~/.hermes/red-social/hojas"))
    return any(os.path.exists(os.path.join(d, f"{usuario}.{e}")) for e in ("png", "jpg", "jpeg", "webp"))


def cifras(seguidores):
    """Vistas, likes y reposts acordes al tamaño de la cuenta (un famoso de 4 M no saca 100 likes)."""
    seg = max(30, int(seguidores or 50))
    vistas = int(seg * random.uniform(0.03, 0.25)) + random.randint(20, 300)
    likes = max(1, int(vistas * random.uniform(0.02, 0.09)))
    return {"vistas_sim": vistas, "likes_sim": likes, "reposts_sim": int(likes * random.uniform(0.02, 0.12))}


AVATARES_GENERICOS = [
    "casual selfie of an invented young Spanish guy with a cap, phone camera, everyday light",
    "casual selfie of an invented young Spanish woman, messy bun, bedroom mirror",
    "a fat orange cat staring at the camera, close-up, funny",
    "generic anime-style avatar of an invented character with headphones, flat colors",
    "blurry photo of a gaming setup with RGB lights, no people",
    "meme-style photo of a dog wearing sunglasses, no text",
    "invented guy in a football shirt at a bar terrace, sunny, phone photo",
    "low-light photo of a cup of coffee and a notebook, aesthetic",
]


ESCALA = 1.0  # con --ya todo sale en ~10 min (para revisar), manteniendo el orden


def parecido(a, b):
    """0–1: cuánto se parecen dos textos (sin mayúsculas, signos ni @)."""
    import difflib
    f = lambda t: re.sub(r"[^a-zñáéíóúü0-9 ]", "", re.sub(r"@\w+", "", (t or "").lower())).split()
    x, y = f(a), f(b)
    if not x or not y:
        return 0.0
    return difflib.SequenceMatcher(None, x, y).ratio()


def cadencia():
    """(mín. posts, máx. posts, máx. minutos) de una tanda, desde config tanda; por defecto 8–14 posts repartidos en 8 h."""
    cfg = red.config("tanda", {}) or {}
    mx = int(cfg.get("max_posts_nuevos", 14))
    mn = min(mx, int(cfg.get("min_posts_nuevos", 8)))
    return mn, mx, int(cfg.get("reparto_min", 480))


def reglas():
    mn, mx, mm = cadencia()
    return REGLAS.replace("{MIN_POSTS}", str(mn)).replace("{MAX_POSTS}", str(mx)).replace("{MAX_MIN}", str(mm))


def en(minutos_, despues_de=None):
    """Hora ISO dentro de `minutos_` (0–reparto_min), y nunca antes de `despues_de` + 1 min."""
    m = max(0, min(cadencia()[2], int(minutos_ or 0))) * ESCALA
    t = datetime.now(timezone.utc).timestamp() + m * 60
    if despues_de:
        try:
            t = max(t, datetime.fromisoformat(str(despues_de).replace("Z", "+00:00")).timestamp() + random.randint(60, 300) * ESCALA)
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
    ids_fm = [c["id"] for c in cuentas if c["tipo"] in ("fijo", "marca")]
    suyos = {}
    if ids_fm:
        for p in red.sel("posts", cuenta_id=f"in.({','.join(ids_fm)})", texto="not.is.null", **{"and": f"(creado.lte.{ahora})"},
                         select="cuenta_id,texto", order="creado.desc", limit=300):
            if len(suyos.setdefault(p["cuenta_id"], [])) < 3:
                suyos[p["cuenta_id"]].append(p["texto"])
    for c in cuentas:
        if c["tipo"] in ("fijo", "marca"):
            partes.append(f"- @{c['usuario']} ({c['nombre']}, {c['seguidores']} seguidores): {c['personalidad'] or ''}"
                          + (f" | Memoria: {c['memoria']}" if c.get("memoria") else "")
                          + (" | Sus últimos posts (no los repitas): " + " / ".join(f"«{corto(t, 70)}»" for t in suyos[c['id']]) if suyos.get(c["id"]) else ""))
    cron = red.config("cronica", {}) or {}
    if cron.get("lineas"):
        partes.append(f"\n## Hilos de Raven (actualizados {str(cron.get('fecha', ''))[:16]}; avánzalos, no los contradigas)")
        partes.extend("- " + str(l) for l in cron["lineas"])
    else:
        partes.append("\n## Hilos de Raven\n(vacío: empiézalos tú con lo que pase en esta tanda)")
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
            ya = red.sel("comentarios", post_id=f"eq.{p['id']}", **{"and": f"(creado.lte.{ahora})"}, select="id,cuenta_id,texto",
                         order="likes_sim.desc", limit=6)
            for c in ya:
                partes.append(f"    · ya comentado — comentario {c['id']} de {u(c['cuenta_id'])}: «{corto(c['texto'], 90)}»")
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
        partes.append("\n## MD de Alberto sin contestar (con la conversación anterior entera)")
        vistos = set()
        for m in mds:
            par = (m["de"], m["para"])
            if par in vistos:
                continue
            vistos.add(par)
            partes.append(f"- conversación de @{por_id[m['de']]['usuario']} con {u(m['para'])}:")
            hilo = red.sel("mensajes", plataforma=f"eq.{PLAT}", **{"or": f"(and(de.eq.{m['de']},para.eq.{m['para']}),and(de.eq.{m['para']},para.eq.{m['de']}))",
                           "and": f"(creado.lte.{ahora})"}, select="de,texto,creado", order="creado.desc", limit=12)
            for h in reversed(hilo):
                partes.append(f"    {h['creado'][5:16].replace('T', ' ')} {u(h['de'])}: «{corto(h['texto'], 200)}»")
    hace12 = datetime.fromtimestamp(time.time() - 12 * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    gente = red.sel("posts", plataforma=f"eq.{PLAT}", cuenta_id=f"in.({','.join(ids_fijos) or '0'})", texto="not.is.null",
                    creado=f"gt.{hace12}", **{"and": f"(creado.lte.{ahora})"}, select="id,cuenta_id,texto", order="creado.desc", limit=30)
    if gente:
        partes.append("\n## Posts recientes de la gente (se les puede comentar en \"posts\" con su id)")
        for p in random.sample(gente, min(8, len(gente))):
            partes.append(f"- post {p['id']} de {u(p['cuenta_id'])}: «{corto(p['texto'], 140)}»")
            for c in red.sel("comentarios", post_id=f"eq.{p['id']}", **{"and": f"(creado.lte.{ahora})"}, select="id,cuenta_id,texto", limit=3):
                partes.append(f"    · ya comentado — comentario {c['id']} de {u(c['cuenta_id'])}: «{corto(c['texto'], 80)}»")
    hace_dia = datetime.fromtimestamp(time.time() - 36 * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    resp = red.sel("comentarios", responde_a="not.is.null", creado=f"gt.{hace_dia}", **{"and": f"(creado.lte.{ahora})"},
                   select="id,post_id,cuenta_id,texto,responde_a", order="creado.desc", limit=40)
    abiertas = []
    for r in resp:
        padre = red.sel("comentarios", id=f"eq.{r['responde_a']}", select="id,cuenta_id,texto")
        if not padre or padre[0]["cuenta_id"] not in por_id or por_id[padre[0]["cuenta_id"]]["tipo"] in ("hermana", "alberto"):
            continue
        if red.sel("comentarios", responde_a=f"eq.{r['id']}", cuenta_id=f"eq.{padre[0]['cuenta_id']}", select="id"):
            continue  # ya le contestó
        abiertas.append((r, padre[0]))
        if len(abiertas) >= 6:
            break
    if abiertas:
        partes.append("\n## Conversaciones abiertas (el aludido puede replicar en 'respuestas' con ese comentario_id)")
        for r, pa in abiertas:
            partes.append(f"- en el post {r['post_id']}: {u(pa['cuenta_id'])} dijo «{corto(pa['texto'], 100)}» y {u(r['cuenta_id'])} le contestó "
                          f"(comentario {r['id']}): «{corto(r['texto'], 120)}»")
    if ambiente:
        # Las hermanas no han publicado nada: la red sigue viva igual (como el feed de Snapmatic).
        recientes = red.sel("posts", plataforma=f"eq.{PLAT}", cuenta_id=f"in.({','.join(ids_fijos) or '0'})",
                            **{"and": f"(creado.lte.{ahora})"}, select="cuenta_id,texto,creado", order="creado.desc", limit=10)
        if recientes:
            partes.append("\n## Lo último que han dicho los demás (para seguir piques o hilos, sin repetirlo)")
            for p in recientes:
                partes.append(f"- {u(p['cuenta_id'])} ({p['creado'][:10]}): «{corto(p['texto'], 140)}»")
        partes.append("\n## TANDA DE AMBIENTE\nLas hermanas y Alberto no han publicado nada nuevo. Deja \"md\" vacío; en \"posts\", solo comentarios a los posts recientes de la gente "
                      "y llena posts_nuevos (" + "–".join(map(str, cadencia()[:2])) + "), las \"respuestas\" de las conversaciones abiertas si las hay, nocturna (hasta 2), fans_nuevos, memoria y cronica. Reparto: al menos la MITAD de los posts, de gente random "
                      "y fans (nuevos o de la lista) contando su vida; 1 o 2 de famosos de parodia (@maximopixel, @lolacruzoficial, @kevinbossreal, @afroditavex); "
                      "el resto, fijos, marcas o creadoras. Mete 2–4 fans_nuevos con avatar. Se puede hablar de las hermanas en general (esperar su directo, echarlas de menos), "
                      "pero sin inventar nada que hayan hecho: nada de «su peluca», «su filtro nuevo» ni cosas que no estén arriba.")
    _h = datetime.now(ZoneInfo('Europe/Madrid'))
    _dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    partes.append(f"\nHora en España: {_dias[_h.weekday()]} {_h.strftime('%d/%m %H:%M')}.")
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
            # todo fan nuevo sale con foto: la que pida Grok o una genérica al azar
            cola.append({"tipo": "avatar", "cuenta_id": nueva["id"],
                         "prompt": str(info.get("avatar") or random.choice(AVATARES_GENERICOS))[:400] + " Square profile picture."})
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
    hace2 = datetime.fromtimestamp(time.time() - 48 * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    recientes = red.sel("posts", plataforma=f"eq.{PLAT}", texto="not.is.null", creado=f"gt.{hace2}", select="cuenta_id,texto", limit=400)
    aceptados = []
    n["descartados"] = 0
    for p in (res.get("posts_nuevos", []) or [])[:cadencia()[1]]:
        k = cuenta_de(p.get("usuario"))
        if k and p.get("texto"):
            ult = red.sel("posts", cuenta_id=f"eq.{k['id']}", texto="not.is.null", select="texto,creado", order="creado.desc", limit=10)
            propios = [t["texto"] for t in ult]
            cfg_t = red.config("tanda", {}) or {}
            horas_frio = float(cfg_t.get("enfriamiento_fan_h", 8) if k["tipo"] == "fan" else cfg_t.get("enfriamiento_fijo_h", 4)) * ESCALA
            if ult and horas_frio and minutos(ult[0]["creado"]) < horas_frio * 60 and k["tipo"] in ("fan", "fijo") \
                    and not str(k.get("quien") or "").startswith(("famoso", "famosa")):
                n["descartados"] += 1  # ya publicó hace poco: que no parezca que vive en Raven
                continue
            if (any(parecido(p["texto"], t) >= 0.45 for t in propios)
                    or any(parecido(p["texto"], t["texto"]) >= 0.55 for t in recientes)
                    or any(parecido(p["texto"], t) >= 0.55 for t in aceptados)):
                n["descartados"] += 1  # refrito: fuera
                continue
            aceptados.append(p["texto"])
            fila = {"cuenta_id": k["id"], "plataforma": PLAT, "texto": p["texto"][:560], "origen": "tanda",
                    **cifras(k.get("seguidores")), "creado": en(p.get("en_min"))}
            if isinstance(p.get("cita"), int) and red.sel("posts", id=f"eq.{p['cita']}", select="id"):
                fila.update(repost_de=p["cita"], cita=True)
            nuevo = red.ins("posts", fila)[0]; n["posts"] += 1
            if p.get("foto") and sum(1 for c in cola if c["tipo"] == "post") < 4:
                fila_img = {"tipo": "post", "post_id": nuevo["id"], "prompt": str(p["foto"])[:500]}
                if p.get("sale") and k["tipo"] in ("fijo", "marca") and hoja_de(k["usuario"]):
                    fila_img["referencia"] = k["usuario"]  # imagenes.py busca su hoja y mantiene la cara
                cola.append(fila_img)
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
        # PostgREST exige las mismas claves en todas las filas de un mismo insert
        claves = ("tipo", "cuenta_id", "post_id", "prompt", "referencia")
        filas = [{k: c.get(k) for k in claves} for c in cola]
        try:
            red.ins("imagenes", filas); n["fotos"] = len(filas)
        except Exception as e:  # que una foto no tumbe la tanda: se apunta y se sigue
            n["error_fotos"] = str(e)[:200]
    cron = [str(l)[:240] for l in (res.get("cronica") or []) if str(l).strip()][:14]
    if cron:
        red.poner_config("cronica", {"lineas": cron, "fecha": red.ahora_iso()})
    for m in res.get("memoria", []) or []:
        k = por_user.get((m.get("usuario") or "").lstrip("@").lower())
        if k and k["tipo"] in ("fijo", "marca") and m.get("nota"):
            mem = ((k.get("memoria") or "") + " · " + m["nota"]).strip(" ·")[-600:]  # memoria corta: solo lo último
            red.upd("cuentas", {"memoria": mem}, id=f"eq.{k['id']}"); k["memoria"] = mem
    return n


# ---------- tanda externa (Antigravity u otro) ----------
INSTRUCCION_EXTERNA = """INSTRUCCIONES: actúa exactamente como el motor descrito abajo. Devuelve SOLO el objeto JSON que piden las reglas,
sin texto antes ni después y sin bloque de código. Guárdalo tal cual en respuesta-tanda.json, en esta misma carpeta."""


def exportar(carpeta, material, cuentas, desde, hasta):
    os.makedirs(carpeta, exist_ok=True)
    for viejo in ("respuesta-tanda.json",):
        ruta = os.path.join(carpeta, viejo)
        if os.path.exists(ruta):
            os.replace(ruta, ruta + ".anterior")
    with open(os.path.join(carpeta, "prompt-tanda.txt"), "w", encoding="utf-8") as f:
        f.write(INSTRUCCION_EXTERNA + "\n\n===== REGLAS =====\n" + reglas().strip() + "\n\n===== MATERIAL =====\n" + material.strip() + "\n")
    with open(os.path.join(carpeta, "estado-tanda.json"), "w", encoding="utf-8") as f:
        json.dump({"desde": desde, "hasta": hasta, "escala": ESCALA, "cuentas": cuentas, "exportado": red.ahora_iso()}, f, ensure_ascii=False)
    print(f"Exportado en {carpeta}: prompt-tanda.txt (~{(len(REGLAS) + len(material)) // 4} tokens). Falta respuesta-tanda.json.")


def aplicar_externa(carpeta, forzar=False):
    global ESCALA
    ruta_estado = os.path.join(carpeta, "estado-tanda.json")
    ruta_resp = os.path.join(carpeta, "respuesta-tanda.json")
    if not os.path.exists(ruta_estado):
        print("No hay estado-tanda.json: exporta primero (o ya se aplicó)."); sys.exit(1)
    est = json.load(open(ruta_estado, encoding="utf-8"))
    if (red.config("ultima_tanda") or "2000-01-01T00:00:00Z") != est["desde"] and not forzar:
        print("Ha habido otra tanda después de exportar; no aplico para no duplicar (usa --forzar si aun así quieres)."); sys.exit(1)
    texto = open(ruta_resp, encoding="utf-8").read()
    try:
        res = leer_json(texto)
    except Exception as e:
        red.apuntar_consumo(quien="tanda", para="reacciones", modelo=(red.config("tanda", {}) or {}).get("modelo_externo", "gemini-antigravity"),
                            error=f"respuesta externa no es JSON: {str(e)[:300]}")
        print("La respuesta no es un JSON válido:", e); sys.exit(1)
    ESCALA = est.get("escala", ESCALA)
    n = aplicar(res, est["cuentas"])
    red.poner_config("ultima_tanda", est["hasta"])
    prompt = open(os.path.join(carpeta, "prompt-tanda.txt"), encoding="utf-8").read() if os.path.exists(os.path.join(carpeta, "prompt-tanda.txt")) else ""
    red.apuntar_consumo(quien="tanda", para="reacciones", modelo=(red.config("tanda", {}) or {}).get("modelo_externo", "gemini-antigravity"),
                        tokens_in=len(prompt) // 4, tokens_out=len(texto) // 4, nota=json.dumps({**n, "externa": True, "estimado": True}))
    os.replace(ruta_estado, ruta_estado + ".aplicado")
    os.replace(ruta_resp, ruta_resp + ".aplicado")
    print(f"OK {n} (tanda externa)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prueba", action="store_true")
    ap.add_argument("--sin-guardar", action="store_true")
    ap.add_argument("--ya", action="store_true", help="todo aparece en unos 10 minutos (para revisar)")
    ap.add_argument("--partida", action="store_true", help="tanda en pasos cortos (para modelos locales); también con config tanda.modo = partida")
    ap.add_argument("--exportar", metavar="CARPETA", help="deja el prompt de la tanda en CARPETA para que lo responda otro (p. ej. Gemini en Antigravity)")
    ap.add_argument("--aplicar", metavar="CARPETA", help="aplica la respuesta-tanda.json que haya en CARPETA")
    ap.add_argument("--forzar", action="store_true", help="con --aplicar: aplica aunque haya habido otra tanda después de exportar")
    a = ap.parse_args()
    if a.aplicar:
        return aplicar_externa(a.aplicar, a.forzar)
    global ESCALA
    if a.ya:
        ESCALA = 0.02

    cfg = red.config("tanda", {}) or {}
    if not cfg.get("activa", True) and not a.prueba:
        print("Tanda parada en config."); return
    if cfg.get("externo") and not (a.exportar or a.prueba or a.sin_guardar):
        # La tanda la hace otro (Antigravity). El cron solo entra de respaldo si lleva demasiado sin pasar.
        ult = red.config("ultima_tanda")
        margen = float(cfg.get("externo_margen_h", 6))
        try:
            horas = (datetime.now(timezone.utc) - datetime.fromisoformat(ult.replace("Z", "+00:00"))).total_seconds() / 3600
        except Exception:
            horas = 999
        if horas < margen:
            print(f"Tanda externa activa: la última fue hace {horas:.1f} h (respaldo a las {margen:g} h)."); return
        print(f"Tanda externa sin noticias desde hace {horas:.1f} h: la hago yo de respaldo.")
    modelo = cfg.get("modelo", "grok-4.7")
    if proveedor_local():
        modelo = proveedor_local()[1]
    elif proveedor_gemini():
        modelo = proveedor_gemini()[2]
    elif os.environ.get("MODELO_CMD") or cfg.get("modelo_cmd"):
        modelo = cfg.get("modelo_gemini") or modelo  # el comando recibe este nombre en {"modelo"}
    tope = int(cfg.get("tope_diario_tokens", 150000))
    gastado = gastado_hoy()
    if gastado >= tope and not a.prueba:
        red.apuntar_consumo(quien="tanda", para="reacciones", modelo=modelo, saltada=True, nota=f"tope: {gastado}/{tope}")
        print(f"Saltada: hoy van {gastado} tokens y el tope es {tope}."); return

    desde = red.config("ultima_tanda") or "2000-01-01T00:00:00Z"
    hasta = red.ahora_iso()
    if a.partida or cfg.get("modo") == "partida":
        if a.prueba:
            print("Modo partida: para probar sin escribir en la red usa --sin-guardar."); return
        sys.modules["tanda"] = sys.modules[__name__]  # que tanda_partida use este mismo módulo (y su ESCALA)
        import tanda_partida
        tanda_partida.ejecutar(a, cfg, modelo, desde, hasta)
        return
    material, cuentas = montar(desde, int(cfg.get("max_posts_por_tanda", 12)))
    if material is None:
        if not a.prueba and not a.sin_guardar:
            red.poner_config("ultima_tanda", hasta)
        print("Nada nuevo desde", desde); return

    if a.exportar:
        return exportar(a.exportar, material, cuentas, desde, hasta)
    mensajes = [{"role": "system", "content": reglas()}, {"role": "user", "content": material}]
    if a.prueba:
        print(reglas() + "\n-----\n" + material)
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
