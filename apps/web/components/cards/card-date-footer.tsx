"use client"

import { CalendarIcon } from "lucide-react"

function formatDate(date: string) {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export function CardDateFooter({ date }: { date: string | null }) {
  if (!date) return null
  return (
    <div className="flex items-center justify-end px-4 pt-2">
      <span className="text-muted-foreground flex items-center gap-1.5 text-xs">
        <CalendarIcon className="size-3.5" />
        {formatDate(date)}
      </span>
    </div>
  )
}
