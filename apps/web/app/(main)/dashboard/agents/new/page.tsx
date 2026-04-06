"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@workspace/ui/components/breadcrumb"
import { Button } from "@workspace/ui/components/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { Input } from "@workspace/ui/components/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@workspace/ui/components/select"
import { Separator } from "@workspace/ui/components/separator"
import { api } from "@/lib/api-client"
import { useSession } from "@/lib/auth-client"
import { ArrowLeftIcon, Loader2Icon } from "lucide-react"

export default function NewAgentPage() {
  const { data: session } = useSession()
  const router = useRouter()
  const [submitting, setSubmitting] = React.useState(false)
  const [error, setError] = React.useState("")

  const [form, setForm] = React.useState({
    name: "",
    jobTitle: "",
    skillsText: "",
    location: "",
    openToRelocate: false,
    experienceLevel: "",
    salaryMin: "",
    salaryMax: "",
    jobType: "",
    sources: ["reddit"],
    scanIntervalMinutes: 1440,
  })

  const userId = session?.user?.id ?? ""

  const handleSubmit = React.useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      if (!userId) return

      setSubmitting(true)
      setError("")

      try {
        const skills = form.skillsText
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)

        const agent = await api.agents.create({
          name: form.name,
          jobTitle: form.jobTitle,
          skills,
          location: form.location || undefined,
          openToRelocate: form.openToRelocate,
          experienceLevel: form.experienceLevel || undefined,
          salaryMin: form.salaryMin ? parseInt(form.salaryMin) : undefined,
          salaryMax: form.salaryMax ? parseInt(form.salaryMax) : undefined,
          jobType: form.jobType || undefined,
          sources: form.sources,
          scanIntervalMinutes: form.scanIntervalMinutes,
        })
        router.push(`/dashboard/agents/${agent.id}`)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to deploy agent")
      } finally {
        setSubmitting(false)
      }
    },
    [form, userId, router]
  )

  return (
    <>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink render={<Link href="/dashboard" />}>
              Dashboard
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Deploy New Agent</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon-sm"
          render={<Link href="/dashboard" />}
        >
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">Deploy New Agent</h1>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Agent Profile</CardTitle>
              <CardDescription>
                Define what kind of jobs this agent should search for
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Agent Name *</label>
                <Input
                  placeholder="e.g., Frontend Job Hunter"
                  value={form.name}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, name: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Target Job Title *
                </label>
                <Input
                  placeholder="e.g., Senior React Developer"
                  value={form.jobTitle}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, jobTitle: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Skills</label>
                <Input
                  placeholder="e.g., React, TypeScript, Node.js (comma-separated)"
                  value={form.skillsText}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, skillsText: e.target.value }))
                  }
                />
                <p className="text-muted-foreground text-xs">
                  Comma-separated list of skills to match against
                </p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Experience Level</label>
                <Select
                  value={form.experienceLevel}
                  onValueChange={(v) =>
                    setForm((f) => ({
                      ...f,
                      experienceLevel: v === "__none" ? "" : (v ?? ""),
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Any level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none">Any level</SelectItem>
                    <SelectItem value="intern">Intern</SelectItem>
                    <SelectItem value="junior">Junior</SelectItem>
                    <SelectItem value="mid">Mid-level</SelectItem>
                    <SelectItem value="senior">Senior</SelectItem>
                    <SelectItem value="lead">Lead</SelectItem>
                    <SelectItem value="staff">Staff</SelectItem>
                    <SelectItem value="principal">Principal</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Preferences</CardTitle>
              <CardDescription>
                Location, salary, and scanning preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Location</label>
                <Input
                  placeholder="e.g., Remote, San Francisco, CA"
                  value={form.location}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, location: e.target.value }))
                  }
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="relocate"
                  checked={form.openToRelocate}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      openToRelocate: e.target.checked,
                    }))
                  }
                  className="size-4 rounded border"
                />
                <label htmlFor="relocate" className="text-sm font-medium">
                  Open to relocate
                </label>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Min Salary ($)</label>
                  <Input
                    type="number"
                    placeholder="e.g., 80000"
                    value={form.salaryMin}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, salaryMin: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Salary ($)</label>
                  <Input
                    type="number"
                    placeholder="e.g., 150000"
                    value={form.salaryMax}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, salaryMax: e.target.value }))
                    }
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Job Type</label>
                <Select
                  value={form.jobType}
                  onValueChange={(v) =>
                    setForm((f) => ({
                      ...f,
                      jobType: v === "__none" ? "" : (v ?? ""),
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Any type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none">Any type</SelectItem>
                    <SelectItem value="full-time">Full-time</SelectItem>
                    <SelectItem value="part-time">Part-time</SelectItem>
                    <SelectItem value="contract">Contract</SelectItem>
                    <SelectItem value="freelance">Freelance</SelectItem>
                    <SelectItem value="internship">Internship</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Separator />
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Scan Interval (minutes) *
                </label>
                <Input
                  type="number"
                  min={30}
                  value={form.scanIntervalMinutes}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      scanIntervalMinutes: parseInt(e.target.value) || 1440,
                    }))
                  }
                  required
                />
                <p className="text-muted-foreground text-xs">
                  Minimum 30 minutes. Controls how often the agent scans for new
                  jobs.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {error && <p className="text-destructive mt-4 text-sm">{error}</p>}

        <div className="mt-6 flex gap-3">
          <Button type="submit" disabled={submitting}>
            {submitting ? (
              <>
                <Loader2Icon className="mr-2 size-4 animate-spin" />
                Deploying...
              </>
            ) : (
              "Deploy Agent"
            )}
          </Button>
          <Button
            variant="outline"
            type="button"
            render={<Link href="/dashboard" />}
          >
            Cancel
          </Button>
        </div>
      </form>
    </>
  )
}
