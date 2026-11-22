alter table public.posts add column oculto text, add column media_n int;
alter table public.mensajes add column imagen_url text, add column precio numeric(6,2), add column oculto text;

create table public.desbloqueos (
  id bigint generated always as identity primary key,
  post_id bigint references public.posts(id) on delete cascade,
  mensaje_id bigint references public.mensajes(id) on delete cascade,
  precio numeric(6,2) not null default 0,
  creado timestamptz not null default now(),
  check ((post_id is null) <> (mensaje_id is null))
);
create unique index on public.desbloqueos(post_id) where post_id is not null;
create unique index on public.desbloqueos(mensaje_id) where mensaje_id is not null;

create table public.suscripciones (
  id bigint generated always as identity primary key,
  creadora uuid not null references public.cuentas(id) on delete cascade,
  precio numeric(6,2) not null,
  desde timestamptz not null default now(),
  hasta timestamptz not null,
  creado timestamptz not null default now()
);

create table public.propinas (
  id bigint generated always as identity primary key,
  para uuid not null references public.cuentas(id) on delete cascade,
  post_id bigint references public.posts(id) on delete set null,
  importe numeric(6,2) not null check (importe > 0),
  mensaje text,
  creado timestamptz not null default now()
);

create table public.push_subs (
  endpoint text primary key,
  p256dh text not null,
  auth text not null,
  creado timestamptz not null default now()
);
create table public.secretos (clave text primary key, valor text not null);

do $$
declare t text;
begin
  foreach t in array array['desbloqueos','suscripciones','propinas','push_subs','secretos'] loop
    execute format('alter table public.%I enable row level security', t);
  end loop;
  foreach t in array array['desbloqueos','suscripciones','propinas','push_subs'] loop
    execute format('create policy alberto_todo on public.%I for all to authenticated using (public.es_alberto()) with check (public.es_alberto())', t);
  end loop;
end $$;

create policy ya_paso on public.posts as restrictive for select to authenticated using (creado <= now());
create policy ya_paso on public.comentarios as restrictive for select to authenticated using (creado <= now());
create policy ya_paso on public.mensajes as restrictive for select to authenticated using (creado <= now());
create index on public.comentarios (creado);
create index on public.mensajes (creado);

create or replace view public.v_posts2 with (security_invoker = true) as
select p.*,
  p.likes_sim + (select count(*) from public.likes l where l.post_id = p.id) as n_likes,
  p.reposts_sim + (select count(*) from public.posts r where r.repost_de = p.id and r.creado <= now()) as n_reposts,
  (select count(*) from public.comentarios c where c.post_id = p.id and c.creado <= now()) as n_comentarios
from public.posts p;

insert into public.config values
  ('agenda', '[{"dia":1,"quien":"VeeNoir","usuario":"veenoir","que":"Directo · LoL","hora":"21:00","dur":180,"c":"#ff3d8b"},
               {"dia":3,"quien":"VeeNoir","usuario":"veenoir","que":"Directo · LoL","hora":"21:00","dur":180,"c":"#ff3d8b"},
               {"dia":5,"quien":"Yoruha","usuario":"yoruha_","que":"Directo de canto","hora":"22:00","dur":90,"c":"#a78bfa"},
               {"dia":6,"quien":"VeeNoir","usuario":"veenoir","que":"Directo · GTA 6","hora":"21:00","dur":180,"c":"#ff3d8b"}]'),
  ('nocturna', '{"precio_mes":9.99,"bienvenida":"bienvenido a mi rincón 🖤 aquí subo lo que no cabe en vox. no seas raro."}'),
  ('ultimo_aviso', to_jsonb(now()::text)),
  ('avisos', '{"silencio_desde":0,"silencio_hasta":9}')
on conflict (clave) do nothing;
