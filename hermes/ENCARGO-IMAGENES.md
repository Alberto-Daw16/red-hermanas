# Red social · imágenes y más vida · 22/11/2026

Encargo para **Shiro**, de una sola vez, sin tablero ni taller. Resultado en `~/tmp/red-social/RESULTADO-IMAGENES.md`.

Ya está hecho (no lo toques): la base de datos tiene una cola de imágenes (`imagenes`) con avatar y banner para todas las cuentas, los famosos de parodia y las creadoras de Nocturna, y además los **7 iconos del móvil** (Aquelarre y sus apps). La red se llama Raven. La tanda ya pide fotos y escribe como Twitter de verdad.

## Reglas
- No toques hub, gateway, la academia ni los SOUL. No reinicies nada.
- Ninguna clave en chats, tarjetas ni en el repo.
- Dos errores seguidos y paras: apúntalo y me lo dices.

## 1. Actualizar
```bash
git -C ~/red-hermanas pull
```

## 2. Enganchar gpt-image-2
`imagenes.py` genera cada imagen llamando a un comando que tú defines en `~/.hermes/red-social.env`:
```
IMAGEN_CMD=python3 /ruta/a/tu/puente.py
```
Ese comando recibe por stdin `{"prompt", "tamano", "referencia", "salida"}` y tiene que dejar un PNG en `salida` (código 0 si va bien). `referencia` es la ruta a una hoja de canonical (solo para las fotos de Valeria) o `null`.

Hazlo igual que genera gpt-image-2 la skill `escenas-hermanas` (la misma cuenta y la misma vía, que no gasta cuota de la API). Si la referencia viene, pásala como imagen de referencia. Escribe el puente en `~/.hermes/red-social/puente-imagen.py` si no hay uno que valga ya.

Prueba:
```bash
python3 ~/.hermes/red-social/imagenes.py --prueba     # lista lo que haría, sin generar
python3 ~/.hermes/red-social/imagenes.py              # una ronda de 8
```
Comprueba que las imágenes salen y que la ronda acaba sin errores. Las de VeeNoir usan `valeria_reference_sheet.jpg` de canonical: si aún no está aprobada, se saltan solas.

## 3. Tareas programadas (script, sin modelo propio)
Además de las dos tandas (13:40 y 21:40, si no están creadas, créalas), dos rondas de imágenes un rato después:

| Tarea | Hora | Comando |
| --- | --- | --- |
| Red · imágenes mediodía | 14:00 | `python3 ~/.hermes/red-social/imagenes.py` |
| Red · imágenes noche | 22:00 | `python3 ~/.hermes/red-social/imagenes.py` |

Hoy, después de probar, lanza rondas a mano hasta vaciar la cola (unas 40: primero salen los iconos, luego avatares y banners).

## 3b. Iconos del móvil
Son los 7 primeros de la cola (`tipo = icono`). `imagenes.py` los sube solo a `publico/iconos/<app>.png` y el móvil los coge al abrirlo; mientras no estén, se ve el dibujado de antes.

Míralos uno a uno. Que se vean bien en pequeño, un solo símbolo, sin texto ni letras, sin esquinas redondeadas ni marco (el móvil ya los recorta), y que no se parezcan a iconos de apps de verdad. Si uno no vale:
```bash
python3 ~/.hermes/red-social/imagenes.py --rehacer <ID>   # vuelve a la cola
python3 ~/.hermes/red-social/imagenes.py
```
Como mucho dos intentos por icono; si sigue sin valer, lo dejas y me lo dices.

## 4. Resultado
En `~/tmp/red-social/RESULTADO-IMAGENES.md`:
- cómo quedó el puente (qué llama y con qué cuenta);
- cuántas imágenes generó, cuántas fallaron y por qué, y cuánto tarda cada una;
- los iconos: cuáles quedaron bien a la primera, cuáles rehiciste y si alguno se quedó sin valer;
- los ID de las tareas (las de la tanda y las de imágenes);
- si el pull trajo la tanda nueva (tiene que tener la regla de tacos y los posts de gente random).
