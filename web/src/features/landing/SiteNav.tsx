import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { List, X, Translate } from '@phosphor-icons/react'
import { useDict } from '../../i18n/useDict'
import { toggleLanguage } from '../../i18n'

/**
 * Barra pública. Sobre el hero es transparente con texto blanco;
 * al bajar se vuelve crema con texto bosque. En móvil se convierte en menú.
 */
export function SiteNav({ overHero = false }: { overHero?: boolean }) {
  const d = useDict()
  const [scrolled, setScrolled] = useState(!overHero)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!overHero) return
    const onScroll = () => setScrolled(window.scrollY > 40)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [overHero])

  const light = !scrolled && !open
  const links = [
    { href: '/explorar', label: d.nav.explore, route: true },
    { href: '/#como', label: d.nav.how },
    { href: '/#datos', label: d.nav.data },
    { href: '/#equipo', label: d.nav.team },
  ]

  return (
    <header
      className={`fixed inset-x-0 top-0 z-40 transition-colors duration-300 ${
        light ? 'bg-transparent text-white' : 'bg-crema/95 text-bosque shadow-suave backdrop-blur'
      }`}
    >
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5 md:h-20 md:px-8">
        <Link to="/" aria-label={d.nav.home} className="shrink-0">
          <img
            src="/brand/logo-groundy.webp"
            alt="Groundy"
            className={`h-7 w-auto md:h-8 ${light ? 'brightness-0 invert' : ''}`}
          />
        </Link>

        <ul className="hidden items-center gap-7 font-semibold md:flex">
          {links.map((l) => (
            <li key={l.href}>
              {l.route ? (
                <Link to={l.href} className="opacity-90 transition hover:opacity-100">
                  {l.label}
                </Link>
              ) : (
                <a href={l.href} className="opacity-90 transition hover:opacity-100">
                  {l.label}
                </a>
              )}
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggleLanguage}
            className={`flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-bold transition ${
              light ? 'hover:bg-white/15' : 'hover:bg-niebla'
            }`}
            aria-label={d.nav.lang}
          >
            <Translate size={18} weight="bold" aria-hidden />
            {d.nav.langCode}
          </button>
          <Link
            to="/finca"
            className={`hidden rounded-full px-5 py-2.5 font-bold transition sm:inline-block ${
              light ? 'bg-white text-bosque hover:bg-crema' : 'bg-bosque text-crema hover:bg-bosque-700'
            }`}
          >
            {d.nav.enter}
          </Link>
          <button
            type="button"
            className="rounded-full p-2 md:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label={open ? d.nav.close : d.nav.menu}
          >
            {open ? <X size={26} weight="bold" /> : <List size={26} weight="bold" />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-borde bg-crema px-5 pb-6 md:hidden">
          <ul className="flex flex-col py-2 text-lg font-semibold">
            {links.map((l) => (
              <li key={l.href}>
                {l.route ? (
                  <Link to={l.href} onClick={() => setOpen(false)} className="block py-3">
                    {l.label}
                  </Link>
                ) : (
                  <a href={l.href} onClick={() => setOpen(false)} className="block py-3">
                    {l.label}
                  </a>
                )}
              </li>
            ))}
          </ul>
          <Link
            to="/finca"
            onClick={() => setOpen(false)}
            className="block rounded-full bg-bosque px-5 py-3.5 text-center font-bold text-crema"
          >
            {d.nav.enter}
          </Link>
        </div>
      )}
    </header>
  )
}
