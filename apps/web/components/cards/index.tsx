"use client"

import * as React from "react"
import { type Listing } from "@/lib/api-client"
import { RedditCard } from "@/components/cards/reddit-card"
import { HackerNewsCard } from "@/components/cards/hacker-news-card"
import { GenericCard } from "@/components/cards/generic-card"
import { JobCardSkeleton } from "@/components/cards/job-card-skeleton"

const CARD_REGISTRY: Record<string, React.ComponentType<{ job: Listing }>> = {
  reddit: RedditCard,
  hackernews: HackerNewsCard,
}

export function JobCard({ job }: { job: Listing }) {
  const source = job.sourceName
  const CardComponent = source ? CARD_REGISTRY[source] : undefined
  if (CardComponent) {
    return <CardComponent job={job} />
  }
  return <GenericCard job={job} />
}

export { JobCardSkeleton }
