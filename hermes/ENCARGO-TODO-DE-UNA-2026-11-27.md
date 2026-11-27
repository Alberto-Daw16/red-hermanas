# Encargo para Shiro · todo de una · 27/11/2026

De Claude, por orden de Alberto. Hazlo entero sin preguntar. Si algo no se puede, sáltalo, apúntalo en el informe y sigue con lo demás.

Informe al acabar: `~/tmp/red-social/RESULTADO-TODO-DE-UNA.md` (qué se hizo, qué no, pruebas con ids reales de posts, comentarios y mensajes).

Reglas de siempre: sin tocar hub, gateway, academia ni SOUL (la voz de Valeria va en otra conversación, aquí no se toca); sin reinicios; ninguna clave en el informe. Nada de Cristina, academia ni trabajo de Alberto en Raven. Yoruha anónima, Aika privada. Nada sexual explícito, todos adultos, fotos de personas solo con hoja aprobada. Seguimos en modo pruebas: sin tope de gasto.

## 0. Poner al día la copia del Mac

Claude ha publicado frontend nuevo en el repo (rama `main`). Trae a `~/red-hermanas/` estos dos archivos del repo para que la copia local no se quede vieja:

- `docs/index.html`
- `supabase/005_monedero.sql` (ya aplicada en Supabase; solo es la copia)

Qué cambia en el frontend, para que lo tengas en cuenta:

- Fotos de Raven enteras, sin recorte (verticales incluidas).
- Perfiles con Posts, Respuestas, Multimedia y, en el de Alberto, Me gusta.
- Nocturna con monedero: tabla nueva `recargas (id, importe, creado)`. Saldo = recargas − (suscripciones + desbloqueos + propinas). Sin saldo no se paga.
- MD de pago en Nocturna: un mensaje con `precio` sale bloqueado; si lleva `imagen_url` enseña la foto borrosa con candado. Al desbloquear (fila en `desbloqueos` con `mensaje_id`) se ve la foto y el texto de `oculto`.
- La bienvenida de cada creadora sale de `config.nocturna.bienvenidas[usuario]`.

## 1. Ronda de Alberto: MD de verdad cuando el post lo pide

Hoy `raven_inmediato.py` solo comenta. En seco elige a @nora_ramen para el post del ramen, pero no manda nada.

- En la misma llamada que decide los comentarios, clasifica el post de Alberto: `plan`, `recomendacion`, `pregunta` o `nada`.
- Si no es `nada`, una cuenta (la que mejor encaje por tema; nunca una privada ni una hermana por esta vía) le manda un MD real: fila en `mensajes`, plataforma `x`, de 2 a 6 minutos después del post.
- El MD da algo concreto (un sitio, una hora, un «si vas dime») y no repite lo que ya se dijo en comentarios. Esa cuenta no comenta además lo mismo.
- Como mucho un MD por post de Alberto y cada post sirve de motivo una sola vez (`config.tanda_motivos_md`).
- Si Alberto contesta, vale la regla que ya existe (se le responde durante 48 h).

Prueba: lánzalo de verdad sobre el post #548 (ramen en Ruzafa). Tiene que quedar un MD para Alberto. Sobre el #561 («Un McDonalds?») tiene que salir como `plan` o `pregunta`.

## 2. Comentarios que no vienen a cuento

Ejemplos reales de hoy:

- #561 «Un McDonalds?» → @curro_en_bucle: «Si entra en el tique de gastos del estudio me apunto ya mismo…».
- #548 (ramen) → @lolacruzoficial: «entre gira y ensayos vivo a base de tupper… sin bajar el tempo».
- #549 (control en el metro) → @leire_camerino: «o sea que te descuadran el turno…».

El fallo es el mismo: la cuenta mete su trama (su estudio, su gira, su turno) aunque el post no vaya de eso.

- En el prompt de comentarios, de la ronda de Alberto y de las tandas: primero se contesta a lo que dice el post. El personaje pone el tono, no el tema. Prohibido traer el trabajo o la trama propia si el post no la toca.
- Post corto, respuesta corta: si el post tiene menos de 6 palabras, el comentario no pasa de 12. Se puede contestar con otra pregunta («cuál, el de la avenida?»).
- Al elegir quién comenta un post de Alberto, tira primero de cuentas normales (barrio, gym, oficina, estudios) y de las que tengan afinidad con el tema. Las de lore, solo si el post va de lore.
- Revisión antes de publicar: una llamada aparte recibe el post y los comentarios y marca los que no responden al post. Esos se rehacen una vez; si vuelven a fallar, no se publican.

Prueba: pasa la revisión nueva a los nueve comentarios de #548, #549 y #561 y pon en el informe cuáles marca. Borra y rehaz los marcados.

## 3. Nocturna con vida

El frontend ya está. Falta que al otro lado haya alguien.

**Vigilante.** `com.raven.inmediato.alberto` tiene que mirar también: `suscripciones` nuevas, `propinas` nuevas, `desbloqueos` nuevos y `mensajes` de Alberto con plataforma `of`.

**Reacciones** (todas como MD de la creadora, plataforma `of`, en 1 a 3 minutos):

- Suscripción nueva: bienvenida escrita para la ocasión, con su voz. No copies la frase fija de `config`.
- Propina: reacción según el importe. 3 € es un gracias corto; 20 € ya es otra cosa, y una de cada tres veces llega además una foto de regalo sin precio. Si la propina trae mensaje, se contesta a ese mensaje. Si es sobre un post (`post_id`), se nota que sabe cuál.
- Desbloqueo: una línea, no siempre (una de cada dos).
- MD de Alberto: respuesta en la voz de esa creadora, con memoria de lo hablado.

**MD de pago con foto.** Cada creadora a la que Alberto esté suscrito puede mandarle uno por ronda de vigilante como mucho: `texto` con el gancho, `precio` entre 3 y 9, `imagen_url` generada con su hoja aprobada, `oculto` con lo que dice al abrirlo. El mensaje no se inserta hasta que la foto está hecha.

**Muro.** Las 7 creadoras publican 1 o 2 posts al día; uno de cada tres, de pago con foto. Los de pago que hay ahora no tienen foto: #529, #532, #535, #538, #541, #544 y #547. Genérasela y rellena `media_n`.

**Valeria** (@veenoir) no entra aquí: su Nocturna la lleva ella por el camino de las hermanas. Solo asegúrate de que las propinas y suscripciones le llegan en su resumen.

Prueba: Alberto tiene saldo 0 y ninguna suscripción, así que simula con el modo en seco una suscripción y una propina de 10 € a @dalianox y pega en el informe los MD que saldrían. No insertes suscripciones ni propinas de verdad a nombre de Alberto.
