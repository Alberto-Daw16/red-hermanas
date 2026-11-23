# Prueba de estilos · anime vs realista · 23/11/2026

Encargo para **Shiro**, de una sola vez, sin tablero ni taller. Hazlo **después** de `ENCARGO-PRUEBA-LOCAL.md`. Resultado en `~/tmp/red-social/prueba-estilos/RESULTADO-PRUEBA-ESTILOS.md`.

Objetivo: decidir con qué estilo se ve todo Aquelarre, **anime/3D** como las hojas de las hermanas o **realista**. Y comprobar que un personaje sale con la misma cara en todas sus fotos si se usa su hoja como referencia. Alberto elige con las imágenes delante.

## Reglas
- No toques hub, gateway, la academia ni los SOUL. No reinicies nada.
- **No cambies nada de Raven:** ni `IMAGEN_CMD`, ni la cola, ni los crons, ni los avatares y banners publicados. Todo lo de esta prueba se queda en la carpeta de la prueba.
- Las hermanas, solo con su hoja aprobada de canonical, sin modificarla. Si una no tiene hoja aprobada, se salta. Yoruha, solo si su lore permite enseñar la cara; si no, se salta y lo apuntas.
- Personajes claramente adultos. Sexy vale, explícito no. Nada que se parezca a una persona real.
- Dos errores seguidos o algo que no puedas resolver: paras, lo apuntas y me lo dices.

## Herramienta
El puente de GPT de siempre (`gpt-image-2`). Si la prueba local dejó Draw Things funcionando, haz además la versión anime con su modelo SDXL anime, para comparar.

## 1. Personajes de la prueba
- **Hermanas:** Valeria (y Aika si tiene hoja aprobada).
- **Fijos:** Nerea (@nereitaa_vlc), Pau (@pau_tilt), Kiara (@kiarapls), Mila (@milaortiz_fit) y Máximo Pixel (@maximopixel).
- Cómo es cada fijo: lee su `personalidad` y su `bio` en la tabla `cuentas`. Lo que no diga, invéntalo tú una vez (edad aproximada, pelo, estilo de ropa) y apúntalo, para que las dos versiones sean la misma persona.

## 2. Hojas de personaje, en los dos estilos
Para cada fijo, una **hoja** por estilo: la misma persona de frente, de perfil y de cuerpo entero, con fondo neutro. Es lo que luego se usa como referencia, igual que la hoja de Valeria.
- `hojas/anime/<usuario>.png`: estilo anime/3D, el mismo acabado que las hojas de las hermanas.
- `hojas/realista/<usuario>.png`: foto realista de una persona inventada.

Para las hermanas no hace falta hoja anime, ya la tienen. Haz solo la **versión realista** a partir de su hoja: la misma persona (pelo, ojos, rasgos, estilo) como si fuera una chica de verdad. Guárdala en `hojas/realista/<hermana>.png`.

## 3. Fotos de post con la hoja como referencia
Para cada personaje y cada estilo, **3 fotos** tipo post de Raven, siempre con su hoja como referencia:
- **Valeria:** selfie en su setup de streaming de noche; espejo del baño con sudadera; saliendo de fiesta con vestido negro.
- **Nerea:** en el sofá con mantita viendo un directo; terraza con amigas; selfie en el bus.
- **Pau:** con cascos jugando, cara de tilt; en un bar con una caña; en la calle de noche.
- **Kiara:** cosplay de bruja; selfie con ring light; con un café, cara de superioridad.
- **Mila:** espejo del gym; con un batido después de entrenar; en la playa.
- **Máximo Pixel:** en su coche; en la nieve, en Andorra; en su silla gaming con micro de podcast.
- **Aika**, si tiene hoja: 3 fotos de su día a día, acordes con su lore.

Guárdalas en `fotos/<estilo>/<usuario>-<n>.png`.

## 4. Hojas de contacto para Alberto
- **Una por personaje**, con dos filas: arriba anime (hoja y 3 fotos), abajo realista (hoja y 3 fotos). Así se ve de un vistazo si la cara se mantiene y qué estilo queda mejor.
- **Una «de feed»** por estilo: las fotos de todos mezcladas en una cuadrícula, como se verían seguidas en Raven. Es la que dice si el mundo entero es coherente.

Guárdalas en `contacto/`.

## 5. Resultado
En `~/tmp/red-social/prueba-estilos/RESULTADO-PRUEBA-ESTILOS.md`:
- las rutas de las hojas de contacto, lo primero de todo;
- cómo describiste a cada fijo (lo que inventaste);
- en una línea por personaje: si la cara se mantiene entre fotos, en cada estilo;
- cuántas imágenes generaste, cuántas fallaron y cuánto tardó cada una de media;
- si alguna hermana se saltó y por qué.

**No elijas tú el estilo.** Lo elige Alberto.
