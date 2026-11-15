import { useState } from 'react'
import { Link } from 'react-router'
import {
  Thermometer,
  MapPinArea,
  Question,
  Polygon,
  CalendarCheck,
  Plant,
  MagnifyingGlass,
  SealCheck,
  WifiSlash,
} from '@phosphor-icons/react'
import { useDict } from '../../i18n/useDict'

const contenedor = 'mx-auto w-full max-w-6xl px-5 md:px-8'

/* ───────────── El reto (con el granjero) ───────────── */
export function Challenge() {
  const d = useDict()
  const iconos = [Thermometer, MapPinArea, Question]
  return (
    <section className={`${contenedor} grid items-center gap-10 py-16 md:grid-cols-[0.8fr_1.2fr] md:py-24`}>
      <div className="relative mx-auto w-56 md:w-72">
        <div aria-hidden className="absolute inset-x-0 bottom-0 h-3/4 rounded-[45%_55%_40%_60%] bg-niebla" />
        <img src="/brand/granjero-720.webp" alt="" className="relative mx-auto h-auto w-4/5" loading="lazy" />
      </div>
      <div>
        <h2 className="text-3xl md:text-[2.75rem]">{d.challenge.title}</h2>
        <p className="mt-4 max-w-2xl text-lg text-gris">{d.challenge.lead}</p>
        <ul className="mt-8 space-y-6">
          {d.challenge.items.map((it, i) => {
            const Icon = iconos[i]
            return (
              <li key={it.title} className="flex gap-4">
                <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-papa-suave text-papa-osc">
                  <Icon size={26} weight="duotone" aria-hidden />
                </span>
                <div>
                  <h3 className="font-sans text-lg font-bold text-bosque">{it.title}</h3>
                  <p className="text-gris">{it.text}</p>
                </div>
              </li>
            )
          })}
        </ul>
      </div>
    </section>
  )
}

/* ───────────── La plataforma ───────────── */
export function Platform() {
  const d = useDict()
  const iconos = [Polygon, CalendarCheck, Plant, MagnifyingGlass, SealCheck, WifiSlash]
  return (
    <section className="relative bg-papel py-16 md:py-24">
      <div className={contenedor}>
        <h2 className="max-w-2xl text-3xl md:text-[2.75rem]">{d.platform.title}</h2>
        <ul className="mt-12 grid gap-x-12 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
          {d.platform.items.map((it, i) => {
            const Icon = iconos[i]
            return (
              <li key={it.title}>
                <Icon size={34} weight="duotone" className="text-pradera-osc" aria-hidden />
                <h3 className="mt-3 font-sans text-xl font-bold text-bosque">{it.title}</h3>
                <p className="mt-1.5 text-gris">{it.text}</p>
              </li>
            )
          })}
        </ul>
      </div>
    </section>
  )
}

/* ───────────── Lupa de escala (el elemento memorable) ───────────── */
type ClaveEscala = 's2' | 'plot' | 'modis' | 'smap' | 'imerg' | 'power'
// Lado aproximado de cada huella en metros. POWER: √(55 km × 69 km) ≈ 61,6 km.
const METROS: Record<ClaveEscala, number> = { s2: 10, plot: 180, modis: 250, smap: 9000, imerg: 10000, power: 61600 }
const ORDEN: ClaveEscala[] = ['s2', 'plot', 'modis', 'smap', 'imerg', 'power']
const lado = (m: number) => 26 + ((Math.log10(m) - 1) / (Math.log10(61600) - 1)) * 318

