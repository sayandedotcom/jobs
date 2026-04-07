"use client"

import * as React from "react"
import { BookmarkIcon } from "lucide-react"
import { Button } from "@workspace/ui/components/button"
import { api, type Listing } from "@/lib/api-client"

export function useSaveJob(job: Listing) {
  const [saved, setSaved] = React.useState(job.isSaved)

  const handleSave = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      if (!saved) {
        await api.saved.create(job.id)
        setSaved(true)
      } else {
        setSaved(false)
      }
    } catch {
      // ignore
    }
  }

  return { saved, handleSave }
}

export function SaveButton({
  saved,
  onClick,
}: {
  saved: boolean
  onClick: (e: React.MouseEvent) => void
}) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onClick}
      aria-label={saved ? "Unsave job" : "Save job"}
    >
      <BookmarkIcon className="size-5" fill={saved ? "currentColor" : "none"} />
    </Button>
  )
}
