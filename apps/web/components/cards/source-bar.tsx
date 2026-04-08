"use client"

import * as React from "react"
import { source, type Source } from "@/config/source"
import { Badge } from "@workspace/ui/components/badge"
import { SaveButton } from "@/components/cards/use-save-job"

const SOURCE_ID_ALIASES: Record<string, string> = {
  hackernews: "ycombinator",
}

export function getSourceConfig(sourceName: string | null): Source | undefined {
  const id = sourceName ? (SOURCE_ID_ALIASES[sourceName] ?? sourceName) : null
  return source.find((s) => s.id === id)
}

const SOURCE_LABEL_SUFFIX: Record<string, string> = {
  hackernews: "HN Hiring",
}

export function SourceBar({
  sourceName,
  sourceUrl,
  saved,
  onSave,
}: {
  sourceName: string | null
  sourceUrl?: string
  saved: boolean
  onSave: (e: React.MouseEvent) => void
}) {
  const src = getSourceConfig(sourceName)
  const suffix = sourceName ? SOURCE_LABEL_SUFFIX[sourceName] : null
  const href = sourceUrl || src?.url
  return (
    <div className="flex items-center justify-between px-4 pb-2">
      {src && (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block"
        >
          <Badge
            variant="outline"
            className="hover:bg-accent/50 cursor-pointer gap-2 px-3 py-1.5 text-sm transition-colors"
          >
            <img
              src={src.src}
              alt={src.name}
              className="size-4 rounded-sm object-contain"
            />
            <span className="text-muted-foreground text-sm font-medium">
              {src.name}
              {suffix && (
                <span className="text-muted-foreground/70 ml-1">
                  ({suffix})
                </span>
              )}
            </span>
          </Badge>
        </a>
      )}
      <SaveButton saved={saved} onClick={onSave} />
    </div>
  )
}
