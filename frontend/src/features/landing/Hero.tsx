import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { Pause, Play, Sparkle } from '@phosphor-icons/react'
import { useDict } from '../../i18n/useDict'

/**
 * Hero. En el video la cámara termina acercándose y Potatonaut ocupa todo el centro,
 * así que el texto no va encima: en escritorio el video ocupa la izquierda y se funde
 * con el turquesa del cielo (mismo color que el token `cielo`), y el texto vive sobre ese cielo liso.
 * En móvil el texto va arriba y el video debajo. Una colina verde une ambos lados.
 * Contraste: título y entrada son texto grande (≥ 19 px en negrita) blanco sobre cielo → 3,2:1 (AA texto grande).
 */
export function Hero() {
  const d = useDict()
  const video = useRef<HTMLVideoElement>(null)
  const [playing, setPlaying] = useState(true)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      video.current?.pause()
      setPlaying(false)
    }
  }, [])

  const toggle = () => {
    const v = video.current
    if (!v) return
    if (v.paused) {
      void v.play()
      setPlaying(true)
    } else {
      v.pause()
      setPlaying(false)
    }
  }

  return (
    <section className="relative isolate flex flex-col overflow-hidden bg-[linear-gradient(to_bottom,#2f8aa3,#3c9cb4_45%)] md:block md:min-h-[100svh] md:bg-cielo">
      {/* Video */}
      <div className="relative order-2 h-[52svh] md:absolute md:inset-y-0 md:left-0 md:h-auto md:w-[66%]">
        <video
          ref={video}
          className="h-full w-full object-cover [mask-image:linear-gradient(to_bottom,transparent,black_22%)] md:[mask-image:linear-gradient(to_right,black_74%,transparent)]"
          autoPlay
          muted
          loop
          playsInline
          poster="/media/hero-poster.webp"
          aria-hidden
        >
          <source src="/media/hero-854.mp4" type="video/mp4" media="(max-width: 760px)" />
          <source src="/media/hero-1280.mp4" type="video/mp4" />
        </video>
        <div className="absolute bottom-20 left-4 z-10 flex items-center gap-2 md:bottom-32 md:left-8">
          <button
            type="button"
            onClick={toggle}
            className="grid size-10 place-items-center rounded-full bg-white/85 text-bosque shadow-suave backdrop-blur transition hover:bg-white"
            aria-label={playing ? d.hero.pause : d.hero.play}
          >
            {playing ? <Pause size={18} weight="fill" /> : <Play size={18} weight="fill" />}
          </button>
          <span className="rounded-full bg-black/35 px-3 py-1 text-xs font-semibold text-white backdrop-blur-sm">
            {d.hero.aiNote}
          </span>
        </div>
      </div>

      {/* Texto sobre el cielo */}
      <div className="relative order-1 mx-auto w-full max-w-6xl px-5 pt-24 md:flex md:min-h-[100svh] md:items-center md:justify-end md:px-8 md:pt-16 md:pb-28">
        <div className="hero-entrada text-white md:w-[40%] md:min-w-[22rem]">
          <p className="inline-flex items-center gap-2 rounded-full bg-white/18 px-3.5 py-1.5 text-sm font-bold">
            <Sparkle size={16} weight="fill" className="text-papa" aria-hidden />
            {d.hero.badge}
          </p>
          <h1 className="mt-5 text-[2.6rem] leading-[1.04] text-white sm:text-6xl lg:text-[4.25rem]">
            {d.hero.title}
          </h1>
          <p className="mt-5 max-w-md text-[1.2rem] leading-relaxed font-bold text-white md:text-xl">{d.hero.lead}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/finca"
              className="rounded-full bg-bosque px-7 py-3.5 font-bold text-crema shadow-flota transition hover:bg-bosque-700"
            >
              {d.hero.cta1}
            </Link>
            <Link to="/explorar" className="rounded-full bg-white px-7 py-3.5 font-bold text-bosque transition hover:bg-crema">
              {d.hero.cta2}
            </Link>
          </div>
        </div>
      </div>

      {/* Colinas: una verde que continúa el pasto del video y la curva crema que da paso a la página. */}
      <svg
        aria-hidden
        className="absolute inset-x-0 bottom-0 z-0 h-20 w-full md:h-32"
        viewBox="0 0 1440 160"
        preserveAspectRatio="none"
      >
        <path fill="#7AB22A" d="M0 96 C 320 58 640 44 940 56 S 1300 78 1440 34 V160 H0 Z" />
        <path fill="#FFF9F5" d="M0 128 C 260 92 540 84 790 108 S 1220 158 1440 112 V160 H0 Z" />
      </svg>
    </section>
  )
}
