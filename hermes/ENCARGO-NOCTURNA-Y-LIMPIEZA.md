# Limpieza, prueba de Nocturna y modelo de texto local · 23/11/2026 (v2)

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

**En los dos estilos, anime y realista**, con el puente de GPT de siempre (`gpt-image-2`). Cada foto se hace dos veces, una por estilo, con la hoja de ese estilo.
- **Valeria:** en anime, su hoja de canonical; en realista, `~/tmp/red-social/prueba-estilos/hojas/realista/valeria.png`.
- **Las creadoras:** su hoja de `~/tmp/red-social/prueba-estilos/hojas/<estilo>/` si la tienen (Mila). Si no, hazles antes una hoja **en cada estilo**, con la misma receta de la prueba de estilos y a partir de su `personalidad` y `bio` en `cuentas`: **Dalia** (@dalianox), **Afrodita Vex** (@afroditavex) y **Bea** (@bealluch).
- En **realista**, que las caras sean atractivas y con la misma pinta seductora que su versión anime. En la prueba anterior a Alberto le parecieron sosas.

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

Guarda todo en `~/tmp/red-social/prueba-nocturna/fotos/<estilo>/`. Haz **una hoja de contacto por personaje**, con anime arriba y realista abajo, y otra con todas juntas por estilo. Las rechazadas van marcadas «RECHAZADA».

## 3. Modelo de texto local, sin censura (abliterated)
Alberto quiere que las tandas de Raven las escriba un **modelo local abliterated**, sin depender de Grok. `tanda.py` ya lo admite: con `LLM_LOCAL_URL` (una API compatible con OpenAI, como la de Ollama) usa ese modelo en vez de Grok. Esto es **solo la prueba**: no cambies la configuración de producción ni los crons.

1. **Instala Ollama** sin `sudo` (Homebrew o la app oficial) y arráncalo solo en 127.0.0.1. Ollama carga el modelo cuando se le pide y lo descarga de memoria al rato, así que no ocupa RAM entre tandas.
2. **Descarga dos modelos** (unos 8–9 GB cada uno):
   - `huihui_ai/qwen3-abliterated:14b-v2`;
   - `huihui_ai/gemma3-abliterated:12b`.
   En Qwen3, desactiva el modo «pensar» si mete texto antes del JSON. `tanda.py` ya quita los bloques `<think>`, pero apunta si hizo falta algo más.
3. **Compara con el mismo material**, tres pasadas sin guardar nada en la red. Antes, haz el pull y comprueba que la copia de `tanda.py` que usas tiene `proveedor_local`:
   ```bash
   python3 ~/.hermes/red-social/tanda.py --sin-guardar > grok.txt
   LLM_LOCAL_URL=http://127.0.0.1:11434/v1 LLM_LOCAL_MODELO=huihui_ai/qwen3-abliterated:14b-v2 python3 ~/.hermes/red-social/tanda.py --sin-guardar > qwen.txt
   LLM_LOCAL_URL=http://127.0.0.1:11434/v1 LLM_LOCAL_MODELO=huihui_ai/gemma3-abliterated:12b python3 ~/.hermes/red-social/tanda.py --sin-guardar > gemma.txt
   ```
   Guárdalo todo en `~/tmp/red-social/prueba-texto/`.
4. **Mide** de cada uno: segundos, RAM mientras genera, si el JSON salió válido a la primera y si el Mac mini siguió respondiendo con Hermes en marcha.
5. **Juzga**, en pocas líneas por modelo y con 3 ejemplos copiados tal cual de cada uno:
   - si suena a Twitter de España, con tacos y gracia, o a traducción;
   - si respeta los usuarios y la agenda y no se inventa hechos de las hermanas;
   - si cumple las reglas de la tanda (las de siempre: nada de actos sexuales explícitos, menores, odio ni amenazas).

Al acabar, deja Ollama instalado pero **sin modelo cargado**, y no borres los modelos: si alguno vale, se usa.

## 4. Resultado
En `~/tmp/red-social/prueba-nocturna/RESULTADO-NOCTURNA.md`:
- GB libres antes y después de la limpieza, y qué borraste;
- las rutas de las hojas de contacto, lo primero de todo;
- cuántas fotos salieron y cuántas rechazó GPT, con el prompt y el motivo de cada rechazo;
- en una línea por personaje: si la cara se mantiene y si el resultado tiene el punto picante que se buscaba o sale demasiado soso;
- tiempo medio por imagen;
- del modelo de texto: la tabla de tiempos y RAM, los ejemplos de cada uno, tu opinión en una línea por modelo y las rutas de `grok.txt`, `qwen.txt` y `gemma.txt`.
