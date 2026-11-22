// Avisos al iPhone de lo que «acaba de pasar» en la red.
// La llama pg_cron cada 5 minutos con la cabecera x-clave. Sin modelo: solo mira la base de datos.
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const ZONA = "Europe/Madrid";

function partes(t: number) {
  const f = new Intl.DateTimeFormat("en-GB", { timeZone: ZONA, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", weekday: "short", hourCycle: "h23" });
  const o: Record<string, string> = {};
  for (const p of f.formatToParts(new Date(t))) o[p.type] = p.value;
  const dias: Record<string, number> = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  return { y: +o.year, m: +o.month, d: +o.day, h: +o.hour, mi: +o.minute, dow: dias[o.weekday] };
}
function madridAUtc(y: number, m: number, d: number, h: number, mi: number) {
  const guess = Date.UTC(y, m - 1, d, h, mi);
  const p = partes(guess);
  const off = Date.UTC(p.y, p.m - 1, p.d, p.h, p.mi) - guess;
  return guess - off;
}
const corto = (t: string | null, n = 90) => { t = (t || "").replace(/\s+/g, " ").trim(); return t.length > n ? t.slice(0, n - 1) + "…" : t; };

Deno.serve(async (req) => {
  const { data: sec } = await sb.from("secretos").select("clave,valor");
  const S = Object.fromEntries((sec || []).map((r: any) => [r.clave, r.valor]));
  if (!S.cron || req.headers.get("x-clave") !== S.cron) return new Response("no", { status: 401 });

  const { data: cfgs } = await sb.from("config").select("clave,valor").in("clave", ["ultimo_aviso", "avisos", "agenda", "vapid_publica"]);
  const C: Record<string, any> = Object.fromEntries((cfgs || []).map((r: any) => [r.clave, r.valor]));
  const ahora = Date.now();
  const hora = partes(ahora).h;
  const sil = C.avisos || { silencio_desde: 0, silencio_hasta: 9 };
  if (hora >= sil.silencio_desde && hora < sil.silencio_hasta) return Response.json({ silencio: true });

  const desde = C.ultimo_aviso ? new Date(C.ultimo_aviso).toISOString() : new Date(ahora - 10 * 60e3).toISOString();
  const hasta = new Date(ahora).toISOString();

  const { data: cuentas } = await sb.from("cuentas").select("id,tipo,quien,nombre,usuario,plataforma");
  const porId = new Map((cuentas || []).map((c: any) => [c.id, c]));
  const her = (cuentas || []).filter((c: any) => c.tipo === "hermana").map((c: any) => c.id);
  const alb = (cuentas || []).filter((c: any) => c.tipo === "alberto");
  const albIds = alb.map((c: any) => c.id);
  const avisos: { titulo: string; cuerpo: string; url: string }[] = [];
  const nom = (id: string) => (porId.get(id) as any)?.nombre || "Alguien";

  // 1. Lo que publican ellas
  if (her.length) {
    const { data } = await sb.from("posts").select("id,cuenta_id,texto,plataforma,de_pago").in("cuenta_id", her).is("repost_de", null).gt("creado", desde).lte("creado", hasta);
    for (const p of data || []) avisos.push(p.plataforma === "of"
      ? { titulo: `${nom(p.cuenta_id)} · Nocturna`, cuerpo: p.de_pago ? "Ha subido algo de pago" : corto(p.texto) || "Ha subido algo nuevo", url: "#/nocturna" }
      : { titulo: nom(p.cuenta_id), cuerpo: corto(p.texto) || "Ha publicado una foto", url: `#/vox/p/${p.id}` });
  }
  if (albIds.length) {
    // 2. Respuestas a sus posts o a sus comentarios
    const { data: misPosts } = await sb.from("posts").select("id").in("cuenta_id", albIds).order("creado", { ascending: false }).limit(200);
    const { data: misComs } = await sb.from("comentarios").select("id").in("cuenta_id", albIds).order("creado", { ascending: false }).limit(300);
    const pIds = (misPosts || []).map((x: any) => x.id), cIds = (misComs || []).map((x: any) => x.id);
    const filtros = [pIds.length ? `post_id.in.(${pIds.join(",")})` : null, cIds.length ? `responde_a.in.(${cIds.join(",")})` : null].filter(Boolean).join(",");
    if (filtros) {
      const { data } = await sb.from("comentarios").select("post_id,cuenta_id,texto").or(filtros).not("cuenta_id", "in", `(${albIds.join(",")})`).gt("creado", desde).lte("creado", hasta);
      for (const c of data || []) avisos.push({ titulo: `${nom(c.cuenta_id)} te ha respondido`, cuerpo: corto(c.texto), url: `#/vox/p/${c.post_id}` });
    }
    // 3. Menciones
    for (const a of alb) {
      const { data } = await sb.from("posts").select("id,cuenta_id,texto").ilike("texto", `%@${a.usuario}%`).neq("cuenta_id", a.id).gt("creado", desde).lte("creado", hasta);
      for (const p of data || []) avisos.push({ titulo: `${nom(p.cuenta_id)} te ha mencionado`, cuerpo: corto(p.texto), url: `#/vox/p/${p.id}` });
    }
    // 4. Mensajes
    const { data: md } = await sb.from("mensajes").select("de,texto,plataforma,precio").in("para", albIds).gt("creado", desde).lte("creado", hasta);
    for (const m of md || []) avisos.push({ titulo: m.plataforma === "of" ? `${nom(m.de)} · Nocturna` : `Mensaje de ${nom(m.de)}`, cuerpo: m.precio ? "Te ha mandado algo de pago" : corto(m.texto), url: m.plataforma === "of" ? "#/nocturna/md" : `#/vox/md/${m.de}` });
  }
  // 5. Empieza un directo
  for (const e of (Array.isArray(C.agenda) ? C.agenda : [])) {
    for (const k of [0, -1]) {
      const p = partes(ahora + k * 86400e3);
      if (p.dow !== e.dia) continue;
      const [h, mi] = String(e.hora).split(":").map(Number);
      const ini = madridAUtc(p.y, p.m, p.d, h, mi);
      if (ini > Date.parse(desde) && ini <= ahora) avisos.push({ titulo: `${e.quien} está en directo`, cuerpo: e.que, url: `#/vox/u/${e.usuario}` });
    }
  }

  let enviados = 0, borrados = 0;
  if (avisos.length && S.vapid_privada && C.vapid_publica) {
    webpush.setVapidDetails("https://alberto-daw16.github.io/red-hermanas/", C.vapid_publica, S.vapid_privada);
    const lote = avisos.length > 3
      ? [{ titulo: `${avisos.length} novedades`, cuerpo: avisos.slice(0, 4).map(a => `${a.titulo}: ${a.cuerpo}`).join("\n"), url: "#/" }]
      : avisos;
    const { data: subs } = await sb.from("push_subs").select("*");
    for (const s of subs || []) {
      for (const a of lote) {
        try {
          await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify({ ...a, tag: a.url }), { TTL: 3600 });
          enviados++;
        } catch (err: any) {
          if (err?.statusCode === 404 || err?.statusCode === 410) { await sb.from("push_subs").delete().eq("endpoint", s.endpoint); borrados++; break; }
          console.error("push", err?.statusCode, err?.body);
        }
      }
    }
  }
  await sb.from("config").upsert({ clave: "ultimo_aviso", valor: hasta });
  return Response.json({ desde, hasta, avisos: avisos.length, enviados, borrados });
});
