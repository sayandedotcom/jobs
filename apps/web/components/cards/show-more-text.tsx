"use client"

import * as React from "react"

const DESC_LIMIT = 300

export function ShowMoreText({
  text,
  limit = DESC_LIMIT,
}: {
  text: string
  limit?: number
}) {
  const [expanded, setExpanded] = React.useState(false)
  const isLong = text.length > limit
  const displayText = isLong && !expanded ? text.slice(0, limit) + "..." : text

  return (
    <>
      <p className="text-muted-foreground text-sm whitespace-pre-line">
        {displayText}
      </p>
      {isLong && (
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
    </>
  )
}
