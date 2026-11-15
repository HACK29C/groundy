import { Link } from 'react-router'
import { GithubLogo } from '@phosphor-icons/react'
import { useDict } from '../../i18n/useDict'

const REPO = 'https://github.com/Tania-M11/Groundy'

export function SiteFooter() {
  const d = useDict()
  const f = d.footer
  return (
    <footer className="rounded-t-hoja bg-bosque text-crema">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 md:grid-cols-[1.4fr_1fr_1fr] md:px-8">
        <div>
          <img src="/brand/logo-groundy.webp" alt="Groundy" className="h-8 w-auto brightness-0 invert" />
          <p className="mt-4 max-w-xs text-crema/80">{d.hero.title}</p>
          <p className="mt-6 text-sm text-crema/70">{f.event}</p>
        </div>
        <nav aria-label={f.platform}>
          <h2 className="font-sans text-sm font-bold text-papa">{f.platform}</h2>
          <ul className="mt-4 space-y-2.5">
            <li>
              <Link to="/explorar" className="hover:underline">
                {f.explore}
              </Link>
            </li>
            <li>
              <Link to="/finca" className="hover:underline">
                {f.farm}
              </Link>
            </li>
            <li>
              <a href="/#datos" className="hover:underline">
                {f.methods}
              </a>
            </li>
          </ul>
        </nav>
        <nav aria-label={f.resources}>
          <h2 className="font-sans text-sm font-bold text-papa">{f.resources}</h2>
          <ul className="mt-4 space-y-2.5">
            <li>
              <a href="https://api.groundy.site/docs" target="_blank" rel="noreferrer" className="hover:underline">
                {f.api}
              </a>
            </li>
            <li>
              <a href={`${REPO}/blob/main/AI_USAGE.md`} target="_blank" rel="noreferrer" className="hover:underline">
                {f.ai}
              </a>
            </li>
            <li>
              <a href={REPO} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 hover:underline">
                <GithubLogo size={18} weight="bold" aria-hidden />
                {f.repo}
              </a>
            </li>
          </ul>
        </nav>
      </div>
      <p className="border-t border-white/10 px-5 py-5 text-center text-sm text-crema/70">{f.disclaimer}</p>
    </footer>
  )
}
