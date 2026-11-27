# Encargo para Shiro · tanda final de pruebas · 27/11/2026

De Claude, por orden de Alberto. Hazlo entero sin preguntar. Si algo no sale, apúntalo en el informe y sigue.

Informe: `~/tmp/red-social/RESULTADO-TANDA-FINAL.md`, con los recuentos de abajo sacados de la base (no de memoria) y una lámina `LAMINA-TANDA-FINAL.png` con las fotos de la tanda.

Reglas fijas de siempre. Sin tocar hub, gateway, academia ni SOUL; sin reinicios. Seguimos en modo pruebas: no lances `fin_pruebas.py`.

Alberto dice que ha mejorado mucho. Si esta tanda sale bien, se cierra la fase de pruebas.

## 0. Frontend

Claude ha dejado ya en `~/red-hermanas/docs/index.html` la versión publicada. Novedad que te afecta: **las respuestas a un comentario (`responde_a`) ya no salen sueltas**, van plegadas debajo del comentario con un «Mostrar N respuestas». Así que en esta tanda tiene que haberlas, para que se vea.

## 1. La tanda

Una sola tanda a mano, variada, sin tema común.

**Cantidad mínima**
- 30 posts en Raven, de 30 cuentas distintas.
- Más de la mitad con foto (18 o más). Formato por escena, como ya está: vertical para gente, horizontal para sitios, cuadrado para objeto. Retratos solo con hoja aprobada.
- 4 comentarios o más en cada post (120 en total como poco), de cuentas variadas: que no comenten siempre las mismas seis.
- En al menos 10 posts, uno o dos de esos comentarios son respuesta a otro comentario (`responde_a` relleno), con el autor del post contestando a alguien en varios de ellos.

**Qué tiene que haber dentro**
- **Personajes:** 8 posts o más de cuentas de lore, cada una con lo suyo.
- **Gente normal:** el resto, de las plantillas de barrio, gym, oficina, estudios, oficio y demás.
- **Promoción de Nocturna:** 4 creadoras o más anuncian en Raven su Nocturna, con foto. Usa la plantilla `nocturna` que ya tienes en `cartera/plantillas/`.
- **Nocturna por dentro:** cada una de las 7 creadoras sube un post nuevo con foto en su muro; 2 o 3 de ellos, de pago.
- **Las tres hermanas:** tiene que haber algo de Valeria, de Yoruha y de Aika en esta tanda, por su camino de siempre (sus ratos y `raven_voces.py`, no el reparto): un post propio de cada una y al menos un comentario de cada una en posts de otros. Yoruha sin cara, Aika en su cuenta privada.
- **Cameos:** esa parte la lleva Alberto contigo directamente; este encargo no la define.

**Cómo**
- El revisor de comentarios pasa por todo, como en la tanda de las 20:04.
- Que no salgan los 30 posts con la misma hora exacta: repártelos hacia atrás en las últimas 3 horas (nada con fecha futura) y los comentarios después de su post.
- Ningún post visible hasta que su foto esté hecha.
- La tanda de las 20:04 pedía entre 10 y 14 posts y salieron 6. Mira por qué y cuéntalo en el informe; aquí no vale quedarse corto: si una pasada no llega, lanza otra hasta completar.

**Recuentos para el informe**
Posts, cuentas distintas, posts con foto, comentarios, comentarios con `responde_a`, mínimo de comentarios en un post, posts por tipo (lore, normal, promo Nocturna, hermanas), posts nuevos en Nocturna (con foto y de pago), tokens gastados y duración.

## 2. Avatares y banners de las hermanas

Siguen siendo los antiguos y están mal. Son estos:

| Cuenta | Avatar | Banner |
|---|---|---|
| @veenoir (Raven) | `gen/avatar-2.png` | `gen/banner-1.png` |
| @yoruha_ (Raven) | `gen/avatar-4.png` | `gen/banner-3.png` |
| @aika_kurenai (Raven) | `gen/avatar-71.png` | `gen/banner-72.png` |
| @veenoir (Nocturna) | `gen/avatar-7.png` | `gen/banner-6.png` |

Rehazlos con sus hojas aprobadas, al nivel de los 60 avatares nuevos del reparto, en WebP. Yoruha sin cara, ni en avatar ni en banner. Guarda antes los actuales en `~/tmp/red-social/copias/hermanas-2026-11-27/`, enlaza los nuevos en `cuentas` y pon una lámina `LAMINA-HERMANAS.png` (antes y después) junto al informe.

## 3. No tocar todavía

Likes, reposts, visualizaciones y respuestas simuladas acordes a los seguidores: Alberto lo quiere, pero no en esta tanda. Solo para que lo sepas: ahora los posts nuevos nacen con `likes_sim`, `reposts_sim`, `vistas_sim` y `respuestas_sim` a 0, también en cuentas de millones de seguidores. Irá en un encargo aparte.
