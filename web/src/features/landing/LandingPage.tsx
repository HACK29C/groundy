import { SiteNav } from './SiteNav'
import { Hero } from './Hero'
import { Challenge, Platform, ScaleLens, DataSources, HowItWorks, MeetPotatonaut, TeamAndCta } from './Sections'
import { SiteFooter } from './SiteFooter'

export default function LandingPage() {
  return (
    <>
      <SiteNav overHero />
      <main>
        <Hero />
        <Challenge />
        <Platform />
        <ScaleLens />
        <DataSources />
        <HowItWorks />
        <MeetPotatonaut />
        <TeamAndCta />
      </main>
      <SiteFooter />
    </>
  )
}
