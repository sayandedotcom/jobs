"use client"

import * as React from "react"
import { JobCard, JobCardSkeleton } from "@/components/cards"
import {
  JobSearchBar,
  JobFilterPanel,
  sourceIdToSourceName,
} from "@/components/job-filters"
import { Button } from "@workspace/ui/components/button"
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"
import { api, type Listing } from "@/lib/api-client"
import { authClient } from "@/lib/auth-client"

const FAKE_JOBS: Listing[] = [
  {
    id: "fake-reddit-1",
    title:
      "[Hiring] Senior Frontend Engineer (React/TypeScript) - $180k-$250k - Remote",
    company: "vercel_official",
    description:
      "Title: [Hiring] Senior Frontend Engineer (React/TypeScript) - $180k-$250k - Remote\n\nBody: We are looking for a Senior Frontend Engineer to join our team and help build the future of web development. You will work on Next.js, Turbopack, and our deployment platform, collaborating with a world-class team of engineers, designers, and product managers. You will be responsible for building performant, accessible UI components and contributing to open source projects. Ideal candidates have 5+ years of experience with React, TypeScript, and modern CSS. Experience with server-side rendering, edge computing, and build tooling is a strong plus. We offer competitive compensation, flexible PTO, and a fully remote work environment.\n\nFlair: [Hiring]\n\nURL: https://vercel.com/careers",
    location: null,
    salary: null,
    url: "https://reddit.com/r/forhire/comments/abc123",
    jobType: null,
    applyUrl: null,
    sourceName: "reddit",
    metadata: {
      subreddit: "forhire",
      score: 156,
      numComments: 42,
      flair: "Hiring",
      title:
        "[Hiring] Senior Frontend Engineer (React/TypeScript) - $180k-$250k - Remote",
    },
    postedAt: "2025-04-01T14:30:00Z",
    createdAt: "2025-04-01T14:30:00Z",
    isSaved: false,
  },
  {
    id: "fake-reddit-2",
    title: "[Hiring] Full Stack Developer - Stripe - Remote - $160k-$220k",
    company: "stripe_eng",
    description:
      "Title: [Hiring] Full Stack Developer - Stripe - Remote - $160k-$220k\n\nBody: Join Stripe's engineering team to build and scale payment infrastructure serving millions of businesses worldwide. You will work across the stack with Ruby, Python, and React, building APIs and dashboards that process billions of dollars in transactions. Our engineering culture values clean code, thorough testing, and iterative development. You will participate in code reviews, architecture discussions, and on-call rotations. We are looking for developers who are passionate about developer experience and building reliable financial systems. Experience with distributed systems, PostgreSQL, and real-time data processing is highly valued. Hybrid work model with offices in San Francisco, Seattle, and Dublin.\n\nFlair: [Hiring]",
    location: null,
    salary: null,
    url: "https://reddit.com/r/remotejobs/comments/def456",
    jobType: null,
    applyUrl: null,
    sourceName: "reddit",
    metadata: {
      subreddit: "remotejobs",
      score: 89,
      numComments: 23,
      flair: "Hiring",
      title: "[Hiring] Full Stack Developer - Stripe - Remote - $160k-$220k",
    },
    postedAt: "2025-04-02T09:15:00Z",
    createdAt: "2025-04-02T09:15:00Z",
    isSaved: false,
  },
  {
    id: "fake-reddit-3",
    title:
      "We're hiring! Backend Engineer (Go/Rust) at Supabase - Fully Remote",
    company: "supabase_careers",
    description:
      "Title: We're hiring! Backend Engineer (Go/Rust) at Supabase - Fully Remote\n\nBody: Help us build the open source Firebase alternative. Work on PostgreSQL tooling, real-time subscriptions, and edge functions with a globally distributed team. You will contribute to our core database engine, authentication system, storage layer, and auto-generated API endpoints. We are a remote-first company with team members across 20+ countries. Strong experience with PostgreSQL internals, Go or Rust, and distributed systems is preferred. You will also engage with our vibrant open source community, review pull requests, and write technical blog posts.\n\nFlair: [For Hire]",
    location: null,
    salary: null,
    url: "https://reddit.com/r/golang/comments/ghi789",
    jobType: null,
    applyUrl: null,
    sourceName: "reddit",
    metadata: {
      subreddit: "golang",
      score: 234,
      numComments: 67,
      flair: "For Hire",
      title:
        "We're hiring! Backend Engineer (Go/Rust) at Supabase - Fully Remote",
    },
    postedAt: "2025-04-03T11:45:00Z",
    createdAt: "2025-04-03T11:45:00Z",
    isSaved: true,
  },
  {
    id: "fake-hn-1",
    title:
      "Vercel | Senior Frontend Engineer | Remote | Full-time | https://vercel.com/careers",
    company: "tobiloba",
    description:
      "Vercel | Senior Frontend Engineer | Remote | Full-time\n\nWe are looking for a Senior Frontend Engineer to join our team and help build the future of web development. You will work on Next.js, Turbopack, and our deployment platform. You will be responsible for building performant, accessible UI components and contributing to open source projects.\n\nIdeal candidates have 5+ years of experience with React, TypeScript, and modern CSS. Experience with server-side rendering, edge computing, and build tooling is a strong plus.\n\nWe offer competitive compensation ($180k-$250k), flexible PTO, and a fully remote work environment.\n\nApply at https://vercel.com/careers",
    location: null,
    salary: null,
    url: "https://news.ycombinator.com/item?id=43864723",
    jobType: null,
    applyUrl: null,
    sourceName: "hackernews",
    metadata: {
      points: 87,
      story_id: 43864723,
      parent_story_title: "Ask HN: Who is hiring? (April 2025)",
    },
    postedAt: "2025-04-01T08:00:00Z",
    createdAt: "2025-04-01T08:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-hn-2",
    title: "Cloudflare | DevOps Engineer | Austin, TX or Remote | Full-time",
    company: "cloudflare-hiring",
    description:
      "Cloudflare | DevOps Engineer | Austin, TX or Remote | Full-time\n\nWork on the edge computing platform that powers a significant portion of the internet. Manage infrastructure, improve deployment pipelines, and optimize performance at scale.\n\nYou will design and maintain CI/CD systems that deploy hundreds of times per day across our global network spanning 300+ cities. Experience with Kubernetes, Terraform, and observability tools like Prometheus and Grafana is essential. You will also work on capacity planning, incident response, and disaster recovery procedures.\n\nCompensation: $150k-$210k + equity. Apply at https://cloudflare.com/careers",
    location: null,
    salary: null,
    url: "https://news.ycombinator.com/item?id=43864724",
    jobType: null,
    applyUrl: null,
    sourceName: "hackernews",
    metadata: {
      points: 54,
      story_id: 43864723,
      parent_story_title: "Ask HN: Who is hiring? (April 2025)",
    },
    postedAt: "2025-04-04T10:30:00Z",
    createdAt: "2025-04-04T10:30:00Z",
    isSaved: false,
  },
  {
    id: "fake-hn-3",
    title: "Anthropic | ML Engineer | San Francisco | Full-time | $200k-$350k",
    company: "anthropic-recruiting",
    description:
      "Anthropic | ML Engineer | San Francisco | Full-time | $200k-$350k\n\nResearch and implement machine learning models for AI safety. Work closely with research scientists to build reliable, interpretable, and steerable AI systems. You will train and evaluate large language models, develop novel alignment techniques, and contribute to our safety research agenda.\n\nStrong background in deep learning, transformers, and reinforcement learning from human feedback (RLHF) is required. Experience with PyTorch, distributed training on GPU clusters, and efficient inference optimization is highly valued.\n\nWe are looking for individuals who are passionate about ensuring AI systems are safe and beneficial. The role involves writing research papers, implementing production-grade ML pipelines, and collaborating with cross-functional teams to translate research into real-world impact.\n\nApply at https://anthropic.com/careers",
    location: null,
    salary: null,
    url: "https://news.ycombinator.com/item?id=43864725",
    jobType: null,
    applyUrl: null,
    sourceName: "hackernews",
    metadata: {
      points: 142,
      story_id: 43864723,
      parent_story_title: "Ask HN: Who is hiring? (April 2025)",
    },
    postedAt: "2025-04-05T16:00:00Z",
    createdAt: "2025-04-05T16:00:00Z",
    isSaved: true,
  },
  {
    id: "fake-hn-4",
    title: "Railway | Platform Engineer | Remote | Full-time",
    company: "railway-dev",
    description:
      "Railway | Platform Engineer | Remote | Full-time\n\nBuild the next-generation cloud deployment platform. Work on container orchestration, build systems, and developer tooling that makes shipping software effortless.\n\nYou will design and implement core infrastructure components including our build pipeline, service mesh, and monitoring stack. We use Rust for performance-critical paths and TypeScript for our control plane. Experience with Docker, Kubernetes, and infrastructure-as-code is essential.\n\nYou will also contribute to our public API, CLI tools, and GitHub integrations. Our team is small but mighty, and every engineer has a significant impact on the product. We value simplicity, developer experience, and building tools that we ourselves love to use.\n\n$150k-$210k + equity. Remote-first with quarterly in-person meetups. Apply at https://railway.app/careers",
    location: null,
    salary: null,
    url: "https://news.ycombinator.com/item?id=43864726",
    jobType: null,
    applyUrl: null,
    sourceName: "hackernews",
    metadata: {
      points: 76,
      story_id: 43864723,
      parent_story_title: "Ask HN: Who is hiring? (April 2025)",
    },
    postedAt: "2025-04-05T12:00:00Z",
    createdAt: "2025-04-05T12:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-x-1",
    title: "Just opened roles at Stripe...",
    company: "stripe",
    description:
      "Author: @stripe\n\nText: Just opened roles at Stripe 🧵\n\n1/ Senior Full Stack Developer (Remote, $160k-$220k)\nJoin our engineering team to build and scale payment infrastructure serving millions of businesses worldwide. You will work across the stack with Ruby, Python, and React.\n\n2/ Staff Data Engineer (Seattle, $175k-$260k)\nBuild and optimize large-scale data pipelines on Apache Spark and Delta Lake. Work with petabyte-scale datasets.\n\nApply: https://stripe.com/jobs\n\nURLs: https://stripe.com/jobs",
    location: null,
    salary: null,
    url: "https://x.com/stripe/status/1234567890",
    jobType: null,
    applyUrl: null,
    sourceName: "x",
    metadata: {
      retweet_count: 342,
      like_count: 1205,
      reply_count: 89,
      quote_count: 67,
      username: "stripe",
      display_name: "Stripe",
    },
    postedAt: "2025-04-02T14:00:00Z",
    createdAt: "2025-04-02T14:00:00Z",
    isSaved: false,
  },
  {
    id: "fake-x-2",
    title: "1Password is hiring Security Engineers!",
    company: "1Password",
    description:
      "Author: @1Password\n\nText: 1Password is hiring Security Engineers! 🔐\n\nHelp secure the password manager trusted by millions. You will work on our zero-knowledge security architecture, end-to-end encryption, and secure key derivation functions. Experience with cryptographic protocols (AES, Argon2, SRP), secure code review, and penetration testing is essential.\n\nFully remote, $155k-$215k.\n\nApply: https://1password.com/jobs\n\nURLs: https://1password.com/jobs",
    location: null,
    salary: null,
    url: "https://x.com/1Password/status/2345678901",
    jobType: null,
    applyUrl: null,
    sourceName: "x",
    metadata: {
      retweet_count: 156,
      like_count: 523,
      reply_count: 34,
      quote_count: 28,
      username: "1Password",
      display_name: "1Password",
    },
    postedAt: "2025-04-07T10:30:00Z",
    createdAt: "2025-04-07T10:30:00Z",
    isSaved: false,
  },
  {
    id: "fake-x-3",
    title: "We're building the future of project management at Linear",
    company: "linear",
    description:
      "Author: @linear\n\nText: We're building the future of project management at Linear ✨\n\nNow hiring Product Designers who want to shape the way teams work. Own the end-to-end design of features from research to pixel-perfect implementation in a fast-moving, design-driven team. We believe great design is a competitive advantage.\n\nRemote, $140k-$200k + equity. Strong portfolio required.\n\nApply: https://linear.app/careers\n\nURLs: https://linear.app/careers",
    location: null,
    salary: null,
    url: "https://x.com/linear/status/3456789012",
    jobType: null,
    applyUrl: null,
    sourceName: "x",
    metadata: {
      retweet_count: 89,
      like_count: 412,
      reply_count: 45,
      quote_count: 31,
      username: "linear",
      display_name: "Linear",
    },
    postedAt: "2025-04-07T16:00:00Z",
    createdAt: "2025-04-07T16:00:00Z",
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
  const [selectedSources, setSelectedSources] = React.useState<string[]>([])

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

  const filteredJobs = React.useMemo(() => {
    const list = jobs.length > 0 ? jobs : FAKE_JOBS
    if (selectedSources.length === 0) return list
    return list.filter((job) => {
      const sourceId = job.sourceName
        ? sourceIdToSourceName(job.sourceName)
        : null
      return sourceId && selectedSources.includes(sourceId)
    })
  }, [jobs, selectedSources])

  const displayTotal = selectedSources.length > 0 ? filteredJobs.length : total

  return (
    <div className="-mt-4 flex flex-col">
      <div className="bg-background sticky top-0 z-10 -mx-4 px-4 pt-4 pb-2">
        <JobSearchBar search={search} onSearchChange={setSearch} />
        <p className="text-muted-foreground mt-3 text-sm">
          {loading
            ? "Searching for jobs..."
            : `${displayTotal} job${displayTotal !== 1 ? "s" : ""} found`}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-3">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <JobCardSkeleton key={i} />
              ))}
            </div>
          ) : filteredJobs.length > 0 ? (
            <div className="space-y-3">
              {filteredJobs.map((job) => (
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
            selectedSources={selectedSources}
            onLocationChange={setLocation}
            onJobTypeChange={setJobType}
            onSelectedSourcesChange={setSelectedSources}
          />
        </div>
      </div>
    </div>
  )
}
