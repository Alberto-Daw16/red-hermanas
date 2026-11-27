-- Monedero de Nocturna (dinero de mentira): lo recargado. Saldo = recargas - (suscripciones + desbloqueos + propinas).
create table if not exists public.recargas (
  id bigint generated always as identity primary key,
  importe numeric not null check (importe > 0),
  creado timestamptz not null default now()
);
alter table public.recargas enable row level security;
drop policy if exists alberto_todo on public.recargas;
create policy alberto_todo on public.recargas for all using (es_alberto()) with check (es_alberto());
