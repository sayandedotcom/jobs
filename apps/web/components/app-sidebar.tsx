"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@workspace/ui/components/sidebar"
import { NavUser } from "@/components/nav-user"
import { api } from "@/lib/api-client"
import {
  BotIcon,
  PlusCircleIcon,
  BriefcaseIcon,
  BookmarkIcon,
  BellIcon,
  LayoutDashboardIcon,
} from "lucide-react"

export function AppSidebar({
  user,
  ...props
}: {
  user: {
    name: string
    email: string
    avatar: string
  }
} & React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname()
  const [agentCount, setAgentCount] = React.useState(0)

  React.useEffect(() => {
    api.agents
      .list()
      .then((agents) => setAgentCount(agents.length))
      .catch(() => {})
  }, [])

  const navItems = [
    {
      title: "Dashboard",
      href: "/dashboard",
      icon: <LayoutDashboardIcon className="size-4" />,
    },
    {
      title: "Browse Jobs",
      href: "/jobs",
      icon: <BriefcaseIcon className="size-4" />,
    },
    {
      title: "Saved Jobs",
      href: "/saved",
      icon: <BookmarkIcon className="size-4" />,
    },
    {
      title: "Alerts",
      href: "/alerts",
      icon: <BellIcon className="size-4" />,
    },
  ]

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              tooltip="JobAgg Agents"
              render={<Link href="/dashboard" />}
            >
              <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                <BotIcon className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">JobAgg Agents</span>
                <span className="truncate text-xs">
                  {agentCount} agent{agentCount !== 1 ? "s" : ""} deployed
                </span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarMenu>
            {navItems.map((item) => (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton
                  isActive={pathname === item.href}
                  tooltip={item.title}
                  render={<Link href={item.href} />}
                >
                  {item.icon}
                  <span>{item.title}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel>AI Agents</SidebarGroupLabel>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip="Deploy New Agent"
                render={<Link href="/dashboard/agents/new" />}
              >
                <PlusCircleIcon className="size-4" />
                <span>Deploy New Agent</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
