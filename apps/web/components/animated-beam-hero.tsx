"use client"

import { AnimatedBeam } from "@workspace/ui/components/animated-beam"
import { BorderBeam } from "@workspace/ui/components/border-beam"
import { Button } from "@workspace/ui/components/button"
import { cn } from "@workspace/ui/lib/utils"
import Image from "next/image"
import React, { forwardRef, useRef } from "react"

const Square = forwardRef<
  HTMLDivElement,
  { className?: string; children?: React.ReactNode }
>(({ className, children }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "relative z-10 flex size-12 items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-black shadow-[0_0_20px_-12px_rgba(255,255,255,0.3)] md:size-14",
        className
      )}
    >
      {children}
      <BorderBeam
        size={40}
        duration={4}
        colorFrom="#e0e0e0"
        colorTo="#ffffff"
        borderWidth={1.5}
      />
    </div>
  )
})

Square.displayName = "Square"

interface NodeConfig {
  id: string
  position: string
}

interface BeamConfig {
  from: string
  to: string
  reverse?: boolean
  endYOffset?: number
}

const nodes: NodeConfig[] = [
  { id: "n1", position: "top-[8%] left-[8%]" },
  { id: "n2", position: "top-[6%] left-[25%]" },
  { id: "n3", position: "top-[6%] left-[42%]" },
  { id: "n4", position: "top-[10%] right-[10%]" },
  { id: "n5", position: "top-[10%] right-[28%]" },
  { id: "n6", position: "top-[38%] left-[8%]" },
  { id: "n7", position: "top-[38%] right-[8%]" },
  { id: "n8", position: "bottom-[12%] left-[8%]" },
  { id: "n9", position: "bottom-[10%] left-[22%]" },
  { id: "n10", position: "bottom-[10%] left-[40%]" },
  { id: "n11", position: "bottom-[8%] right-[12%]" },
  { id: "n12", position: "bottom-[8%] right-[28%]" },
  { id: "n13", position: "top-[22%] left-[20%]" },
  { id: "n14", position: "top-[24%] right-[20%]" },
  { id: "n15", position: "bottom-[24%] left-[18%]" },
  { id: "n16", position: "bottom-[26%] right-[22%]" },
]

const beams: BeamConfig[] = [
  { from: "n1", to: "center" },
  { from: "n2", to: "center" },
  { from: "n3", to: "center" },
  { from: "n4", to: "center" },
  { from: "n5", to: "center", reverse: true },
  { from: "n6", to: "center" },
  { from: "n7", to: "center", reverse: true },
  { from: "n8", to: "center" },
  { from: "n9", to: "center", reverse: true },
  { from: "n10", to: "center" },
  { from: "n11", to: "center", reverse: true },
  { from: "n12", to: "center", reverse: true },
  { from: "n13", to: "center" },
  { from: "n14", to: "center", reverse: true },
  { from: "n15", to: "center" },
  { from: "n16", to: "center", reverse: true },
]

const beamGradient = {
  pathColor: "white",
  pathOpacity: 0.1,
  gradientStartColor: "#c0c0c0",
  gradientStopColor: "#ffffff",
}

export function AnimatedBeamHero({
  heading,
  headingHighlight,
  headingHighlightClass,
  subheading,
  ctaText,
  ctaIcon: CtaIcon,
  ctaSubtext,
  onCtaClick,
}: {
  heading: string
  headingHighlight: string
  headingHighlightClass: string
  subheading: string
  ctaText: string
  ctaIcon: React.ComponentType<{ className?: string }>
  ctaSubtext: string
  onCtaClick: () => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const centerRef = useRef<HTMLDivElement>(null)
  const nodeRefs = useRef<Record<string, HTMLDivElement | null>>({})

  return (
    <div
      className="relative min-h-[800px] w-full overflow-hidden"
      ref={containerRef}
    >
      {nodes.map((node) => (
        <Square
          key={node.id}
          ref={(el) => {
            nodeRefs.current[node.id] = el
          }}
          className={cn("absolute", node.position)}
        >
          <Image
            src="/svg/reddit.svg"
            alt="Reddit"
            width={40}
            height={40}
            className="size-full"
          />
        </Square>
      ))}

      <div
        ref={centerRef}
        className="absolute top-1/2 left-1/2 z-20 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center rounded-3xl px-5 py-5 text-center"
      >
        <div className="absolute inset-0 rounded-3xl bg-black/60 [mask-image:radial-gradient(ellipse_at_center,black_50%,transparent_100%)] backdrop-blur-xl" />
        <h1 className="relative z-10 bg-gradient-to-b from-neutral-50 to-neutral-400 bg-clip-text text-6xl font-bold text-transparent sm:text-7xl md:text-8xl lg:text-8xl">
          {heading}
          <br />
          <span className={headingHighlightClass}>{headingHighlight}</span>
        </h1>
        <p className="relative z-10 mx-auto mt-4 max-w-lg text-center text-base font-normal text-neutral-300">
          {subheading}
        </p>
        <div className="relative z-10 mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Button
            size="lg"
            onClick={onCtaClick}
            className="cursor-pointer gap-2 px-8"
          >
            {ctaText}
            <CtaIcon className="h-4 w-4" />
          </Button>
          <p className="text-xs text-neutral-500">{ctaSubtext}</p>
        </div>
      </div>

      {beams.map((beam, i) => (
        <AnimatedBeam
          key={i}
          containerRef={containerRef}
          fromRef={{
            get current() {
              return nodeRefs.current[beam.from] ?? null
            },
          }}
          toRef={centerRef}
          reverse={beam.reverse}
          endYOffset={beam.endYOffset}
          delay={i * 0.3}
          {...beamGradient}
        />
      ))}
    </div>
  )
}
