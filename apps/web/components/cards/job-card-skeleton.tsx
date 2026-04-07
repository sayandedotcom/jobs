"use client"

import { Card, CardContent, CardHeader } from "@workspace/ui/components/card"
import { Skeleton } from "@workspace/ui/components/skeleton"

export function JobCardSkeleton() {
  return (
    <Card>
      <div className="flex items-center justify-between px-4 pb-2">
        <div className="flex items-center gap-2.5">
          <Skeleton className="size-5 rounded-sm" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="size-8 rounded-md" />
      </div>
      <CardHeader>
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-1/3" />
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
        <div className="flex items-center gap-4">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-3 w-20" />
        </div>
      </CardContent>
    </Card>
  )
}
