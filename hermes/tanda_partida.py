#!/usr/bin/env python3
"""Tanda de Raven partida en pasos cortos, pensada para modelos locales (Mistral, Qwen…).

En vez de un encargo enorme con todo, cada cosa es una llamada pequeña:
  1. un post por autor (el código elige los autores, no el modelo);
  2. los comentarios de cada post de las hermanas o de Alberto;
  3. las respuestas a Alberto (comentarios y MD);
  4. hasta 2 posts de Nocturna de las creadoras;
  5. la crónica, solo con lo que ha pasado de verdad.
El código hace lo que los modelos pequeños hacen mal: el día y la hora, quién escribe, las cifras,
la memoria, y rechazar copias, nombres prohibidos y textos raros. Al final monta el mismo `res`
que la tanda normal y lo aplica con `tanda.aplicar`.

Se activa con `tanda.py --partida` o con config tanda.modo = "partida".
"""
import difflib, json, random, re, sys, time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import red
import tanda as T

DIAS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]  # mismo orden que config.agenda.dia
PROHIBIDO = re.compile(r"\b(valeria|aika|shiro|alberto|cristina|academia|aircrew)\b", re.I)  # nombres privados y vida real

SISTEMA = """Escribes UNA cosa para una red social FALSA y privada tipo X/Twitter llamada Raven. Todo es ficción y parodia, estilo GTA.
- Español de España como en X de verdad: corto, minúsculas, jerga, a veces faltas leves. Tacos sin miedo (joder, hostia, coño, gilipollas…) y comentarios salidos de los que hay en cualquier red.
- NO: describir actos sexuales, nada con menores, odio por raza/religión/orientación, amenazas.
- No suenes a IA ni a anuncio: nada de frases redondas, ni hashtags de marketing, ni «la vida adulta es un meme». Cada persona habla como habla ella.
- NO TE INVENTES HECHOS: solo lo que se te da (día, agenda, crónica). Si algo no consta, no lo afirmes.
- La streamer se llama VeeNoir (@veenoir) y la cantante anónima Yoruha (@yoruha_). Nunca uses otros nombres para ellas. Nadie sabe la cara ni la vida privada de Yoruha.
- No copies ni reescribas posts que ya existen: di algo nuevo.
Devuelve SOLO el objeto JSON que se te pide, sin nada más."""


def ahora_madrid():
    return datetime.now(ZoneInfo("Europe/Madrid"))


def proximos(agenda, ahora=None):
    """Los directos de los próximos 7 días con su fecha real: [(fecha, dia_semana, evento)]."""
    ahora = ahora or ahora_madrid()
    hoy = (ahora.weekday() + 1) % 7  # 0 = domingo, como la agenda
    out = []
    for e in agenda or []:
        try:
            dif = (int(e["dia"]) - hoy) % 7
            h, m = map(int, str(e["hora"]).split(":"))
        except Exception:
            continue
        if dif == 0 and (ahora.hour, ahora.minute) > (h, m):
            dif = 7  # el de hoy ya pasó: el siguiente es la semana que viene
        out.append((ahora.date() + timedelta(days=dif), int(e["dia"]), e))
    return sorted(out, key=lambda x: (x[0], str(x[2].get("hora"))))


def contexto_dia(agenda):
    """Día, hora y agenda ya resueltos con fecha, para que el modelo no se líe."""
    ahora = ahora_madrid()
    hoy = (ahora.weekday() + 1) % 7
    lineas = [f"Ahora es {DIAS[hoy]} {ahora.day}/{ahora.month}, las {ahora.strftime('%H:%M')} en España."]
    if ahora.hour < 6:
        ayer = DIAS[(hoy - 1) % 7]
        lineas.append(f"Es de madrugada: para la gente sigue siendo la noche del {ayer}. Para hablar de directos NO uses «hoy» ni «mañana»: di el día de la semana.")
    prox = proximos(agenda, ahora)
    lineas.append("Agenda de los próximos días (lo ÚNICO que hay; no existe ningún otro directo ni concierto):")
    for f, d, e in prox:
        dif = (f - ahora.date()).days
        cuando = {0: "HOY", 1: "mañana"}.get(dif, "el") if ahora.hour >= 6 else "el"
        lineas.append(f"- {e['quien']} (@{e.get('usuario', '')}): {e['que']}, {cuando} {DIAS[d]} {f.day}/{f.month} a las {e['hora']}.")
    dias_con = {d for _, d, _ in prox}
    sin = [DIAS[d] for d in range(7) if d not in dias_con]
    if hoy not in dias_con or all((f - ahora.date()).days != 0 for f, _, _ in prox):
        lineas.append(f"HOY ({DIAS[hoy]}) NO hay ningún directo.")
    if sin:
        lineas.append("Días SIN nada: " + ", ".join(sin) + ". No digas que hay directo esos días.")
    lineas.append("No pongas fechas con número (27/11…) salvo las de esta agenda.")
    return "\n".join(lineas)


