"use client"

import * as React from "react"
import { authClient } from "@/lib/auth-client"
import { siteConfig } from "@/lib/site-config"
import { Button } from "@workspace/ui/components/button"
import { AnimatedBeamHero } from "@/components/animated-beam-hero"
import { Bot } from "lucide-react"
// import { LightRays } from "@workspace/ui/components/light-rays"
import { ShootingStars } from "@workspace/ui/components/shooting-stars"
import { StarsBackground } from "@workspace/ui/components/stars-background"
// import OrbitImages from "@workspace/ui/components/OrbitImages"
// import { images } from "./orbit-integrations"

export function Hero() {
  const signIn = () =>
    authClient.signIn.social({
      provider: siteConfig.auth.provider,
      callbackURL: siteConfig.auth.callbackUrl,
    })

  return (
    <div className="flex min-h-svh flex-col">
      <header className="sticky top-0 z-50 bg-transparent backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white">
              <Bot className="h-4 w-4 text-black" />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">
              {siteConfig.name}
            </span>
          </div>
          <Button onClick={signIn} className="cursor-pointer">
            Sign In
          </Button>
        </div>
        <StarsBackground />
      </header>

      <main className="flex flex-1 flex-col gap-6">
        <section className="bg-grid-white/[0.02] relative w-full overflow-hidden bg-black/[0.96] antialiased md:flex md:items-center md:justify-center">
          {/* <Spotlight /> */}
          {/* <LightRays /> */}
          <div className="relative z-10 mx-auto w-full px-4 md:px-0">
            <AnimatedBeamHero
              heading={siteConfig.hero.heading}
              headingHighlight={siteConfig.hero.headingHighlight}
              headingHighlightClass={siteConfig.hero.headingHighlightClass}
              subheading={siteConfig.hero.subheading}
              ctaText={siteConfig.hero.cta.text}
              ctaIcon={siteConfig.hero.cta.icon}
              ctaSubtext={siteConfig.hero.ctaSubtext}
              onCtaClick={signIn}
            />
            <h1 className="sr-only">
              {siteConfig.hero.heading} {siteConfig.hero.headingHighlight}
            </h1>
          </div>
          <ShootingStars />
          <StarsBackground />
        </section>
        {/* <section>
          <div className="relative">
            <OrbitImages
              images={images.slice(0, 14)}
              shape="ellipse"
              radiusX={350}
              radiusY={90}
              rotation={-6}
              duration={40}
              itemSize={40}
              responsive={true}
              baseWidth={800}
              radius={160}
              direction="normal"
              fill
              showPath
              paused={false}
              circular
              pathColor="rgba(180,180,200,0.35)"
              pathWidth={1}
            />
            <div className="absolute inset-0">
              <OrbitImages
                images={images.slice(14)}
                shape="ellipse"
                radiusX={200}
                radiusY={52}
                rotation={-6}
                duration={25}
                itemSize={36}
                responsive={true}
                baseWidth={800}
                radius={100}
                direction="normal"
                fill
                showPath
                paused={false}
                circular
                pathColor="rgba(180,180,200,0.3)"
                pathWidth={1}
              />
            </div>{" "}
            <ShootingStars />
            <StarsBackground />
          </div>
        </section> */}
        <section className="border-y border-white/10 bg-white/[0.02] px-6 py-12">
          <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-3">
            {siteConfig.stats.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-3xl font-bold tracking-tight text-white">
                  {s.value}
                </div>
                <div className="mt-1 text-sm text-neutral-400">{s.label}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-black px-6 py-20">
          <div className="mx-auto max-w-5xl">
            <div className="mb-12 text-center">
              <h2 className="text-3xl font-bold tracking-tight text-white">
                {siteConfig.features.heading}
              </h2>
              <p className="mt-3 text-neutral-400">
                {siteConfig.features.subheading}
              </p>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {siteConfig.features.items.map((f) => (
                <div
                  key={f.title}
                  className="group rounded-xl border border-white/10 p-6 transition-colors hover:border-white/20 hover:bg-white/[0.03]"
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-white/10 text-white">
                    <f.icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-white">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-neutral-400">
                    {f.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-white/10 bg-white/[0.02] px-6 py-20">
          <div className="mx-auto max-w-5xl">
            <div className="mb-12 text-center">
              <h2 className="text-3xl font-bold tracking-tight text-white">
                {siteConfig.testimonials.heading}
              </h2>
              <p className="mt-3 text-neutral-400">
                {siteConfig.testimonials.subheading}
              </p>
            </div>
            <div className="grid gap-6 sm:grid-cols-3">
              {siteConfig.testimonials.items.map((t) => (
                <div
                  key={t.name}
                  className="flex flex-col justify-between rounded-xl border border-white/10 p-6"
                >
                  <div>
                    <div className="mb-3 flex gap-0.5">
                      {[...Array(5)].map((_, i) => (
                        <svg
                          key={i}
                          className="h-4 w-4 fill-yellow-500 text-yellow-500"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                    <p className="text-sm leading-relaxed text-neutral-300">
                      &ldquo;{t.quote}&rdquo;
                    </p>
                  </div>
                  <div className="mt-4 border-t border-white/10 pt-4">
                    <div className="text-sm font-medium text-white">
                      {t.name}
                    </div>
                    <div className="text-xs text-neutral-500">{t.role}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-black px-6 py-16">
          <div className="mx-auto max-w-4xl text-center">
            <p className="mb-6 text-sm font-medium tracking-widest text-neutral-500 uppercase">
              {siteConfig.sources.heading}
            </p>
            <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4">
              {siteConfig.sources.logos.map((name) => (
                <span
                  key={name}
                  className="text-sm font-semibold tracking-wide text-neutral-500"
                >
                  {name}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-white/10 bg-black px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white">
              {siteConfig.bottomCta.heading}
            </h2>
            <p className="mt-4 text-lg text-neutral-400">
              {siteConfig.bottomCta.subheading}
            </p>
            <Button
              size="lg"
              onClick={signIn}
              className="mt-8 cursor-pointer gap-2 px-8"
            >
              {siteConfig.bottomCta.cta.text}
              <siteConfig.bottomCta.cta.icon className="h-4 w-4" />
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 bg-black px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-white">
              <Bot className="h-3 w-3 text-black" />
            </div>
            <span className="text-sm font-semibold text-white">
              {siteConfig.name}
            </span>
          </div>
          <p className="text-xs text-neutral-500">
            &copy; {new Date().getFullYear()} {siteConfig.footer.copyrightOwner}
            . All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}
