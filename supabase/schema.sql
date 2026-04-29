-- BTC-Trustee-Quant-V3  ·  Supabase schema
-- Run in the Supabase SQL editor (or via supabase db push)

-- ── Extensions ────────────────────────────────────────────────────────────────
create extension if not exists "pgcrypto";

-- ── bets ──────────────────────────────────────────────────────────────────────
-- Win/loss ledger for every bet placed by the signal engine.
create table if not exists public.bets (
  id               uuid        primary key default gen_random_uuid(),
  user_id          uuid        references auth.users(id) on delete cascade,
  ticker           text        not null,                    -- e.g. KXBTC15M-25APR01-T94000
  bet_type         text        not null check (bet_type in ('YES','NO')),
  amount           numeric(12,2) not null default 50,       -- USD at risk
  outcome          text        not null default 'PENDING'
                               check (outcome in ('WIN','LOSS','PENDING')),
  payout           numeric(12,2),                           -- gross return (null until settled)
  floor_strike     numeric(12,2) not null,                  -- 60-sec BRTI avg at round open
  settlement_price numeric(12,2),                           -- actual 60-sec BRTI mean at close
  created_at       timestamptz not null default now()
);

-- Enable Row-Level Security
alter table public.bets enable row level security;

create policy "Users see own bets"
  on public.bets for select
  using (auth.uid() = user_id);

create policy "Service role can insert bets"
  on public.bets for insert
  with check (true);  -- lock down to service role in production

create index bets_user_created on public.bets(user_id, created_at desc);

-- ── diary ─────────────────────────────────────────────────────────────────────
-- Secret diary: every HOLD decision with the AI's shadow prediction.
create table if not exists public.diary (
  id                uuid        primary key default gen_random_uuid(),
  user_id           uuid        references auth.users(id) on delete cascade,
  ticker            text        not null,
  decision          text        not null default 'HOLD' check (decision = 'HOLD'),
  shadow_prediction text        not null check (shadow_prediction in ('YES','NO')),
  confidence        numeric(5,4) not null,                  -- 0.0000–1.0000
  reason_text       text        not null,                   -- e.g. "neutral_zone_50.2"
  created_at        timestamptz not null default now()
);

alter table public.diary enable row level security;

create policy "Users see own diary"
  on public.diary for select
  using (auth.uid() = user_id);

create policy "Service role can insert diary"
  on public.diary for insert
  with check (true);

create index diary_user_created on public.diary(user_id, created_at desc);

-- ── Realtime ──────────────────────────────────────────────────────────────────
-- Enable Supabase Realtime on both tables so the dashboard updates live.
alter publication supabase_realtime add table public.bets;
alter publication supabase_realtime add table public.diary;
