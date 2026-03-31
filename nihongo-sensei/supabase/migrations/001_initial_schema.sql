-- Users table
create table users (
  id uuid primary key default gen_random_uuid(),
  display_name text not null default 'Learner',
  current_level int not null default 1,
  total_xp int not null default 0,
  current_streak int not null default 0,
  longest_streak int not null default 0,
  last_active_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Lesson progress tracking
create table lesson_progress (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  lesson_id text not null,
  status text not null default 'not_started'
    check (status in ('not_started', 'in_progress', 'completed')),
  score int check (score >= 0 and score <= 100),
  xp_earned int not null default 0,
  attempts int not null default 0,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, lesson_id)
);

-- Vocabulary bank with spaced repetition
create table vocabulary_bank (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  word text not null,
  reading text not null,
  meaning text not null,
  srs_level int not null default 1 check (srs_level >= 1 and srs_level <= 5),
  next_review_date date not null default current_date,
  correct_count int not null default 0,
  incorrect_count int not null default 0,
  last_reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, word)
);

-- Session logs
create table session_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  lesson_id text not null,
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  duration_seconds int,
  xp_earned int not null default 0,
  turn_count int not null default 0,
  avg_pronunciation_score float,
  transcript jsonb,
  created_at timestamptz not null default now()
);

-- Enable Row Level Security
alter table users enable row level security;
alter table lesson_progress enable row level security;
alter table vocabulary_bank enable row level security;
alter table session_logs enable row level security;

-- For prototype: allow all access (single user, no auth)
create policy "Allow all for prototype" on users for all using (true);
create policy "Allow all for prototype" on lesson_progress for all using (true);
create policy "Allow all for prototype" on vocabulary_bank for all using (true);
create policy "Allow all for prototype" on session_logs for all using (true);

-- Seed a dev user
insert into users (id, display_name) values
  ('00000000-0000-0000-0000-000000000001', 'Dev Learner');

-- updated_at trigger
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger users_updated_at before update on users
  for each row execute function update_updated_at();
create trigger lesson_progress_updated_at before update on lesson_progress
  for each row execute function update_updated_at();
create trigger vocabulary_bank_updated_at before update on vocabulary_bank
  for each row execute function update_updated_at();
