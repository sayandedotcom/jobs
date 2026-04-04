"use client"

import * as React from "react"
import { JobCard } from "@/components/job-card"
import { JobFilters } from "@/components/job-filters"
import { api, type Listing } from "@/lib/api-client"
import { authClient } from "@/lib/auth-client"

export default function JobsPage() {
  const { data: session } = authClient.useSession()
  const [jobs, setJobs] = React.useState<Listing[]>([])
  const [total, setTotal] = React.useState(0)
  const [page, setPage] = React.useState(1)
  const [loading, setLoading] = React.useState(true)
  const [search, setSearch] = React.useState("")
  const [location, setLocation] = React.useState("")
  const [jobType, setJobType] = React.useState("all")

  React.useEffect(() => {
    const fetchJobs = async () => {
      setLoading(true)
      try {
        const data = await api.jobs.list({
          search: search || undefined,
          location: location || undefined,
          jobType: jobType === "all" ? undefined : jobType,
          page,
          pageSize: 20,
          userId: session?.user?.id,
        })
        setJobs(data.jobs)
        setTotal(data.total)
      } catch {
        // ignore
      } finally {
        setLoading(false)
      }
    }
    fetchJobs()
  }, [search, location, jobType, page, session?.user?.id])

  const totalPages = Math.ceil(total / 20)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Jobs</h1>
        <p className="text-muted-foreground text-sm">
          {total} job{total !== 1 ? "s" : ""} found from Reddit and other
          sources
        </p>
      </div>

      <JobFilters
        search={search}
        location={location}
        jobType={jobType}
        onSearchChange={setSearch}
        onLocationChange={setLocation}
        onJobTypeChange={setJobType}
      />

      {loading ? (
        <div className="text-muted-foreground py-12 text-center">
          Loading jobs...
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-muted-foreground py-12 text-center">
          No jobs found. Try adjusting your filters.
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} userId={session?.user?.id} />
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-muted-foreground text-sm">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
