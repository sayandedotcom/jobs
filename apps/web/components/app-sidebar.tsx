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
  SidebarTrigger,
} from "@workspace/ui/components/sidebar"
import { NavUser } from "@/components/nav-user"
import { api } from "@/lib/api-client"
import { siteConfig } from "@/lib/site-config"
import {
  BotIcon,
  PlusCircleIcon,
  BriefcaseIcon,
  BookmarkIcon,
  BellIcon,
  LayoutDashboardIcon,
  PuzzleIcon,
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
    {
      title: "Integrations",
      href: "/integrations",
      icon: <PuzzleIcon className="size-4" />,
    },
  ]

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <div className="flex items-center gap-2">
              <SidebarMenuButton
                size="lg"
                tooltip={siteConfig.name}
                render={<Link href="/dashboard" />}
                className="flex-1 group-data-[collapsible=icon]:hidden"
              >
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <BotIcon className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">
                    {siteConfig.name}
                  </span>
                  <span className="truncate text-xs">
                    {agentCount} agent{agentCount !== 1 ? "s" : ""} deployed
                  </span>
                </div>
              </SidebarMenuButton>
              <div className="group/icon relative hidden size-8 place-items-center group-data-[collapsible=icon]:grid">
                <Link
                  href="/dashboard"
                  className="bg-sidebar-primary text-sidebar-primary-foreground col-start-1 row-start-1 flex size-8 items-center justify-center rounded-lg group-hover/icon:invisible"
                >
                  <BotIcon className="size-4" />
                </Link>
                <SidebarTrigger className="invisible col-start-1 row-start-1 cursor-pointer group-hover/icon:visible" />
              </div>
              <SidebarTrigger className="shrink-0 cursor-pointer group-data-[collapsible=icon]:hidden" />
            </div>
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
