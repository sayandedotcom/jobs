"use client"

import * as React from "react"
import { LinkIcon, UserIcon } from "lucide-react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { cn } from "@workspace/ui/lib/utils"
import { type Listing } from "@/lib/api-client"
import { useSaveJob } from "@/components/cards/use-save-job"
import { HtmlRenderer } from "@/components/html-renderer"
import { SourceBar } from "@/components/cards/source-bar"
import { CardDateFooter } from "@/components/cards/card-date-footer"

interface HackerNewsMetadata {
  commentId?: string | null
  headerLine?: string | null
  htmlContent?: string | null
  hnAuthor?: string | null
  storyId?: number | string | null
  storyTitle?: string | null
}

const COLLAPSED_HEIGHT = 200

function getHackerNewsMetadata(job: Listing): HackerNewsMetadata {
  return (job.metadata as HackerNewsMetadata | null) ?? {}
}

function plainTextToHtml(text: string): string {
  if (!text) return ""
  return text
    .split("\n\n")
    .map((paragraph) => `<p>${paragraph.replace(/\n/g, "<br>")}</p>`)
    .join("")
}

function getBodyHtml(job: Listing, metadata: HackerNewsMetadata): string {
  if (metadata.htmlContent) {
    return metadata.htmlContent
  }
  const description = job.description || ""
  const headerLine = metadata.headerLine || ""
  let body = description
  if (headerLine) {
    const lines = description.split("\n")
    if (lines[0]?.trim() === headerLine.trim()) {
      body = lines.slice(1).join("\n").trim() || description
    }
  }
  return plainTextToHtml(body)
}

function CollapsibleContent({ html }: { html: string }) {
  const ref = React.useRef<HTMLDivElement>(null)
  const [expanded, setExpanded] = React.useState(false)
  const [needsCollapse, setNeedsCollapse] = React.useState(false)

  React.useEffect(() => {
    const el = ref.current
    if (!el) return
    setNeedsCollapse(el.scrollHeight > COLLAPSED_HEIGHT)
  }, [html])

  return (
    <div>
      <div
        ref={ref}
        className={cn(
          "relative overflow-hidden transition-[max-height] duration-200",
          !expanded && needsCollapse && "max-h-[200px]"
        )}
        style={expanded || !needsCollapse ? { maxHeight: "none" } : undefined}
      >
        <HtmlRenderer content={html} />
        {!expanded && needsCollapse && (
          <div className="from-card pointer-events-none absolute right-0 bottom-0 left-0 h-12 bg-gradient-to-t to-transparent" />
        )}
      </div>
      {needsCollapse && (
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setExpanded((v) => !v)
          }}
          className="text-primary mt-1 cursor-pointer text-sm font-medium hover:underline"
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  )
}

export function HackerNewsCard({ job }: { job: Listing }) {
  const { saved, handleSave } = useSaveJob(job)
  const metadata = getHackerNewsMetadata(job)
  const headerLine = metadata.headerLine || job.title
  const storyTitle = metadata.storyTitle
  const author = metadata.hnAuthor
  const storyId = metadata.storyId
  const storyUrl =
    typeof storyId === "number" || typeof storyId === "string"
      ? `https://news.ycombinator.com/item?id=${storyId}`
      : undefined
  const bodyHtml = getBodyHtml(job, metadata)

  return (
    <Card className="hover:bg-accent/50 transition-colors">
      <SourceBar
        sourceName={job.sourceName}
        sourceUrl={storyUrl}
        saved={saved}
        onSave={handleSave}
      />
      <CardHeader className="space-y-3">
        <div className="space-y-1.5">
          <CardTitle className="text-lg leading-tight">
            <a
              href={job.url || `/jobs/${job.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              {headerLine}
            </a>
          </CardTitle>
          {storyTitle && (
            <p className="text-muted-foreground text-xs">{storyTitle}</p>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-muted-foreground flex flex-wrap items-center gap-3 text-xs">
          {author && (
            <span className="inline-flex items-center gap-1.5">
              <UserIcon className="size-3.5" />
              {author}
            </span>
          )}
          {metadata.commentId && (
            <span className="inline-flex items-center gap-1.5">
              <LinkIcon className="size-3.5" />
              Comment #{metadata.commentId}
            </span>
          )}
        </div>
        {bodyHtml && <CollapsibleContent html={bodyHtml} />}
      </CardContent>
      <CardDateFooter
        date={job.postedAt}
        link={job.url}
        linkLabel="View on HN"
      />
    </Card>
  )
}
