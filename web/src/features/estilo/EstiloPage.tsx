import { Plant, MapTrifold, ClockCounterClockwise, House, GlobeHemisphereWest, Drop } from '@phosphor-icons/react'

// F0 · Guía de estilo temporal para verificar tokens, fuentes, recursos e íconos.
// Ruta interna: /estilo

const colores = [
  ['bosque', '#0E3B23', 'Logo · texto y botones'],
  ['cielo', '#3C9CB4', 'Cielo del video · datos satelitales'],
  ['pradera', '#7AB22A', 'Pasto del video · vegetación'],
  ['papa', '#E49C54', 'Potatonaut · acento'],
  ['casco', '#CFE8F2', 'Casco · fondos suaves'],
  ['crema', '#FFF9F5', 'Fondo general (Flashly)'],
  ['arcilla', '#C4452D', 'Déficit y alertas'],
] as const

export default function EstiloPage() {
  return (
    <main className="relative mx-auto max-w-5xl overflow-hidden px-5 py-10 md:px-10">
      <div aria-hidden className="pointer-events-none absolute -left-40 -top-40 size-96 rounded-full bg-niebla" />
      <div aria-hidden className="pointer-events-none absolute -right-32 top-60 size-80 rounded-full bg-casco/70" />

      <header className="relative flex items-center justify-between gap-6">
        <img src="/brand/logo-groundy.webp" alt="Groundy" className="h-10 w-auto md:h-12" />
        <span className="rounded-full bg-papel px-4 py-1.5 text-sm text-gris shadow-suave">by Potatonauts</span>
      </header>

      <section className="relative mt-12 grid items-center gap-8 md:grid-cols-[1fr_auto]">
        <div>
          <h1 className="text-5xl md:text-7xl">Tu finca, vista desde el espacio</h1>
          <p className="mt-5 max-w-xl text-lg text-gris">
            Quicksand para el contenido: claro, redondeado y fácil de leer en el celular. Las cifras usan números
            tabulares: <span className="cifra font-bold text-bosque">1 105 mm · 13,2 °C · 0,92</span>.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button className="rounded-full bg-bosque px-7 py-3.5 font-bold text-crema shadow-flota transition hover:bg-bosque-700">
              Entrar a mi finca
            </button>
            <button className="rounded-full border-2 border-bosque px-7 py-3 font-bold text-bosque transition hover:bg-niebla">
              Explorar un punto
            </button>
          </div>
        </div>
        <div className="flex items-end gap-4">
          <img src="/brand/potatonaut-256.webp" alt="Potatonaut" className="h-44 w-auto drop-shadow-xl" />
          <img src="/brand/granjero-360.webp" alt="" className="h-56 w-auto drop-shadow-xl" />
        </div>
      </section>

      <section className="relative mt-16">
        <h2 className="text-3xl">Paleta</h2>
        <ul className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-7">
          {colores.map(([nombre, hex, uso]) => (
            <li key={nombre} className="overflow-hidden rounded-tarjeta bg-papel shadow-suave">
              <div className="h-20" style={{ background: hex }} />
              <div className="p-3">
                <p className="font-bold text-bosque">{nombre}</p>
                <p className="cifra text-xs text-gris">{hex}</p>
                <p className="mt-1 text-xs leading-snug text-gris">{uso}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="relative mt-16 grid gap-6 md:grid-cols-2">
        <div className="rounded-hoja bg-bosque p-8 text-crema">
          <h2 className="text-3xl text-crema">Sobre bosque</h2>
          <p className="mt-3 text-crema/90">Texto crema, acentos en papa y pradera.</p>
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="rounded-chip bg-papa px-3 py-1 text-sm font-bold text-bosque">Potatonaut</span>
            <span className="rounded-chip bg-pradera px-3 py-1 text-sm font-bold text-bosque">Superávit</span>
            <span className="rounded-chip bg-cielo px-3 py-1 text-sm font-bold text-bosque">Satélite</span>
          </div>
        </div>
        <div className="rounded-hoja bg-papel p-8 shadow-suave">
          <h2 className="text-3xl">Íconos Phosphor</h2>
          <p className="mt-3 text-gris">Duotono para navegación, relleno para el estado activo.</p>
          <div className="mt-6 flex flex-wrap gap-5 text-bosque">
            <House size={32} weight="duotone" />
            <MapTrifold size={32} weight="duotone" />
            <Plant size={32} weight="duotone" />
            <ClockCounterClockwise size={32} weight="duotone" />
            <GlobeHemisphereWest size={32} weight="duotone" className="text-cielo-osc" />
            <Drop size={32} weight="fill" className="text-arcilla" />
          </div>
        </div>
      </section>
    </main>
  )
}