export function ScaleLens() {
  const d = useDict()
  const [sel, setSel] = useState<ClaveEscala>('power')
  const info = d.scale.items[sel]
  return (
    <section className="relative overflow-hidden bg-bosque py-16 text-crema md:py-24">
      <div className={`${contenedor} grid items-center gap-12 lg:grid-cols-[1fr_1fr]`}>
        <div>
          <h2 className="text-3xl text-crema md:text-[2.75rem]">{d.scale.title}</h2>
          <p className="mt-4 text-lg text-crema/85">{d.scale.lead}</p>
          <p className="mt-8 text-sm font-bold text-papa">{d.scale.hint}</p>
          <div className="mt-3 flex flex-wrap gap-2" role="radiogroup" aria-label={d.scale.hint}>
            {ORDEN.map((k) => (
              <button
                key={k}
                type="button"
                role="radio"
                aria-checked={sel === k}
                onClick={() => setSel(k)}
                className={`rounded-chip px-3.5 py-2 text-sm font-bold transition ${
                  sel === k ? 'bg-papa text-bosque' : 'bg-white/10 text-crema hover:bg-white/20'
                }`}
              >
                {d.scale.items[k].label}
              </button>
            ))}
          </div>
          <div className="mt-6 min-h-24 rounded-tarjeta bg-white/8 p-5" aria-live="polite">
            <p className="font-bold">
              {info.label} · <span className="cifra text-papa">{info.size}</span>
            </p>
            <p className="mt-1 text-crema/85">{info.text}</p>
          </div>
        </div>

        <figure className="mx-auto w-full max-w-md">
          <svg viewBox="0 0 360 360" className="h-auto w-full" role="img" aria-label={d.scale.title}>
            {[...ORDEN].reverse().map((k) => {
              const s = lado(METROS[k])
              const o = (360 - s) / 2
              const activo = sel === k
              const esParcela = k === 'plot'
              return (
                <rect
                  key={k}
                  x={o}
                  y={o}
                  width={s}
                  height={s}
                  rx={k === 'power' ? 28 : 10}
                  onClick={() => setSel(k)}
                  className="cursor-pointer transition-all duration-300"
                  fill={esParcela ? '#7AB22A' : activo ? 'rgb(228 156 84 / 0.22)' : 'transparent'}
                  stroke={activo ? '#E49C54' : esParcela ? '#7AB22A' : 'rgb(207 232 242 / 0.4)'}
                  strokeWidth={activo ? 3.5 : 1.5}
                  strokeDasharray={activo || esParcela ? undefined : '6 6'}
                />
              )
            })}
          </svg>
          <figcaption className="mt-3 text-center text-sm text-crema/70">{d.scale.note}</figcaption>
        </figure>
      </div>
    </section>
  )
}

/* ───────────── Datos NASA ───────────── */
export function DataSources() {
  const d = useDict()
  return (
    <section id="datos" className={`${contenedor} scroll-mt-24 py-16 md:py-24`}>
      <h2 className="max-w-2xl text-3xl md:text-[2.75rem]">{d.data.title}</h2>
      <p className="mt-4 max-w-2xl text-lg text-gris">{d.data.lead}</p>

      <div className="mt-10 overflow-hidden rounded-tarjeta bg-papel shadow-suave">
        <div className="hidden grid-cols-[1fr_1.6fr_1fr_1.6fr] gap-6 bg-niebla px-6 py-3 text-sm font-bold text-bosque md:grid">
          <span>{d.data.head.source}</span>
          <span>{d.data.head.what}</span>
          <span>{d.data.head.res}</span>
          <span>{d.data.head.cannot}</span>
        </div>
        <ul className="divide-y divide-borde">
          {d.data.rows.map((r) => (
            <li key={r.source} className="grid gap-1.5 px-6 py-5 md:grid-cols-[1fr_1.6fr_1fr_1.6fr] md:gap-6">
              <div>
                <p className="font-bold text-bosque">{r.source}</p>
                {'partner' in r && r.partner && <p className="text-xs text-gris">{d.data.partner}</p>}
              </div>
              <p>{r.what}</p>
              <p className="cifra font-bold text-cielo-osc">{r.res}</p>
              <p className="text-gris">
                <span className="font-bold text-arcilla md:hidden">{d.data.head.cannot}: </span>
                {r.cannot}
              </p>
            </li>
          ))}
        </ul>
      </div>
      <p className="mt-4 text-sm text-gris">{d.data.foot}</p>
    </section>
  )
}

