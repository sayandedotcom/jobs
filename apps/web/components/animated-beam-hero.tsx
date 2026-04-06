"use client"

import { AnimatedBeam } from "@workspace/ui/components/animated-beam"
import { BorderBeam } from "@workspace/ui/components/border-beam"
import { Button } from "@workspace/ui/components/button"
import { cn } from "@workspace/ui/lib/utils"
import { AnimatePresence, motion } from "motion/react"
import Image from "next/image"
import React, { forwardRef, useRef, useState } from "react"

const Square = forwardRef<
  HTMLDivElement,
  {
    className?: string
    children?: React.ReactNode
    tooltip?: string
  }
>(({ className, children, tooltip }, ref) => {
  const [show, setShow] = useState(false)

  return (
    <div
      className={cn("group relative", className)}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      <AnimatePresence>
        {show && tooltip && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.85 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.85 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            className="absolute -top-10 left-1/2 z-50 -translate-x-1/2 rounded-md bg-black px-3 py-1.5 text-xs font-medium whitespace-nowrap text-white shadow-xl"
          >
            {tooltip}
          </motion.div>
        )}
      </AnimatePresence>
      <div
        ref={ref}
        className={cn(
          "relative z-10 flex size-12 items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-white shadow-[0_0_20px_-12px_rgba(255,255,255,0.3)] md:size-14"
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
    </div>
  )
})

Square.displayName = "Square"

interface SourceIcon {
  index: number
  id: string
  svg: string
  tooltip: string
}

const sourceIcons: SourceIcon[] = [
  {
    index: 1,
    id: "reddit",
    svg: "/integration-logos/reddit.svg",
    tooltip: "Reddit",
  },
  {
    index: 2,
    id: "x",
    svg: "/integration-logos/x.jpeg",
    tooltip: "X (Twitter)",
  },
  {
    index: 3,
    id: "ycombinator",
    svg: "/integration-logos/y-combinator.svg",
    tooltip: "Y Combinator",
  },
  {
    index: 4,
    id: "ashbyhq",
    svg: "/integration-logos/ashbyhq.png",
    tooltip: "Ashby HQ",
  },
  {
    index: 5,
    id: "greenhouse",
    svg: "/integration-logos/greenhouse.jpeg",
    tooltip: "Greenhouse",
  },
  {
    index: 6,
    id: "lever",
    svg: "/integration-logos/lever.jpeg",
    tooltip: "Lever",
  },
  {
    index: 7,
    id: "smartrecruiters",
    svg: "/integration-logos/smartrecruiters.svg",
    tooltip: "Smart Recruiters",
  },
  {
    index: 8,
    id: "weworkremotely",
    svg: "/integration-logos/weworkremotely.png",
    tooltip: "We Work Remotely",
  },
  {
    index: 9,
    id: "wellfound",
    svg: "/integration-logos/wellfound.jpeg",
    tooltip: "Wellfound",
  },
  {
    index: 10,
    id: "remoteok",
    svg: "/integration-logos/remoteok.jpeg",
    tooltip: "Remote OK",
  },
  {
    index: 11,
    id: "remotive",
    svg: "/integration-logos/remotive.jpeg",
    tooltip: "Remotive",
  },
  {
    index: 12,
    id: "arbeitnow",
    svg: "/integration-logos/arbeitnow.png",
    tooltip: "Arbeitnow",
  },
  {
    index: 13,
    id: "himalayas",
    svg: "/integration-logos/himalayas.jpeg",
    tooltip: "Himalayas",
  },
  {
    index: 14,
    id: "jobicy",
    svg: "/integration-logos/jobicy.png",
    tooltip: "Jobicy",
  },
  {
    index: 15,
    id: "teamtailor",
    svg: "/integration-logos/teamtailor.jpeg",
    tooltip: "Teamtailor",
  },
  {
    index: 16,
    id: "workable",
    svg: "/integration-logos/workable.jpeg",
    tooltip: "Workable",
  },
  {
    id: "linkedin",
    svg: "/integration-logos/linkedin.png",
    tooltip: "LinkedIn",
    index: 17,
  },
  {
    id: "indeed",
    svg: "/integration-logos/indeed.jpeg",
    tooltip: "Indeed",
    index: 18,
  },
  {
    id: "googlejobs",
    svg: "/integration-logos/google-jobs.jpeg",
    tooltip: "Google Jobs",
    index: 19,
  },
  {
    id: "4daysweek",
    svg: "/integration-logos/4days-week.png",
    tooltip: "4 Days Week",
    index: 20,
  },
  {
    id: "web3career",
    svg: "/integration-logos/web3-career.jpeg",
    tooltip: "Web3 Career",
    index: 21,
  },
]

interface NodeConfig {
  id: string
  position: string
  source: SourceIcon
}

interface BeamConfig {
  from: string
  to: string
  reverse?: boolean
  endYOffset?: number
}

const nodes: NodeConfig[] = Array.from({ length: 21 }, (_, i) => ({
  id: `n${i + 1}`,
  position: [
    "top-[8%] left-[8%]",
    "top-[6%] left-[25%]",
    "top-[6%] left-[42%]",
    "top-[10%] right-[10%]",
    "top-[10%] right-[28%]",
    "top-[38%] left-[8%]",
    "top-[38%] right-[8%]",
    "bottom-[12%] left-[8%]",
    "bottom-[10%] left-[22%]",
    "bottom-[10%] left-[35%]",
    "bottom-[8%] right-[12%]",
    "bottom-[8%] right-[28%]",
    "top-[22%] left-[20%]",
    "top-[24%] right-[20%]",
    "bottom-[29%] left-[18%]",
    "bottom-[26%] right-[22%]",
    "top-[14%] left-[58%]",
    "bottom-[5%] left-[55%]",
    "bottom-[18%] left-[48%]",
    "top-[60%] left-[4%]",
    "top-[60%] right-[10%]",
  ][i]!,
  source: sourceIcons[i % sourceIcons.length]!,
}))

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
  { from: "n17", to: "center" },
  { from: "n18", to: "center", reverse: true },
  { from: "n19", to: "center" },
  { from: "n20", to: "center", reverse: true },
  { from: "n21", to: "center", reverse: true },
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
          className={cn("absolute cursor-pointer", node.position)}
          tooltip={node.source.tooltip}
        >
          <Image
            src={node.source.svg}
            alt={node.source.tooltip}
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