CLAVE_AGENDA = re.compile(r"\b(directo|stream|en vivo|lol|gta|canta|concierto|twitch)\b", re.I)
DIA_RE = re.compile(r"\b(domingo|lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|hoy|mañana)\b", re.I)
FECHA_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})\b")
_SIN_TILDE = {"miercoles": "miércoles", "sabado": "sábado"}


def agenda_mal(texto, agenda):
    """Motivo si el texto se inventa una fecha o un día de directo; None si cuadra con la agenda."""
    ahora = ahora_madrid()
    prox = proximos(agenda, ahora)
    fechas = {(f.day, f.month) for f, _, _ in prox} | {(ahora.day, ahora.month)}
    menciona = {e.get("usuario", "").lower() for _, _, e in prox if e.get("usuario") and "@" + e["usuario"].lower() in (texto or "").lower()}
    for d, m in FECHA_RE.findall(texto or ""):
        if (int(d), int(m)) not in fechas:
            return f"fecha inventada ({d}/{m})"
        de_quien = {e.get("usuario", "").lower() for f, _, e in prox if (f.day, f.month) == (int(d), int(m))}
        if menciona and de_quien and not (menciona & de_quien):
            return f"le pone a otra persona el directo del {d}/{m}"
    if not CLAVE_AGENDA.search(texto or ""):
        return None
    hoy = (ahora.weekday() + 1) % 7
    dias_con = {DIAS[d] for _, d, _ in prox}
    difs = {(f - ahora.date()).days for f, _, _ in prox}
    for w in DIA_RE.findall(texto or ""):
        w = _SIN_TILDE.get(w.lower(), w.lower())
        if w in ("hoy", "mañana") and ahora.hour < 6:
            return "de madrugada usa el día de la semana, no «hoy» ni «mañana»"
        if w == "hoy" and 0 not in difs and ahora.hour >= 6:
            return "dice que hoy hay directo y no lo hay"
        if w == "mañana" and 1 not in difs and ahora.hour >= 6:
            return "dice que mañana hay directo y no lo hay"
        if w in DIAS and w not in dias_con:
            return f"pone directo el {w} y ese día no hay"
    return None


def norm(t):
    return re.sub(r"[^a-zñáéíóúü0-9 ]", "", (t or "").lower())


