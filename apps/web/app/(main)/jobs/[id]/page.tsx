"use client"

import * as React from "react"
import Link from "next/link"
import { api, type Listing } from "@/lib/api-client"
import { authClient } from "@/lib/auth-client"
import { Badge } from "@workspace/ui/components/badge"

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = React.use(params)
  const { data: session } = authClient.useSession()
  const [job, setJob] = React.useState<Listing | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [saved, setSaved] = React.useState(false)

  React.useEffect(() => {
    api.jobs
      .get(id)
      .then(setJob)
      .finally(() => setLoading(false))
  }, [id])

  const handleSave = async () => {
    if (!job) return
    try {
      if (!saved) {
        await api.saved.create(job.id)
        setSaved(true)
      }
    } catch {
      // ignore
    }
  }

  if (loading) {
    return (
      <div className="text-muted-foreground py-12 text-center">Loading...</div>
    )
  }

  if (!job) {
    return (
      <div className="text-muted-foreground py-12 text-center">
        Job not found
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Link
        href="/jobs"
        className="text-muted-foreground hover:text-foreground text-sm"
      >
        ← Back to jobs
      </Link>

      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{job.title}</h1>
            <p className="text-muted-foreground mt-1 text-lg">{job.company}</p>
          </div>
          {session?.user?.id && (
            <button
              onClick={handleSave}
              className="hover:bg-accent rounded-md border px-4 py-2 text-sm"
            >
              {saved ? "Saved" : "Save Job"}
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {job.location && <Badge variant="outline">📍 {job.location}</Badge>}
          {job.salary && <Badge variant="outline">💰 {job.salary}</Badge>}
          {job.jobType && <Badge>{job.jobType}</Badge>}
        </div>

        <div className="rounded-lg border p-6 text-sm leading-relaxed whitespace-pre-wrap">
          {job.description}
        </div>

        <div className="flex gap-3">
          {job.applyUrl && (
            <a
              href={job.applyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-foreground text-background hover:bg-foreground/90 rounded-md px-6 py-2.5 text-sm font-medium"
            >
              Apply Now
            </a>
          )}
          {job.url && (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:bg-accent rounded-md border px-6 py-2.5 text-sm"
            >
              View Source
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
