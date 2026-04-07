"use client"

import * as React from "react"
import { QueryProvider } from "@/components/query-provider"

function Providers({ children }: { children: React.ReactNode }) {
  return <QueryProvider>{children}</QueryProvider>
}

export { Providers }
