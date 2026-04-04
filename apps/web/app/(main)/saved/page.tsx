"use client"

import * as React from "react"
import { api, type UserSavedJob } from "@/lib/api-client"
import { useSession } from "next-auth/react"

export default function SavedPage() {
  const { data: session } = useSession()
  const [savedJobs, setSavedJobs] = React.useState<UserSavedJob[]>([])
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    if (!session?.user?.id) return
    api.saved
      .list(session.user.id)
      .then(setSavedJobs)
      .finally(() => setLoading(false))
  }, [session?.user?.id])

  const handleRemove = async (savedId: string) => {
    if (!session?.user?.id) return
    try {
      await api.saved.delete(savedId, session.user.id)
      setSavedJobs((prev) => prev.filter((j) => j.id !== savedId))
    } catch {
      // ignore
    }
  }

  if (loading) {
    return (
      <div className="text-muted-foreground py-12 text-center">Loading...</div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Saved Jobs</h1>

      {savedJobs.length === 0 ? (
        <div className="text-muted-foreground py-12 text-center">
          No saved jobs yet. Browse jobs and save the ones you like.
        </div>
      ) : (
        <div className="space-y-3">
          {savedJobs.map((saved) => (
            <div
              key={saved.id}
              className="flex items-start justify-between rounded-lg border p-4"
            >
              <a href={`/jobs/${saved.listingId}`} className="min-w-0 flex-1">
                <h3 className="font-medium">{saved.listing.title}</h3>
                <p className="text-muted-foreground text-sm">
                  {saved.listing.company}
                </p>
                {saved.notes && (
                  <p className="text-muted-foreground mt-1 text-xs">
                    {saved.notes}
                  </p>
                )}
              </a>
              <div className="flex items-center gap-2">
                <span className="bg-secondary rounded-full px-2 py-0.5 text-xs">
                  {saved.status}
                </span>
                <button
                  onClick={() => handleRemove(saved.id)}
                  className="text-muted-foreground hover:text-destructive text-xs"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
