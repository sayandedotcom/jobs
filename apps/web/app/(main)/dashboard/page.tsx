"use client"

import * as React from "react"
import Link from "next/link"

import { AppSidebar } from "@/components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@workspace/ui/components/breadcrumb"
import { Button } from "@workspace/ui/components/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { Badge } from "@workspace/ui/components/badge"
import { Separator } from "@workspace/ui/components/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@workspace/ui/components/sidebar"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { api, type Agent } from "@/lib/api-client"
import { useSession } from "@/lib/auth-client"
import {
  BotIcon,
  PlusCircleIcon,
  PlayCircleIcon,
  PauseIcon,
  EyeIcon,
  ClockIcon,
  ExternalLinkIcon,
} from "lucide-react"

export default function DashboardPage() {
  const { data: session } = useSession()
  const [agents, setAgents] = React.useState<Agent[]>([])
  const [loading, setLoading] = React.useState(true)

  const userId = session?.user?.id ?? ""

  React.useEffect(() => {
    if (!userId) return
    setLoading(true)
    api.agents
      .list()
      .then(setAgents)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [userId])

  const user = {
    name: session?.user?.name ?? "User",
    email: session?.user?.email ?? "",
    avatar: session?.user?.image ?? "",
  }

  const activeAgents = agents.filter((a) => a.isActive).length
  const totalResults = agents.reduce((sum, a) => sum + a.totalResults, 0)
  const unviewedResults = agents.reduce((sum, a) => sum + a.unviewedResults, 0)

  return (
    <SidebarProvider>
      <AppSidebar user={user} agentCount={agents.length} />
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
                  <BreadcrumbPage>Dashboard</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                AI Agent Dashboard
              </h1>
              <p className="text-muted-foreground text-sm">
                Deploy and manage your AI job-hunting agents
              </p>
            </div>
            <Button render={<Link href="/dashboard/agents/new" />}>
              <PlusCircleIcon className="mr-2 size-4" />
              Deploy New Agent
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Active Agents
                </CardTitle>
                <BotIcon className="text-muted-foreground size-4" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {activeAgents}
                  <span className="text-muted-foreground text-sm font-normal">
                    {" "}
                    / {agents.length} total
                  </span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Jobs Found
                </CardTitle>
                <EyeIcon className="text-muted-foreground size-4" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalResults}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Unviewed Results
                </CardTitle>
                <ExternalLinkIcon className="text-muted-foreground size-4" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{unviewedResults}</div>
              </CardContent>
            </Card>
          </div>

          <Separator />

          <div>
            <h2 className="mb-4 text-lg font-semibold">Your Agents</h2>
            {loading ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardHeader>
                      <Skeleton className="h-5 w-32" />
                      <Skeleton className="h-4 w-24" />
                    </CardHeader>
                    <CardContent>
                      <Skeleton className="h-16 w-full" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : agents.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <BotIcon className="text-muted-foreground mb-4 size-12" />
                  <h3 className="mb-1 text-lg font-medium">
                    No agents deployed yet
                  </h3>
                  <p className="text-muted-foreground mb-4 text-sm">
                    Deploy your first AI agent to start scanning for jobs
                    automatically
                  </p>
                  <Button render={<Link href="/dashboard/agents/new" />}>
                    <PlusCircleIcon className="mr-2 size-4" />
                    Deploy Your First Agent
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {agents.map((agent) => (
                  <AgentCard key={agent.id} agent={agent} />
                ))}
              </div>
            )}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

function AgentCard({ agent }: { agent: Agent }) {
  const [toggling, setToggling] = React.useState(false)

  const handleToggle = React.useCallback(async () => {
    setToggling(true)
    try {
      await api.agents.update(agent.id, {
        isActive: !agent.isActive,
      })
      window.location.reload()
    } catch (err) {
      console.error(err)
    } finally {
      setToggling(false)
    }
  }, [agent.id, agent.isActive])

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{agent.name}</CardTitle>
            <CardDescription>{agent.jobTitle}</CardDescription>
          </div>
          <Badge variant={agent.isActive ? "default" : "secondary"}>
            {agent.isActive ? "Active" : "Paused"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2 text-sm">
          {agent.skills.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {agent.skills.slice(0, 4).map((skill) => (
                <Badge key={skill} variant="outline" className="text-xs">
                  {skill}
                </Badge>
              ))}
              {agent.skills.length > 4 && (
                <Badge variant="outline" className="text-xs">
                  +{agent.skills.length - 4}
                </Badge>
              )}
            </div>
          )}
          <div className="text-muted-foreground flex items-center gap-1 text-xs">
            <ClockIcon className="size-3" />
            Every {agent.scanIntervalMinutes} min
          </div>
          <div className="flex items-center justify-between text-xs">
            <span>
              {agent.totalResults} results ({agent.unviewedResults} new)
            </span>
            {agent.latestRunStatus && (
              <Badge
                variant={
                  agent.latestRunStatus === "completed"
                    ? "default"
                    : agent.latestRunStatus === "failed"
                      ? "destructive"
                      : "secondary"
                }
                className="text-xs"
              >
                {agent.latestRunStatus}
              </Badge>
            )}
          </div>
        </div>
        <Separator className="my-3" />
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            render={<Link href={`/dashboard/agents/${agent.id}`} />}
            className="flex-1"
          >
            <EyeIcon className="mr-1 size-3" />
            View
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggle}
            disabled={toggling}
          >
            {agent.isActive ? (
              <PauseIcon className="size-3" />
            ) : (
              <PlayCircleIcon className="size-3" />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
