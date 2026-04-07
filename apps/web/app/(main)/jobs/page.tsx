"use client"

import * as React from "react"
import { JobCard, JobCardSkeleton } from "@/components/job-card"
import { JobSearchBar, JobFilterPanel } from "@/components/job-filters"
import { Button } from "@workspace/ui/components/button"
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"
import { api, type Listing } from "@/lib/api-client"
import { authClient } from "@/lib/auth-client"

const FAKE_JOBS: Listing[] = [
  {
    id: "fake-1",
    title: "Senior Frontend Engineer",
    company: "Vercel",
    description:
      "We are looking for a Senior Frontend Engineer to join our team and help build the future of web development. You will work on Next.js, Turbopack, and our deployment platform.",
    location: "San Francisco, CA",
    salary: "$180k - $250k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-01",
    createdAt: "2025-04-01T00:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-2",
    title: "Full Stack Developer",
    company: "Stripe",
    description:
      "Join Stripe's engineering team to build and scale payment infrastructure serving millions of businesses worldwide. You will work across the stack with Ruby, Python, and React.",
    location: "Remote",
    salary: "$160k - $220k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-02",
    createdAt: "2025-04-02T00:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-3",
    title: "Backend Engineer",
    company: "Supabase",
    description:
      "Help us build the open source Firebase alternative. Work on PostgreSQL tooling, real-time subscriptions, and edge functions with a globally distributed team.",
    location: "Remote",
    salary: "$140k - $200k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-03",
    createdAt: "2025-04-03T00:00:00Z",
    isSaved: true,
  },
  {
    id: "fake-4",
    title: "DevOps Engineer",
    company: "Cloudflare",
    description:
      "Work on the edge computing platform that powers a significant portion of the internet. Manage infrastructure, improve deployment pipelines, and optimize performance at scale.",
    location: "Austin, TX",
    salary: "$150k - $210k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-04",
    createdAt: "2025-04-04T00:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-5",
    title: "ML Engineer",
    company: "Anthropic",
    description:
      "Research and implement machine learning models for AI safety. Work closely with research scientists to build reliable, interpretable, and steerable AI systems.",
    location: "San Francisco, CA",
    salary: "$200k - $350k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-05",
    createdAt: "2025-04-05T00:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-6",
    title: "Platform Engineer",
    company: "Railway",
    description:
      "Build the next-generation cloud deployment platform. Work on container orchestration, build systems, and developer tooling that makes shipping software effortless.",
    location: "Remote",
    salary: "$150k - $210k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-05",
    createdAt: "2025-04-05T00:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-7",
    title: "iOS Engineer",
    company: "Loom",
    description:
      "Design and develop features for our iOS video messaging app used by millions of professionals. Strong experience with Swift, SwiftUI, and AVFoundation required.",
    location: "New York, NY",
    salary: "$170k - $240k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-06",
    createdAt: "2025-04-06T00:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-8",
    title: "Data Engineer",
    company: "Databricks",
    description:
      "Build and optimize large-scale data pipelines on Apache Spark and Delta Lake. Work with petabyte-scale datasets to power analytics and ML workloads for enterprise customers.",
    location: "Seattle, WA",
    salary: "$175k - $260k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-06",
    createdAt: "2025-04-06T00:00:00Z",
    isSaved: true,
  },
  {
    id: "fake-9",
    title: "Security Engineer",
    company: "1Password",
    description:
      "Help secure the password manager trusted by millions. Perform security audits, implement encryption protocols, and respond to vulnerabilities across our platforms.",
    location: "Remote",
    salary: "$155k - $215k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-07",
    createdAt: "2025-04-07T00:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-10",
    title: "Product Designer",
    company: "Linear",
    description:
      "Shape the future of project management tools. Own the end-to-end design of features from research to pixel-perfect implementation in a fast-moving, design-driven team.",
    location: "Remote",
    salary: "$140k - $200k",
    url: null,
    jobType: "Full-time",
    applyUrl: null,
    postedAt: "2025-04-07",
    createdAt: "2025-04-07T00:00:00Z",
    isSaved: false,
  },
]

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
        })
        setJobs(data.jobs)
        setTotal(data.total)
      } catch {
        setJobs(FAKE_JOBS)
        setTotal(FAKE_JOBS.length)
      } finally {
        setLoading(false)
      }
    }
    fetchJobs()
  }, [search, location, jobType, page, session?.user?.id])

  const totalPages = Math.ceil(total / 20)

  return (
    <div className="-mt-4 flex flex-col">
      <div className="bg-background sticky top-0 z-10 -mx-4 px-4 pt-4 pb-2">
        <JobSearchBar search={search} onSearchChange={setSearch} />
        <p className="text-muted-foreground mt-3 text-sm">
          {loading
            ? "Searching for jobs..."
            : `${total} job${total !== 1 ? "s" : ""} found`}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
        <div className="flex flex-col gap-3">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <JobCardSkeleton key={i} />
              ))}
            </div>
          ) : jobs.length > 0 ? (
            <div className="space-y-3">
              {jobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {FAKE_JOBS.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeftIcon className="size-4" />
                Previous
              </Button>
              <span className="text-muted-foreground text-sm">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
                <ChevronRightIcon className="size-4" />
              </Button>
            </div>
          )}
        </div>

        <div className="sticky top-[6.5rem] h-[calc(100vh-7.5rem)] self-start">
          <JobFilterPanel
            location={location}
            jobType={jobType}
            onLocationChange={setLocation}
            onJobTypeChange={setJobType}
          />
        </div>
      </div>
    </div>
  )
}
