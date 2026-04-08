"use client"

import { buttonVariants } from "@workspace/ui/components/button"
import { cn } from "@workspace/ui/lib/utils"
import { ArrowUpRightIcon, CalendarIcon } from "lucide-react"

function formatDate(date: string) {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export function CardDateFooter({
  date,
  link,
  linkLabel,
}: {
  date: string | null
  link?: string | null
  linkLabel?: string | null
}) {
  if (!date && !link) return null
  return (
    <div className="flex items-center justify-between px-4 pt-2">
      {link && linkLabel ? (
        <a
          href={link}
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            buttonVariants({ variant: "outline", size: "sm" }),
            "cursor-pointer no-underline"
          )}
        >
          {linkLabel}
          <ArrowUpRightIcon className="size-3.5" />
        </a>
      ) : (
        <div />
      )}
      {date && (
        <span className="text-muted-foreground flex items-center gap-1.5 text-xs">
          <CalendarIcon className="size-3.5" />
          {formatDate(date)}
        </span>
      )}
    </div>
  )
}
