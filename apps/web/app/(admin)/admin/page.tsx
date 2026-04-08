"use client"

import * as React from "react"
import { source } from "@/config/source"
import { Card, CardContent } from "@workspace/ui/components/card"
import { Button } from "@workspace/ui/components/button"
import { Badge } from "@workspace/ui/components/badge"

type ScanStatus = "idle" | "loading" | "success" | "error"

export default function AdminPage() {
  const [scanStatuses, setScanStatuses] = React.useState<
    Record<string, ScanStatus>
  >({})

  const triggerScan = async (sourceId: string) => {
    setScanStatuses((prev) => ({ ...prev, [sourceId]: "loading" }))
    try {
      const res = await fetch(
        `/api/scan/trigger?source=${encodeURIComponent(sourceId)}`,
        { method: "POST" }
      )
      if (!res.ok) throw new Error(await res.text())
      setScanStatuses((prev) => ({ ...prev, [sourceId]: "success" }))
    } catch {
      setScanStatuses((prev) => ({ ...prev, [sourceId]: "error" }))
    }
  }

  const triggerAll = async () => {
    for (const s of source) {
      await triggerScan(s.id)
    }
  }

  const anyLoading = Object.values(scanStatuses).some((s) => s === "loading")

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Admin — Integrations
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            {source.length} sources configured. Trigger scans manually.
          </p>
        </div>
        <Button onClick={triggerAll} disabled={anyLoading}>
          {anyLoading ? "Scanning…" : "Scan All"}
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {source.map((s) => {
          const status = scanStatuses[s.id] ?? "idle"
          return (
            <Card key={s.id}>
              <CardContent className="flex items-center gap-3">
                <img
                  src={s.src}
                  alt={s.name}
                  className="bg-muted size-10 shrink-0 rounded-lg object-contain p-1.5"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium">{s.name}</span>
                    {s.active ? (
                      <Badge variant="outline" className="text-xs">
                        Active
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="text-xs">
                        Inactive
                      </Badge>
                    )}
                  </div>
                  <p className="text-muted-foreground truncate text-xs">
                    {s.url}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => triggerScan(s.id)}
                  disabled={status === "loading"}
                >
                  {status === "loading"
                    ? "Scanning…"
                    : status === "success"
                      ? "Done"
                      : status === "error"
                        ? "Error"
                        : "Scan"}
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
