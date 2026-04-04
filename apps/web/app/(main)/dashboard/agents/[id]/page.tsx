"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

import { AppSidebar } from "@/components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@workspace/ui/components/breadcrumb"
import { Badge } from "@workspace/ui/components/badge"
import { Button } from "@workspace/ui/components/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { Separator } from "@workspace/ui/components/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@workspace/ui/components/sidebar"
import { Skeleton } from "@workspace/ui/components/skeleton"
import {
  api,
  type Agent,
  type AgentResult,
  type AgentRun,
} from "@/lib/api-client"
import { useSession } from "@/lib/auth-client"
import {
  ArrowLeftIcon,
  BotIcon,
  ClockIcon,
  ExternalLinkIcon,
  Loader2Icon,
  MapPinIcon,
  PauseIcon,
  PlayCircleIcon,
  RefreshCwIcon,
  Trash2Icon,
  ZapIcon,
} from "lucide-react"

export default function AgentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = React.use(params)
  const { data: session } = useSession()
  const router = useRouter()
  const [agent, setAgent] = React.useState<Agent | null>(null)
  const [results, setResults] = React.useState<AgentResult[]>([])
  const [runs, setRuns] = React.useState<AgentRun[]>([])
  const [loading, setLoading] = React.useState(true)
  const [activeTab, setActiveTab] = React.useState<"results" | "runs">(
    "results"
  )
  const [triggering, setTriggering] = React.useState(false)
  const [toggling, setToggling] = React.useState(false)

  const userId = session?.user?.id ?? ""

  const user = {
    name: session?.user?.name ?? "User",
    email: session?.user?.email ?? "",
    avatar: session?.user?.image ?? "",
  }

  React.useEffect(() => {
    if (!userId || !id) return
    setLoading(true)
    Promise.all([
      api.agents.get(id, userId),
      api.agents.results(id, userId),
      api.agents.runs(id, userId),
    ])
      .then(([agentData, resultsData, runsData]) => {
        setAgent(agentData)
        setResults(resultsData)
        setRuns(runsData)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [userId, id])

  const handleToggle = React.useCallback(async () => {
    if (!agent) return
    setToggling(true)
    try {
      await api.agents.update(agent.id, userId, {
        isActive: !agent.isActive,
      })
      setAgent((a) => (a ? { ...a, isActive: !a.isActive } : a))
    } catch (err) {
      console.error(err)
    } finally {
      setToggling(false)
    }
  }, [agent, userId])

  const handleTrigger = React.useCallback(async () => {
    if (!agent) return
    setTriggering(true)
    try {
      const run = await api.agents.trigger(agent.id, userId)
      setRuns((prev) => [run, ...prev])
      setAgent((a) =>
        a
          ? {
              ...a,
              latestRunStatus: run.status,
            }
          : a
      )
    } catch (err) {
      console.error(err)
    } finally {
      setTriggering(false)
    }
  }, [agent, userId])

  const handleDelete = React.useCallback(async () => {
    if (!agent) return
    if (!confirm("Are you sure you want to delete this agent?")) return
    try {
      await api.agents.delete(agent.id, userId)
      router.push("/dashboard")
    } catch (err) {
      console.error(err)
    }
  }, [agent, userId, router])

  if (loading) {
    return (
      <SidebarProvider>
        <AppSidebar user={user} />
        <SidebarInset>
          <div className="p-4">
            <Skeleton className="mb-4 h-8 w-64" />
            <Skeleton className="mb-2 h-32 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        </SidebarInset>
      </SidebarProvider>
    )
  }

  if (!agent) {
    return (
      <SidebarProvider>
        <AppSidebar user={user} />
        <SidebarInset>
          <div className="p-4">
            <p className="text-destructive">Agent not found</p>
            <Button
              className="mt-4"
              variant="outline"
              render={<Link href="/dashboard" />}
            >
              Back to Dashboard
            </Button>
          </div>
        </SidebarInset>
      </SidebarProvider>
    )
  }

  return (
    <SidebarProvider>
      <AppSidebar user={user} />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator
              orientation="vertical"
              className="mr-2 data-vertical:h-4 data-vertical:self-auto"
            />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbLink render={<Link href="/dashboard" />}>
                    Dashboard
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage>{agent.name}</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon-sm"
                render={<Link href="/dashboard" />}
              >
                <ArrowLeftIcon className="size-4" />
              </Button>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold tracking-tight">
                    {agent.name}
                  </h1>
                  <Badge variant={agent.isActive ? "default" : "secondary"}>
                    {agent.isActive ? "Active" : "Paused"}
                  </Badge>
                </div>
                <p className="text-muted-foreground text-sm">
                  {agent.jobTitle}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleTrigger}
                disabled={triggering}
              >
                {triggering ? (
                  <Loader2Icon className="mr-1 size-3 animate-spin" />
                ) : (
                  <RefreshCwIcon className="mr-1 size-3" />
                )}
                Run Now
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleToggle}
                disabled={toggling}
              >
                {agent.isActive ? (
                  <PauseIcon className="mr-1 size-3" />
                ) : (
                  <PlayCircleIcon className="mr-1 size-3" />
                )}
                {agent.isActive ? "Pause" : "Resume"}
              </Button>
              <Button variant="destructive" size="sm" onClick={handleDelete}>
                <Trash2Icon className="mr-1 size-3" />
                Delete
              </Button>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Scan Interval</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-1 text-lg font-semibold">
                  <ClockIcon className="size-4" />
                  {agent.scanIntervalMinutes} min
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Results Found</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-semibold">
                  {agent.totalResults}
                  <span className="text-muted-foreground text-sm font-normal">
                    {" "}
                    ({agent.unviewedResults} new)
                  </span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Location</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-1 text-lg font-semibold">
                  <MapPinIcon className="size-4" />
                  {agent.location || "Any"}
                  {agent.openToRelocate && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      Willing to relocate
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Last Run</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-semibold">
                  {agent.lastRunAt
                    ? new Date(agent.lastRunAt).toLocaleDateString()
                    : "Never"}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Agent Profile</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Skills: </span>
                  {agent.skills.length > 0 ? (
                    <span className="inline-flex gap-1">
                      {agent.skills.map((s) => (
                        <Badge key={s} variant="outline" className="text-xs">
                          {s}
                        </Badge>
                      ))}
                    </span>
                  ) : (
                    "None"
                  )}
                </div>
                <div>
                  <span className="text-muted-foreground">Experience: </span>
                  {agent.experienceLevel || "Any"}
                </div>
                <div>
                  <span className="text-muted-foreground">Salary: </span>
                  {agent.salaryMin && agent.salaryMax
                    ? `$${agent.salaryMin.toLocaleString()} - $${agent.salaryMax.toLocaleString()}`
                    : "Any"}
                </div>
                <div>
                  <span className="text-muted-foreground">Type: </span>
                  {agent.jobType || "Any"}
                </div>
                <div>
                  <span className="text-muted-foreground">Sources: </span>
                  {agent.sources.join(", ")}
                </div>
              </div>
            </CardContent>
          </Card>

          <div>
            <div className="mb-4 flex gap-2">
              <Button
                variant={activeTab === "results" ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveTab("results")}
              >
                <ZapIcon className="mr-1 size-3" />
                Results ({results.length})
              </Button>
              <Button
                variant={activeTab === "runs" ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveTab("runs")}
              >
                <BotIcon className="mr-1 size-3" />
                Run History ({runs.length})
              </Button>
            </div>

            {activeTab === "results" && (
              <div className="space-y-3">
                {results.length === 0 ? (
                  <Card>
                    <CardContent className="py-8 text-center">
                      <p className="text-muted-foreground">
                        No results yet. The agent will find matching jobs on its
                        next scan.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  results.map((result) => (
                    <Card key={result.id}>
                      <CardContent className="flex items-start gap-4 py-4">
                        <div className="bg-primary/10 flex size-10 shrink-0 items-center justify-center rounded-full">
                          <span className="text-primary text-sm font-bold">
                            {Math.round(result.relevanceScore * 100)}%
                          </span>
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="font-medium">
                                {result.listing.title}
                              </h3>
                              <p className="text-muted-foreground text-sm">
                                {result.listing.company}
                                {result.listing.location &&
                                  ` - ${result.listing.location}`}
                              </p>
                            </div>
                            <div className="flex gap-2">
                              {result.listing.url && (
                                <Button
                                  variant="ghost"
                                  size="icon-xs"
                                  render={
                                    <a
                                      href={result.listing.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    />
                                  }
                                >
                                  <ExternalLinkIcon className="size-3" />
                                </Button>
                              )}
                              {result.listing.applyUrl && (
                                <Button
                                  size="xs"
                                  render={
                                    <a
                                      href={result.listing.applyUrl}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    />
                                  }
                                >
                                  Apply
                                </Button>
                              )}
                            </div>
                          </div>
                          {result.matchReason && (
                            <p className="text-muted-foreground mt-1 text-xs">
                              {result.matchReason}
                            </p>
                          )}
                          <p className="mt-1 line-clamp-2 text-xs">
                            {result.listing.description}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            )}

            {activeTab === "runs" && (
              <Card>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="p-3 text-left font-medium">Status</th>
                          <th className="p-3 text-left font-medium">
                            Posts Scanned
                          </th>
                          <th className="p-3 text-left font-medium">
                            Jobs Found
                          </th>
                          <th className="p-3 text-left font-medium">
                            New Jobs
                          </th>
                          <th className="p-3 text-left font-medium">Started</th>
                          <th className="p-3 text-left font-medium">
                            Duration
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {runs.length === 0 ? (
                          <tr>
                            <td
                              colSpan={6}
                              className="text-muted-foreground p-6 text-center"
                            >
                              No runs yet
                            </td>
                          </tr>
                        ) : (
                          runs.map((run) => (
                            <tr key={run.id} className="border-b last:border-0">
                              <td className="p-3">
                                <Badge
                                  variant={
                                    run.status === "completed"
                                      ? "default"
                                      : run.status === "failed"
                                        ? "destructive"
                                        : "secondary"
                                  }
                                  className="text-xs"
                                >
                                  {run.status}
                                </Badge>
                              </td>
                              <td className="p-3">{run.postsScanned}</td>
                              <td className="p-3">{run.jobsFound}</td>
                              <td className="p-3">{run.newJobs}</td>
                              <td className="text-muted-foreground p-3">
                                {new Date(run.startedAt).toLocaleString()}
                              </td>
                              <td className="text-muted-foreground p-3">
                                {run.finishedAt
                                  ? `${Math.round(
                                      (new Date(run.finishedAt).getTime() -
                                        new Date(run.startedAt).getTime()) /
                                        1000
                                    )}s`
                                  : "-"}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
