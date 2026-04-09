"use client"

import * as React from "react"
import { BookmarkIcon } from "lucide-react"
import { Button } from "@workspace/ui/components/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@workspace/ui/components/tooltip"
import { api, type Listing } from "@/lib/api-client"
import { toast } from "sonner"

export function useSaveJob(job: Listing) {
  const [saved, setSaved] = React.useState(job.isSaved)

  const handleSave = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      if (!saved) {
        await api.saved.create(job.id)
        setSaved(true)
        toast.success("Job bookmarked")
      } else {
        await api.saved.deleteByListing(job.id)
        setSaved(false)
        toast.success("Removed from bookmarks")
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
    <TooltipProvider delay={300}>
      <Tooltip>
        <TooltipTrigger
          render={
            <Button
              variant="ghost"
              size="icon"
              onClick={onClick}
              aria-label={saved ? "Remove bookmark" : "Add bookmark"}
              className="cursor-pointer"
            >
              <BookmarkIcon
                className="size-5"
                fill={saved ? "currentColor" : "none"}
              />
            </Button>
          }
        />
        <TooltipContent>
          {saved ? "Remove from bookmarks" : "Add bookmark"}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
