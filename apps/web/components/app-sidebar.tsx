"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@workspace/ui/components/sidebar"
import { NavUser } from "@/components/nav-user"
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
  agentCount = 0,
  ...props
}: {
  user: {
    name: string
    email: string
    avatar: string
  }
  agentCount?: number
} & React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname()

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
            <SidebarMenuButton size="lg" render={<Link href="/dashboard" />}>
              <div className="bg-primary text-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                <BotIcon className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">JobAgg Agents</span>
                <span className="text-muted-foreground truncate text-xs">
                  {agentCount} agent{agentCount !== 1 ? "s" : ""} deployed
                </span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <div className="px-4 py-2">
          <h4 className="text-muted-foreground mb-1 text-xs font-medium">
            Navigation
          </h4>
        </div>
        <SidebarMenu>
          {navItems.map((item) => (
            <SidebarMenuItem key={item.href}>
              <SidebarMenuButton
                isActive={pathname === item.href}
                render={<Link href={item.href} />}
              >
                {item.icon}
                <span>{item.title}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
        <div className="mt-4 px-4 py-2">
          <h4 className="text-muted-foreground mb-1 text-xs font-medium">
            AI Agents
          </h4>
        </div>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton render={<Link href="/dashboard/agents/new" />}>
              <PlusCircleIcon className="size-4" />
              <span>Deploy New Agent</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
