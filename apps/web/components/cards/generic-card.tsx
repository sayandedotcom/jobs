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

export function GenericCard({ job }: { job: Listing }) {
  const { saved, handleSave } = useSaveJob(job)

  return (
    <Card className="hover:bg-accent/50 transition-colors">
      <a
        href={job.url || `/jobs/${job.id}`}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <SourceBar
          sourceName={job.sourceName}
          saved={saved}
          onSave={handleSave}
        />
        <CardHeader>
          <CardTitle className="leading-tight">{job.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <ShowMoreText text={job.description} />
        </CardContent>
        <CardDateFooter date={job.postedAt} />
      </a>
    </Card>
  )
}