/* ───────────── Cómo funciona + lectura real ───────────── */
export function HowItWorks() {
  const d = useDict()
  const ex = d.how.example
  return (
    <section id="como" className="scroll-mt-24 bg-niebla py-16 md:py-24">
      <div className={`${contenedor} grid gap-12 lg:grid-cols-[1.1fr_0.9fr]`}>
        <div>
          <h2 className="text-3xl md:text-[2.75rem]">{d.how.title}</h2>
          <ol className="mt-10 space-y-7">
            {d.how.steps.map((s, i) => (
              <li key={s.title} className="flex gap-5">
                <span className="cifra grid size-11 shrink-0 place-items-center rounded-full bg-bosque font-display text-lg text-crema">
                  {i + 1}
                </span>
                <div>
                  <h3 className="font-sans text-lg font-bold text-bosque">{s.title}</h3>
                  <p className="text-gris">{s.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <aside className="self-center rounded-hoja bg-papel p-7 shadow-suave md:p-8">
          <h3 className="text-2xl">{ex.title}</h3>
          <dl className="mt-6 divide-y divide-borde">
            {ex.rows.map(([k, v]) => (
              <div key={k} className="flex items-baseline justify-between gap-4 py-3">
                <dt className="text-gris">{k}</dt>
                <dd className="cifra text-right text-lg font-bold whitespace-nowrap text-bosque">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-5 rounded-chip bg-casco/60 p-4 text-sm text-tinta">{ex.note}</p>
          <p className="mt-4 text-xs text-gris">{ex.source}</p>
        </aside>
      </div>
    </section>
  )
}

/* ───────────── Potatonaut ───────────── */
export function MeetPotatonaut() {
  const d = useDict()
  return (
    <section className={`${contenedor} grid items-center gap-12 py-16 md:grid-cols-[0.8fr_1.2fr] md:py-24`}>
      <div className="relative mx-auto w-60 md:w-80">
        <div aria-hidden className="absolute inset-4 rounded-full bg-casco" />
        <img
          src="/brand/potatonaut-512.webp"
          alt="Potatonaut"
          className="relative mx-auto h-auto w-4/5 drop-shadow-2xl"
          loading="lazy"
        />
      </div>
      <div>
        <h2 className="text-3xl md:text-[2.75rem]">{d.potatonaut.title}</h2>
        <p className="mt-4 max-w-2xl text-lg text-gris">{d.potatonaut.lead}</p>
        <div className="mt-8 space-y-5">
          {d.potatonaut.chat.map((c) => (
            <div key={c.q} className="space-y-2">
              <p className="ml-auto w-fit max-w-[85%] rounded-3xl rounded-br-md bg-bosque px-4 py-2.5 font-semibold text-crema">
                {c.q}
              </p>
              <div className="flex max-w-[92%] items-end gap-2">
                <img src="/brand/potatonaut-128.webp" alt="" className="size-8 shrink-0" />
                <p className="rounded-3xl rounded-bl-md bg-papel px-4 py-2.5 shadow-suave">{c.a}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ───────────── Equipo + llamado final ───────────── */
export function TeamAndCta() {
  const d = useDict()
  return (
    <section id="equipo" className={`${contenedor} scroll-mt-24 pb-20`}>
      <div className="max-w-2xl">
        <h2 className="text-3xl md:text-[2.75rem]">{d.team.title}</h2>
        <p className="mt-4 text-lg text-gris">{d.team.lead}</p>
      </div>

      <div className="relative mt-14 overflow-hidden rounded-hoja bg-cielo px-7 py-10 md:px-12 md:py-14">
        <div aria-hidden className="absolute -right-16 -bottom-24 hidden size-72 rounded-full bg-pradera/80 sm:block" />
        <div aria-hidden className="absolute right-24 -bottom-32 hidden size-72 rounded-full bg-pradera sm:block" />
        <img
          src="/brand/potatonaut-256.webp"
          alt=""
          className="absolute right-6 bottom-6 hidden w-36 drop-shadow-xl sm:block md:right-16 md:w-44"
          loading="lazy"
        />
        <div className="relative max-w-lg">
          <h2 className="text-3xl text-white md:text-5xl">{d.cta.title}</h2>
          <p className="mt-3 text-lg font-semibold text-white">{d.cta.lead}</p>
          <Link
            to="/finca"
            className="mt-7 inline-block rounded-full bg-bosque px-7 py-3.5 font-bold text-crema shadow-flota transition hover:bg-bosque-700"
          >
            {d.cta.button}
          </Link>
        </div>
      </div>
    </section>
  )
}