def parecido(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def limpio(texto, quien=None):
    """Quita el «Nombre:» o «@usuario:» que a veces ponen delante."""
    t = (texto or "").strip()
    if quien:
        for n in (quien.get("nombre"), quien.get("usuario"), "@" + str(quien.get("usuario"))):
            if n and t.lower().startswith(str(n).lower() + ":"):
                t = t[len(str(n)) + 1:].strip()
    return t


def problema(texto, existentes, maximo=280, agenda=None):
    """Devuelve por qué se rechaza un texto, o None si vale."""
    t = (texto or "").strip()
    if len(t) < 8:
        return "vacío o demasiado corto"
    if len(t) > maximo:
        return "demasiado largo"
    if t.endswith("…") or t.endswith("..."):
        return "cortado con «…»"
    if PROHIBIDO.search(t):
        return "nombre privado o de la vida real"
    for e in existentes:
        if e and parecido(t, e) >= 0.55:
            return "copia o refrito de un post que ya existe"
    if agenda is not None:
        return agenda_mal(t, agenda)
    return None


class Motor:
    """Llama al modelo con mensajes cortos y lleva la cuenta de lo gastado."""

    def __init__(self, modelo):
        self.modelo, self.llamadas, self.tin, self.tout, self.ms, self.rechazos = modelo, 0, 0, 0, 0, []

    def pedir(self, encargo):
        t0 = time.time()
        texto, uso = T.llamar_modelo([{"role": "system", "content": SISTEMA}, {"role": "user", "content": encargo}], self.modelo)
        self.ms += int((time.time() - t0) * 1000); self.llamadas += 1
        self.tin += int(uso.get("prompt_tokens") or 0)
        self.tout += int(uso.get("completion_tokens") or 0)
        return T.leer_json(texto)

    def pedir_valido(self, encargo, comprobar, intentos=2):
        """Pide hasta `intentos` veces; `comprobar(res)` devuelve el motivo del rechazo o None."""
        for i in range(intentos):
            try:
                res = self.pedir(encargo if i == 0 else encargo + "\n\nLo anterior no valía. Escribe algo distinto y nuevo.")
            except Exception as e:
                self.rechazos.append(f"error: {e}"[:200]); continue
            motivo = comprobar(res)
            if not motivo:
                return res
            self.rechazos.append(motivo)
        return None


def ficha(c):
    s = f"@{c['usuario']} ({c['nombre']}, {c.get('seguidores', 0)} seguidores). Bio: {c.get('bio') or '—'}."
    if c.get("personalidad"):
        s += f" Cómo es: {T.corto(c['personalidad'], 300)}"
    if c.get("memoria"):
        s += f" Lo último que ha hecho: {T.corto(c['memoria'], 200)}"
    return s


def ultimos_de(cid, n=3):
    return [p["texto"] for p in red.sel("posts", cuenta_id=f"eq.{cid}", texto="not.is.null", select="texto", order="creado.desc", limit=n)]


def ejecutar(a, cfg, modelo, desde, hasta):
    motor = Motor(modelo)
    cuentas = red.sel("cuentas", plataforma=f"eq.{T.PLAT}", select="id,tipo,quien,nombre,usuario,bio,seguidores,personalidad,memoria")
    por_id = {c["id"]: c for c in cuentas}
    por_user = {c["usuario"].lower(): c for c in cuentas}
    ahora = red.ahora_iso()
    agenda = red.config("agenda", []) or []
    dia = contexto_dia(agenda)
    cron_prev = (red.config("cronica", {}) or {}).get("lineas") or []
    cronica = "\n".join("- " + l for l in cron_prev[:10]) or "(vacía)"

    hermanas = [c for c in cuentas if c["tipo"] == "hermana"]
    alberto = [c for c in cuentas if c["tipo"] == "alberto"]
    fans = [c for c in cuentas if c["tipo"] == "fan"]
    fijos = [c for c in cuentas if c["tipo"] == "fijo" and not str(c.get("quien") or "").startswith(("famoso", "famosa"))]
    famosos = [c for c in cuentas if str(c.get("quien") or "").startswith(("famoso", "famosa"))]
    marcas = [c for c in cuentas if c["tipo"] == "marca"]
    creadoras = [c for c in fijos if str(c.get("quien") or "").startswith("creadora_")]

    # Lo que ya hay (para no copiarlo) y lo último que se comenta (para tener de qué hablar)
    recientes = red.sel("posts", plataforma=f"eq.{T.PLAT}", texto="not.is.null", **{"and": f"(creado.lte.{ahora})"},
                        select="cuenta_id,texto,creado", order="creado.desc", limit=40)
    existentes = [p["texto"] for p in recientes]
    charla = "\n".join(f"- @{por_id.get(p['cuenta_id'], {}).get('usuario', '?')}: «{T.corto(p['texto'], 120)}»" for p in recientes[:8])

    res = {"posts": [], "respuestas": [], "posts_nuevos": [], "md": [], "fans_nuevos": [], "nocturna": [], "memoria": [], "cronica": []}
    eventos = []  # lo que pasa en esta tanda, para la crónica

    # ---- 1. Comentarios a lo nuevo de las hermanas y de Alberto ----
    ids_clave = [c["id"] for c in hermanas + alberto]
    if ids_clave:
        nuevos = red.sel("posts", cuenta_id=f"in.({','.join(ids_clave)})", plataforma=f"eq.{T.PLAT}", creado=f"gt.{desde}",
                         **{"and": f"(creado.lte.{ahora})"}, select="id,cuenta_id,texto,creado", order="creado.asc", limit=6)
        for p in nuevos:
            autor = por_id[p["cuenta_id"]]
            es_alberto = autor["tipo"] == "alberto"
            gente = random.sample(fans, min(3 if not es_alberto else 1, len(fans))) + random.sample(fijos, min(2, len(fijos)))
            nombres = [g["usuario"] for g in gente]
            encargo = (f"{dia}\n\nCrónica de Raven:\n{cronica}\n\nPost nuevo de @{autor['usuario']}: «{p['texto']}»\n\n"
                       f"Escribe entre {2 if es_alberto else 3} y {len(gente)} comentarios a ESE post, cada uno de una de estas cuentas "
                       f"y con su forma de ser:\n" + "\n".join(ficha(g) for g in gente) +
                       '\n\nJSON: {"comentarios":[{"usuario":"...","texto":"...","responde_a":null}]} '
                       '("responde_a": null o el índice de otro comentario de la lista al que contesta).')

            def ok(r, nombres=nombres):
                cs = (r or {}).get("comentarios") or []
                if not cs:
                    return "sin comentarios"
                for c in cs:
                    if (c.get("usuario") or "").lstrip("@") not in nombres:
                        return "comenta alguien que no estaba en la lista"
                    c["texto"] = limpio(c.get("texto"), por_user.get((c.get("usuario") or "").lstrip("@").lower()))
                    m = problema(c.get("texto"), existentes, 240, agenda)
                    if m:
                        return m
                return None
            r = motor.pedir_valido(encargo, ok)
            if r:
                cs = r["comentarios"][:len(gente)]
                for i, c in enumerate(cs):
                    c["en_min"] = random.randint(2, 40) if i < 2 else random.randint(40, 300)
                    c["likes"] = random.randint(0, 60)
                base = T.cifras(autor.get("seguidores"))
                res["posts"].append({"id": p["id"], "vistas": base["vistas_sim"], "likes": base["likes_sim"], "reposts": base["reposts_sim"], "comentarios": cs})
                eventos.append(f"@{autor['usuario']} publicó «{T.corto(p['texto'], 80)}» y le comentaron " + ", ".join("@" + c["usuario"].lstrip("@") for c in cs))

    # ---- 2. Respuestas a Alberto: sus comentarios y sus MD ----
    if alberto:
        coms = red.sel("comentarios", cuenta_id=f"eq.{alberto[0]['id']}", creado=f"gt.{desde}", **{"and": f"(creado.lte.{ahora})"},
                       select="id,post_id,texto", order="creado.asc", limit=5)
        for c in coms:
            post = red.sel("posts", id=f"eq.{c['post_id']}", select="cuenta_id,texto")
            dueno = por_id.get(post[0]["cuenta_id"]) if post else None
            quien = dueno if dueno and dueno["tipo"] in ("fijo", "marca") else (random.choice(fijos) if fijos else None)
            if not quien:
                continue
            encargo = (f"{dia}\n\nPost de @{dueno['usuario'] if dueno else '?'}: «{T.corto(post[0]['texto'] if post else '', 200)}»\n"
                       f"Comentario de @alberto_16: «{c['texto']}»\n\nEres {ficha(quien)}\nContesta a ese comentario, con tu forma de ser. "
                       'JSON: {"texto":"..."}')
            r = motor.pedir_valido(encargo, lambda r: problema(limpio((r or {}).get("texto"), quien), existentes, 240, agenda))
            if r:
                res["respuestas"].append({"comentario_id": c["id"], "usuario": quien["usuario"], "texto": limpio(r["texto"], quien), "likes": random.randint(0, 20), "en_min": random.randint(5, 90)})
                eventos.append(f"@{quien['usuario']} contestó a un comentario de @alberto_16")
        ids_fijos = [c["id"] for c in fijos + marcas + fans]
        mds = red.sel("mensajes", plataforma=f"eq.{T.PLAT}", de=f"eq.{alberto[0]['id']}", para=f"in.({','.join(ids_fijos) or '0'})",
                      creado=f"gt.{desde}", select="id,para,texto", order="creado.asc", limit=4) if ids_fijos else []
        for m in mds:
            quien = por_id.get(m["para"])
            if not quien:
                continue
            encargo = f"{dia}\n\nEres {ficha(quien)}\n@alberto_16 te ha mandado este MD: «{m['texto']}»\nContéstale por MD, con tu forma de ser. " + 'JSON: {"texto":"..."}'
            r = motor.pedir_valido(encargo, lambda r: problema(limpio((r or {}).get("texto"), quien), [], 400, agenda))
            if r:
                res["md"].append({"de": quien["usuario"], "para": "alberto_16", "texto": limpio(r["texto"], quien), "en_min": random.randint(10, 180)})
                eventos.append(f"@{quien['usuario']} contestó un MD de @alberto_16")

    # ---- 3. Posts nuevos: el código elige quién escribe ----
    autores = random.sample(fans, min(3, len(fans))) + random.sample(fijos, min(3, len(fijos)))
    autores += random.sample(famosos, min(1, len(famosos))) + random.sample(marcas, min(1 if random.random() < 0.5 else 0, len(marcas)))
    # un fan nuevo, inventado aparte
    usados = ", ".join("@" + c["usuario"] for c in cuentas)
    r = motor.pedir_valido(
        "Inventa UNA cuenta nueva de fan de Raven (gente normal de España: curro, estudios, gym, juegos, anime, música). "
        f"No puede llamarse como ninguna de estas: {T.corto(usados, 900)}.\n"
        'JSON: {"usuario":"nombre_de_usuario","nombre":"nombre visible","bio":"bio corta","avatar":"prompt corto en inglés de su foto de perfil (persona inventada, mascota o avatar anime genérico, sin texto)"}',
        lambda r: None if re.fullmatch(r"\w{3,20}", (r or {}).get("usuario", "").lstrip("@")) and (r or {}).get("usuario", "").lstrip("@").lower() not in por_user else "usuario no válido o repetido")
    if r:
        r["usuario"] = r["usuario"].lstrip("@")
        res["fans_nuevos"].append(r)
        autores.append({"usuario": r["usuario"], "nombre": r.get("nombre") or r["usuario"], "bio": r.get("bio"), "seguidores": random.randint(20, 900), "tipo": "fan", "id": None})
    random.shuffle(autores)
    minutos = sorted(random.sample(range(0, 420), len(autores))) if autores else []
    for autor, en_min in zip(autores, minutos):
        suyos = ultimos_de(autor["id"]) if autor.get("id") else []
        encargo = (f"{dia}\n\nCrónica de Raven (lo que viene pasando):\n{cronica}\n\nLo último que se comenta:\n{charla}\n\n"
                   f"Eres {ficha(autor)}\n" + (f"Tus últimos posts (NO los repitas):\n" + "\n".join(f"- «{T.corto(t, 140)}»" for t in suyos) + "\n" if suyos else "") +
                   "\nEscribe UN post nuevo tuyo: tu vida, tu día, algo de la agenda o de la crónica, o un pique con alguien de arriba. "
                   "Si menciona un directo, usa el día exacto de la agenda.\n"
                   'JSON: {"texto":"...","foto":null o "prompt corto en inglés de la foto que acompaña al post","sale":true si sales tú en la foto}')
        def ok_post(r, suyos=suyos, autor=autor):
            t = limpio((r or {}).get("texto"), autor)
            if r is not None:
                r["texto"] = t
            if any(parecido(t, x) >= 0.42 for x in suyos):
                return "repite un post suyo de antes"
            return problema(t, existentes + [p["texto"] for p in res["posts_nuevos"]], 280, agenda)
        r = motor.pedir_valido(encargo, ok_post)
        if r:
            res["posts_nuevos"].append({"usuario": autor["usuario"], "texto": r["texto"], "cita": None, "en_min": en_min,
                                        "foto": r.get("foto") if random.random() < 0.45 else None, "sale": bool(r.get("sale"))})
            eventos.append(f"@{autor['usuario']} publicó «{T.corto(r['texto'], 90)}»")

    # ---- 4. Nocturna: hasta 2 creadoras ----
    for c in random.sample(creadoras, min(2 if random.random() < 0.6 else 1, len(creadoras))):
        encargo = (f"Eres {ficha(c)}\nTienes página de pago en Nocturna (tipo OnlyFans). Escribe UN post nuevo para tus suscriptores: "
                   "texto gancho con picardía, sin describir actos sexuales.\n"
                   'JSON: {"texto":"...","precio":null o un número entre 4.99 y 14.99,"fotos":de 3 a 15,"oculto":"lo que se lee al desbloquear, con picardía y sin describir actos"}')
        r = motor.pedir_valido(encargo, lambda r: problema((r or {}).get("texto"), existentes, 300))
        if r:
            r.update(usuario=c["usuario"], en_min=random.randint(30, 400))
            res["nocturna"].append(r)
            eventos.append(f"@{c['usuario']} subió un post nuevo a Nocturna")

    # ---- 5. Memoria (la escribe el código, solo con lo que ha pasado) ----
    for p in res["posts_nuevos"]:
        k = por_user.get(p["usuario"].lower())
        if k and k["tipo"] in ("fijo", "marca"):
            res["memoria"].append({"usuario": k["usuario"], "nota": f"publicó «{T.corto(p['texto'], 70)}»"})

    # ---- 6. Crónica: solo hechos de la lista ----
    if eventos:
        conocidos = {c["usuario"].lower() for c in cuentas} | {f["usuario"].lower() for f in res["fans_nuevos"]}
        encargo = (f"{dia}\n\nCrónica anterior:\n{cronica}\n\nLo que ha pasado ahora en Raven:\n" + "\n".join("- " + e for e in eventos) +
                   "\n\nDevuelve la crónica actualizada: de 6 a 12 líneas cortas con los hilos abiertos (piques, colabos, bromas, cosas anunciadas). "
                   "Quita lo cerrado o viejo. SOLO hechos de las dos listas de arriba, sin añadir nada.\n"
                   'JSON: {"cronica":["...","..."]}')

        def ok_cron(r):
            ls = (r or {}).get("cronica") or []
            if not 3 <= len(ls) <= 14:
                return "crónica con un número raro de líneas"
            for l in ls:
                for u in re.findall(r"@?([a-z0-9_]{3,30})", str(l).lower()):
                    if "@" + u in str(l).lower() and u not in conocidos:
                        return f"la crónica menciona a alguien que no existe (@{u})"
            return None
        r = motor.pedir_valido(encargo, ok_cron)
        res["cronica"] = (r or {}).get("cronica") or cron_prev

    resumen = (f"partida · {motor.llamadas} llamadas · entrada {motor.tin} · salida {motor.tout} · {motor.ms/1000:.1f} s · "
               f"{len(motor.rechazos)} rechazos")
    if a.sin_guardar:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n[sin guardar] {resumen}")
        if motor.rechazos:
            print("Rechazos:", json.dumps(motor.rechazos, ensure_ascii=False))
        red.apuntar_consumo(quien="tanda", para="reacciones", modelo=modelo, tokens_in=motor.tin, tokens_out=motor.tout,
                            duracion_ms=motor.ms, nota=f"sin-guardar (prueba) · {resumen}")
        return
    n = T.aplicar(res, cuentas)
    red.poner_config("ultima_tanda", hasta)
    red.apuntar_consumo(quien="tanda", para="reacciones", modelo=modelo, tokens_in=motor.tin, tokens_out=motor.tout,
                        duracion_ms=motor.ms, nota=json.dumps({**n, "modo": "partida", "llamadas": motor.llamadas, "rechazos": len(motor.rechazos)}))
    print(f"OK {n} · {resumen}")
