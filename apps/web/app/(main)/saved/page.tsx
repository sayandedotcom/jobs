"use client"

import * as React from "react"
import { api, type UserSavedJob } from "@/lib/api-client"
import { authClient } from "@/lib/auth-client"
import { BookmarkIcon } from "lucide-react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { Badge } from "@workspace/ui/components/badge"
import { Button } from "@workspace/ui/components/button"
import { Separator } from "@workspace/ui/components/separator"
import { Skeleton } from "@workspace/ui/components/skeleton"

function SavedJobSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/3" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-4 w-14" />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-3 w-1/2" />
      </CardContent>
    </Card>
  )
}

export default function SavedPage() {
  const { data: session } = authClient.useSession()
  const [savedJobs, setSavedJobs] = React.useState<UserSavedJob[]>([])
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    api.saved
      .list()
      .then(setSavedJobs)
      .finally(() => setLoading(false))
  }, [])

  const handleRemove = async (savedId: string) => {
    try {
      await api.saved.delete(savedId)
      setSavedJobs((prev) => prev.filter((j) => j.id !== savedId))
    } catch {
      // ignore
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Saved Jobs</h1>
      <Separator />

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <SavedJobSkeleton key={i} />
          ))}
        </div>
      ) : savedJobs.length === 0 ? (
        <div className="text-muted-foreground flex flex-col items-center gap-4 py-12 text-center">
          <BookmarkIcon className="size-12 opacity-20" />
          <p>No saved jobs yet. Browse jobs and save the ones you like.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {savedJobs.map((saved) => (
            <Card key={saved.id} className="transition-colors">
              <a href={`/jobs/${saved.listingId}`} className="block">
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <CardTitle className="leading-tight">
                        {saved.listing.title}
                      </CardTitle>
                      <p className="text-muted-foreground mt-1 text-sm">
                        {saved.listing.company}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {saved.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          handleRemove(saved.id)
                        }}
                        className="text-muted-foreground hover:text-destructive text-xs"
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                {saved.notes && (
                  <CardContent>
                    <p className="text-muted-foreground text-xs">
                      {saved.notes}
                    </p>
                  </CardContent>
                )}
              </a>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
