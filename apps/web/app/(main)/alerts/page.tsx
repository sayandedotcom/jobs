"use client"

import * as React from "react"
import { api, type SavedSearch } from "@/lib/api-client"
import { authClient } from "@/lib/auth-client"
import { Input } from "@workspace/ui/components/input"

export default function AlertsPage() {
  const { data: session } = authClient.useSession()
  const [searches, setSearches] = React.useState<SavedSearch[]>([])
  const [loading, setLoading] = React.useState(true)
  const [keywords, setKeywords] = React.useState("")
  const [location, setLocation] = React.useState("")

  const fetchSearches = React.useCallback(async () => {
    try {
      const data = await api.searches.list()
      setSearches(data)
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    fetchSearches()
  }, [fetchSearches])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.searches.create({
        keywords: keywords || undefined,
        location: location || undefined,
      })
      setKeywords("")
      setLocation("")
      fetchSearches()
    } catch {
      // ignore
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await api.searches.delete(id)
      setSearches((prev) => prev.filter((s) => s.id !== id))
    } catch {
      // ignore
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Saved Searches</h1>

      <form onSubmit={handleCreate} className="flex gap-3">
        <Input
          placeholder="Keywords (e.g., React, Python)"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          className="flex-1"
        />
        <Input
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="w-48"
        />
        <button
          type="submit"
          className="bg-foreground text-background hover:bg-foreground/90 rounded-md px-4 py-2 text-sm font-medium"
        >
          Create Alert
        </button>
      </form>

      {loading ? (
        <div className="text-muted-foreground py-12 text-center">
          Loading...
        </div>
      ) : searches.length === 0 ? (
        <div className="text-muted-foreground py-12 text-center">
          No saved searches. Create one above to get notified about new jobs.
        </div>
      ) : (
        <div className="space-y-3">
          {searches.map((search) => (
            <div
              key={search.id}
              className="flex items-center justify-between rounded-lg border p-4"
            >
              <div>
                {search.keywords && (
                  <span className="font-medium">{search.keywords}</span>
                )}
                {search.location && (
                  <span className="text-muted-foreground ml-2 text-sm">
                    in {search.location}
                  </span>
                )}
                {search.jobType && (
                  <span className="text-muted-foreground ml-2 text-sm">
                    ({search.jobType})
                  </span>
                )}
              </div>
              <button
                onClick={() => handleDelete(search.id)}
                className="text-muted-foreground hover:text-destructive text-xs"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
