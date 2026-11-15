import { Link } from 'react-router'
import { SiteNav } from './SiteNav'
import { useDict } from '../../i18n/useDict'

/** Página provisional para rutas que se construyen en pasos siguientes (Explorar en F6, Mi finca desde F2). */
export default function ComingSoonPage() {
  const d = useDict()
  return (
    <>
      <SiteNav />
      <main className="mx-auto flex min-h-[100svh] max-w-xl flex-col items-center justify-center px-5 pt-20 text-center">
        <img src="/brand/potatonaut-256.webp" alt="" className="w-36 drop-shadow-xl" />
        <h1 className="mt-6 text-4xl">{d.soon.title}</h1>
        <p className="mt-3 text-lg text-gris">{d.soon.lead}</p>
        <Link to="/" className="mt-8 rounded-full bg-bosque px-7 py-3.5 font-bold text-crema">
          {d.soon.back}
        </Link>
      </main>
    </>
  )
}
