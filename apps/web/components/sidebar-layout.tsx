"use client"

import * as React from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { SidebarInset, SidebarProvider } from "@workspace/ui/components/sidebar"
import { Toaster } from "@workspace/ui/components/sonner"

export function SidebarLayout({
  user,
  children,
}: {
  user: {
    name: string
    email: string
    avatar: string
  }
  children: React.ReactNode
}) {
  return (
    <SidebarProvider
      style={{ "--sidebar-width": "18rem" } as React.CSSProperties}
    >
      <AppSidebar user={user} />
      <SidebarInset className="h-svh overflow-y-auto">
        <div className="flex flex-col gap-4 px-4 pt-4 pb-4">{children}</div>
      </SidebarInset>
      <Toaster position="bottom-right" />
    </SidebarProvider>
  )
}
