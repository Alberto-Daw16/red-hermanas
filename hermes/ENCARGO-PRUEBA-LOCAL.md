# Prueba de imágenes en local · Draw Things · 23/11/2026

Encargo para **Shiro**, de una sola vez, sin tablero ni taller. Resultado en `~/tmp/red-social/prueba-local/RESULTADO-PRUEBA-LOCAL.md`.

Objetivo: saber si podemos generar las fotos de Aquelarre en el Mac mini, con un modelo abierto, sin depender de la cuota de GPT. Y, sobre todo, si **Valeria sale reconocible y siempre igual**. Es solo una prueba: no se cambia nada de lo que ya funciona.

## Reglas
- No toques hub, gateway, la academia ni los SOUL. No reinicies nada.
- **No cambies `IMAGEN_CMD`**, ni la cola de imágenes, ni los crons. Raven sigue con GPT mientras dure la prueba.
- Ninguna clave en chats, tarjetas ni en el repo.
- Personajes siempre claramente adultos. Sexy vale, explícito no.
- Dos errores seguidos o algo que no puedas resolver: paras, lo apuntas y me lo dices.

## 1. Instalar Draw Things
- Es la app gratuita **Draw Things** del App Store. Si el App Store pide iniciar sesión o confirmar la descarga, no lo hagas tú: deja apuntado que Alberto tiene que instalarla y sigue con lo que puedas.
- En sus ajustes, activa el **API Server (HTTP)**, solo en local (127.0.0.1), puerto 7860. Comprueba que `curl http://127.0.0.1:7860` responde.
- Desde el catálogo de la propia app, descarga dos modelos:
  - un **SDXL de estilo anime** (de los que ofrece la app; elige el más usado para personajes anime);
  - **FLUX.1 [schnell]**.
- Apunta cuánto ocupa cada modelo en disco.

## 2. Puente de prueba (sin instalarlo)
Escribe `~/tmp/red-social/prueba-local/puente-drawthings.py` con el mismo contrato que el puente de GPT: recibe por stdin `{"prompt", "tamano", "referencia", "salida"}`, llama a Draw Things en `127.0.0.1:7860` y deja un PNG en `salida`. Si llega `referencia`, úsala como imagen de referencia por la mejor vía que tenga Draw Things para mantener al personaje. Si no tiene ninguna, dilo.

**No lo pongas en `IMAGEN_CMD`.** Se llama a mano solo para esta prueba.

## 3. Las pruebas
Con cada modelo (SDXL anime y Flux), y para comparar, también con el puente de GPT de siempre:

**A · Valeria con su hoja** (`valeria_reference_sheet.png` de canonical, sin modificarla), 6 fotos:
1. selfie en el espejo del baño, con sudadera oversize;
2. en su setup de streaming, de noche, luces rosas;
3. selfie en la cama, con poca luz;
4. vestido negro saliendo de fiesta, en la calle;
5. bikini en la playa, al atardecer;
6. de espaldas en el gimnasio, mirando por encima del hombro.

**B · Gente inventada de Raven**, 4 fotos: los prompts de las 4 últimas fotos de posts de la cola (los de k4rmasleeper, melodia_baja, softcover_23 y foxfiretilt), tal cual.

Guarda todo en `~/tmp/red-social/prueba-local/<modelo>/` con nombres que se entiendan (`valeria-1-espejo.png`…). Haz además **una hoja de contacto por prueba**, una imagen con las tres versiones lado a lado (SDXL, Flux, GPT) de cada foto, para que Alberto lo compare de un vistazo.

## 4. Medir
Para cada modelo:
- segundos por imagen (de media, con la más lenta y la más rápida);
- memoria usada mientras genera y si el Mac mini sigue respondiendo con Hermes en marcha;
- si alguna salió rota, con caras deformes, manos raras o un personaje que no se parece.

Si un modelo tarda más de 3 minutos por imagen, haz solo 2 fotos de Valeria con él y apúntalo.

## 5. No hacer todavía
- **No entrenes ningún LoRA.** Primero decidimos con esta prueba si vale la pena.
- No borres los modelos al acabar: si la prueba sale bien, se usan.

## 6. Resultado
En `~/tmp/red-social/prueba-local/RESULTADO-PRUEBA-LOCAL.md`:
- si Draw Things quedó instalado y con el servidor activo, o qué faltó (por ejemplo, la instalación desde el App Store);
- los modelos, cuánto ocupan y la memoria que usan;
- los tiempos por imagen;
- tu opinión, en una línea por modelo, sobre si Valeria se reconoce y se mantiene igual entre fotos;
- las rutas de las hojas de contacto.
