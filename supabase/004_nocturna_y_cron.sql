-- Cuentas de Nocturna
insert into public.cuentas (tipo, quien, plataforma, nombre, usuario, bio, seguidores, verificada, personalidad) values
('hermana','valeria','of','VeeNoir 🖤🎀','veenoir','lo que no subo a vox. sin caras raras en md, gracias',0,true,
 'Valeria en su página de pago. Picardía y bait, erotismo sin ser explícita. Cariñosa con quien paga, borde con los pesados.'),
('alberto','alberto','of','Alberto','alberto_16','',0,false,null);

-- Contenido de arranque de Nocturna (en días pasados, para no tocar el tope de hoy)
insert into public.posts (cuenta_id, plataforma, texto, de_pago, precio, media_n, oculto, likes_sim, origen, creado)
select c.id, 'of', v.texto, v.pago, v.precio, v.fotos, v.oculto, v.likes, 'semilla', now() - (v.h || ' hours')::interval
from public.cuentas c, (values
  ('primer post por aquí 🖤 lo de vox se queda en vox, lo de aquí se queda aquí', false, null::numeric, null::int, null::text, 410, 96),
  ('la sesión del cosplay de ahri que no cabía en vox 🦊', false, null, 8, 'las 8 de la peluca nueva. la tercera es la buena, no preguntes por qué.', 620, 72),
  ('set completo de ahri. el de verdad. 14 fotos 🙄', true, 7.99, 14, 'las que no se podían subir a vox. picardía, no te emociones.', 380, 50),
  ('lo que pasa cuando pierdo una apuesta con nerea 💀', true, 4.99, 5, 'me hizo ponerme el uniforme de maid. nunca más. (bueno.)', 290, 30)
) as v(texto, pago, precio, fotos, oculto, likes, h)
where c.plataforma = 'of' and c.quien = 'valeria';

-- Un mensaje de pago para Alberto
insert into public.mensajes (plataforma, de, para, texto, precio, oculto, origen, creado)
select 'of', v.id, a.id, 'ya que estás suscrito… esto no lo ve nadie más', 3.99, 'foto del espejo antes del directo, con la peluca a medio poner. ni una palabra.', 'semilla', now() - interval '3 hours'
from public.cuentas v, public.cuentas a
where v.plataforma = 'of' and v.quien = 'valeria' and a.plataforma = 'of' and a.tipo = 'alberto';

-- El gancho en Vox
insert into public.posts (cuenta_id, plataforma, texto, likes_sim, reposts_sim, vistas_sim, origen, creado)
select id, 'x', 'subido algo a nocturna 👀 los de vox os quedáis con las ganas', 1850, 40, 30000, 'semilla', now() - interval '26 hours'
from public.cuentas where plataforma = 'x' and quien = 'valeria';

-- Avisos cada 5 minutos
create extension if not exists pg_net;
create extension if not exists pg_cron;
select cron.schedule('avisos-red', '*/5 * * * *', $$
  select net.http_post(
    url := 'https://wtxiqvzercgharibvubw.supabase.co/functions/v1/avisos',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-clave', (select valor from public.secretos where clave = 'cron')),
    body := '{}'::jsonb)
$$);
