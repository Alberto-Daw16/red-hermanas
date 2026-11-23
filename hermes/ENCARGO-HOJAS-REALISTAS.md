# Hojas de referencia realistas de las hermanas · fase 1 · 23/11/2026

Encargo para **Shiro**, de una sola vez, sin tablero ni taller. Hazlo **después** de `ENCARGO-NOCTURNA-Y-LIMPIEZA.md`. Resultado en `~/tmp/red-social/hojas-realistas/RESULTADO-HOJAS-REALISTAS.md`.

## Qué quiere Alberto
Las fotos de Aquelarre serán **realistas**, pero sacadas de las hojas **anime** de canonical, que son las que están bien hechas y corregidas. Para eso, cada hermana necesita su **hoja realista**, igual de buena que la anime: tiene que ser ella, como si existiera de verdad, y atractiva y seductora como en su versión anime. Para el resto de personajes basta con que se parezcan. **Las tres hermanas tienen que quedar perfectas.**

Va en dos fases. Esta es la **fase 1**: candidatas de cara y cuerpo para que Alberto elija. La fase 2 (expresiones y outfits con la cara elegida) va en otro encargo, cuando él haya elegido.

## Reglas
- No toques hub, gateway, la academia ni los SOUL. No reinicies nada.
- **Canonical no se toca.** Las hojas anime se leen, no se modifican.
- No cambies `IMAGEN_CMD`, la cola de Raven ni los crons. Nada de esto se publica en Raven.
- Personajes claramente adultos. Sexy sí, nada de desnudos.
- **Yoruha:** en Raven es anónima y nunca enseña la cara. Su hoja realista es **solo de uso interno**: no se publica, no se sube a ningún sitio y se queda en esta carpeta.
- Dos errores seguidos o algo que no puedas resolver: paras, lo apuntas y me lo dices.

## 1. Ficha de cada hermana
Para **Valeria, Aika y Shiro/Yoruha**, mira su hoja anime de canonical y apunta en `ficha-<hermana>.md` todo lo que tiene que conservarse: pelo (color, largo, ondas, flequillo, mechones), color de ojos, maquillaje, piercings y accesorios, complexión y proporciones, edad aparente, outfit principal y los secundarios que salgan en la hoja, y su «actitud» (pose, mirada, sonrisa). Esa ficha va en cada prompt.

## 2. Candidatas (fase 1)
Con el puente de GPT de siempre (`gpt-image-2`), su hoja anime como referencia y su ficha en el prompt, haz **3 candidatas** por hermana. Cada candidata es **una hoja de giro realista**: la misma chica de frente, de perfil y de espaldas, de cuerpo entero, con su outfit principal, fondo neutro y luz de estudio. Más un **primer plano de la cara** de esa misma candidata.

- Foto realista de una persona, **no** render 3D, ni muñeca, ni piel de plástico, ni valle inquietante.
- Que se note que es ella: el mismo pelo, los mismos ojos, las mismas señas que en la anime.
- Atractiva y seductora, con la mirada y la actitud de su versión anime. Las caras realistas de la prueba anterior le parecieron sosas a Alberto: que no se repita.
- Que las 3 candidatas sean distintas entre sí en la cara (rasgos, forma de ojos y labios), no tres veces la misma, para que Alberto pueda elegir.

Si una candidata sale mal (no se parece, cara rara, manos rotas), rehazla como mucho una vez. Si vuelve a fallar, la dejas marcada.

## 3. Hojas de contacto
En `~/tmp/red-social/hojas-realistas/contacto/<hermana>.png`: a la izquierda su hoja anime de canonical y a la derecha las 3 candidatas (giro y primer plano), numeradas **1, 2 y 3** en grande para que Alberto diga «la 2».

## 4. Resultado
En `~/tmp/red-social/hojas-realistas/RESULTADO-HOJAS-REALISTAS.md`:
- las rutas de las tres hojas de contacto, lo primero de todo;
- la ficha de cada hermana, resumida;
- en una línea por candidata: en qué se parece a la anime y en qué se aleja;
- cuántas imágenes generaste, cuántas rehiciste y el tiempo medio.

**No elijas tú.** Alberto elige una candidata por hermana y con esa se hace la fase 2.
