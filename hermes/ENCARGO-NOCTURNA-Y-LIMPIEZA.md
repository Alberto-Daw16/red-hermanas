# Limpieza del Mac mini y prueba de Nocturna con GPT · 23/11/2026

Encargo para **Shiro**, de una sola vez, sin tablero ni taller. Resultado en `~/tmp/red-social/prueba-nocturna/RESULTADO-NOCTURNA.md`.

## Reglas
- No toques hub, gateway, la academia ni los SOUL. No reinicies nada.
- No cambies `IMAGEN_CMD`, la cola de Raven ni los crons.
- Las hermanas, solo con su hoja aprobada de canonical, sin modificarla.
- Personajes claramente adultos. Sexy sí, **nada de desnudos ni actos sexuales**.
- Dos errores seguidos o algo que no puedas resolver: paras, lo apuntas y me lo dices.

## 1. Limpieza (autorizada por Alberto)
1. **ComfyUI fuera.** La prueba en local no compensa en el Mac mini y todo se genera con GPT. Comprueba que no está corriendo y borra `~/ComfyUI` entero, con sus modelos y su entorno. Si los modelos de la prueba se descargaron también en alguna caché, bórralos de ahí.
2. **Cachés regenerables:** limpia la caché de **uv** con su propia herramienta (`uv cache clean`) y la de **npm** con `npm cache clean --force`, sin ninguna instalación en curso. No toques los entornos instalados, `~/.local` ni el resto de `~/.cache`.
3. Apunta los GB libres antes y después.

No toques nada más de la lista de espacio, ni `~/backups` ni `~/.hermes`: lo de las copias se decide aparte.

## 2. Prueba de Nocturna con GPT
Queremos saber si GPT genera el contenido de **Nocturna** (la página de pago, tipo OnlyFans): fotos sexys, de lencería y boudoir, picantes pero **sin desnudos**. Interesa sobre todo **qué acepta y qué rechaza**.

Estilo **anime**, con el puente de GPT de siempre (`gpt-image-2`).
- **Valeria** con su hoja de canonical.
- Las creadoras con su hoja anime de `~/tmp/red-social/prueba-estilos/hojas/anime/` si la tienen (Mila). Si no la tienen, hazles antes una hoja anime con la misma receta de la prueba de estilos, a partir de su `personalidad` y `bio` en `cuentas`: **Dalia** (@dalianox), **Afrodita Vex** (@afroditavex) y **Bea** (@bealluch).

### Fotos (6 de Valeria y 3 de cada creadora)
Valeria:
1. lencería negra de encaje, de pie frente al espejo del dormitorio, foto con el móvil;
2. tumbada boca abajo en la cama, con camiseta grande y medias, mirando a cámara;
3. en la bañera con espuma hasta los hombros, luz de velas;
4. con ropa interior y una sudadera abierta, sentada en su silla gaming, luces rosas;
5. bikini mínimo en una piscina de noche;
6. de espaldas en ropa interior, mirando por encima del hombro, luz cálida.

- **Mila:** body deportivo ajustado en el gym vacío; lencería deportiva frente al espejo; toalla al salir de la ducha.
- **Dalia:** corsé negro con luz roja; lencería de cuero con cadenas de adorno; tumbada en sábanas negras.
- **Afrodita:** bikini en la villa al atardecer; bata de seda medio abierta, sin enseñar nada explícito; jacuzzi con copa de cava.
- **Bea:** pijama corto de satén en el sofá; ropa interior y medias en el dormitorio; selfie en la cama tapada con la sábana.

Si GPT rechaza una foto, **no la reformules para colarla**: apunta el prompt y el mensaje de rechazo tal cual y sigue con la siguiente.

Guarda todo en `~/tmp/red-social/prueba-nocturna/fotos/` y haz **una hoja de contacto por personaje** y otra con todas juntas, con las rechazadas marcadas «RECHAZADA».

## 3. Resultado
En `~/tmp/red-social/prueba-nocturna/RESULTADO-NOCTURNA.md`:
- GB libres antes y después de la limpieza, y qué borraste;
- las rutas de las hojas de contacto, lo primero de todo;
- cuántas fotos salieron y cuántas rechazó GPT, con el prompt y el motivo de cada rechazo;
- en una línea por personaje: si la cara se mantiene y si el resultado tiene el punto picante que se buscaba o sale demasiado soso;
- tiempo medio por imagen.
