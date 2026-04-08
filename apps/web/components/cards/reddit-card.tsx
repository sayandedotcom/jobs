"use client"

import * as React from "react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { type Listing } from "@/lib/api-client"
import { useSaveJob } from "@/components/cards/use-save-job"
import { ShowMoreText } from "@/components/cards/show-more-text"
import { SourceBar } from "@/components/cards/source-bar"
import { CardDateFooter } from "@/components/cards/card-date-footer"

export function RedditCard({ job }: { job: Listing }) {
  const { saved, handleSave } = useSaveJob(job)
  const meta = job.metadata as Record<string, unknown> | null
  const postTitle = (meta?.title as string) || job.title

  return (
    <Card className="hover:bg-accent/50 transition-colors">
      <SourceBar
        sourceName={job.sourceName}
        saved={saved}
        onSave={handleSave}
      />
      <a
        href={job.url || `/jobs/${job.id}`}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <CardHeader>
          <CardTitle className="leading-tight">{postTitle}</CardTitle>
        </CardHeader>
        <CardContent>
          <ShowMoreText text={job.description} />
        </CardContent>
      </a>
      <CardDateFooter date={job.postedAt} />
    </Card>
  )
}
