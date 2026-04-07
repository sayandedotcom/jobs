"use client"

import { type Listing } from "@/lib/api-client"
import { RedditCard } from "@/components/cards/reddit-card"
import { HackerNewsCard } from "@/components/cards/hacker-news-card"
import { TwitterCard } from "@/components/cards/twitter-card"
import { GenericCard } from "@/components/cards/generic-card"
import { JobCardSkeleton } from "@/components/cards/job-card-skeleton"

export function JobCard({ job }: { job: Listing }) {
  const source = job.sourceName
  if (source === "reddit") return <RedditCard job={job} />
  if (source === "hackernews") return <HackerNewsCard job={job} />
  if (source === "x") return <TwitterCard job={job} />
  return <GenericCard job={job} />
}

export { JobCardSkeleton }
