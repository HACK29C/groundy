-- Papanauta / BD_Potatonauts: schema for the reference-site data.
-- Run once in Supabase -> SQL Editor. Safe to re-run (create if not exists).
-- Access model: the public (anon) key can only READ; writing needs the secret key (server side only).

create table if not exists public.sites (
  site            text primary key,
  grp             text not null,
  zone            text,
  lat             double precision not null,
  lon             double precision not null,
  elev_approx_m   real,
  elev_srtm_m     real
);

create table if not exists public.power_daily (
  site text not null references public.sites(site),
  date date not null,
  t2m_max real, t2m_min real, t2m real, prectotcorr real, rh2m real, ws2m real, allsky_sfc_sw_dwn real,
  primary key (site, date)
);

create table if not exists public.imerg_daily (
  site text not null references public.sites(site),
  date date not null,
  cell_lat double precision, cell_lon double precision,
  p_center real, p_mean5 real, p_sd5 real, p_max5 real, p_wet5 real, p_mean11 real, p_sd11 real,
  precipitation_cnt real, precipitation_cnt_cond real,
  mwprecipitation real, mwprecipitation_cnt real, mwprecipitation_cnt_cond real,
  randomerror real, randomerror_cnt real, probabilityliquidprecipitation real,
  primary key (site, date)
);

create table if not exists public.rain_monthly (
  site text not null references public.sites(site),
  month date not null,
  power_mm real, imerg_pixel_mm real, imerg_mean5_mm real, imerg_microwave_mm real,
  range_low_mm real, range_high_mm real,
  primary key (site, month)
);

create table if not exists public.rain_sites (
  site text primary key references public.sites(site),
  power_mm_yr real, imerg_pixel_mm_yr real, imerg_mean5_mm_yr real, imerg_microwave_mm_yr real,
  ratio_pixel_over_power real, monthly_rank_corr real, wet_day_freq_pct real, p_wet_wet real,
  longest_dry_spell_d real, days_ge_25mm real, days_ge_50mm real, rain_hours_per_rainy_day real,
  rainy_days_prob_liquidlt50 real, rainy_days real
);

-- Filled by notebook 04 (NDVI / SMAP / POWER monthly master table)
create table if not exists public.master_monthly (
  site text not null references public.sites(site),
  month date not null,
  rain_mm real, et0_mm real, tmean_c real, tmin_c real, rs_mj real, p_over_et0 real,
  ndvi real, evi real, sm_surf real, sm_root real, tsoil real, month_of_year int,
  ndvi_anom real, evi_anom real, sm_surf_anom real, sm_root_anom real, rain_mm_anom real, tmean_c_anom real,
  primary key (site, month)
);

-- Security: RLS on, public read-only policy, explicit grants (tables are not auto-exposed).
do $$
declare t text;
begin
  foreach t in array array['sites','power_daily','imerg_daily','rain_monthly','rain_sites','master_monthly'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists "public read" on public.%I', t);
    execute format('create policy "public read" on public.%I for select to anon, authenticated using (true)', t);
    execute format('revoke all on public.%I from anon, authenticated', t);
    execute format('grant select on public.%I to anon, authenticated', t);
    execute format('grant all on public.%I to service_role', t);
  end loop;
end $$;
