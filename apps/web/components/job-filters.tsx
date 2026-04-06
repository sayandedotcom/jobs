"use client"

import * as React from "react"
import { Input } from "@workspace/ui/components/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@workspace/ui/components/select"
import {
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from "@workspace/ui/components/sidebar"
import { SearchIcon, MapPinIcon, BriefcaseIcon, XIcon } from "lucide-react"

interface JobFiltersProps {
  search: string
  location: string
  jobType: string
  onSearchChange: (value: string) => void
  onLocationChange: (value: string) => void
  onJobTypeChange: (value: string) => void
}

function JobSearchBar({
  search,
  onSearchChange,
}: {
  search: string
  onSearchChange: (value: string) => void
}) {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="relative">
        <SearchIcon className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
        <Input
          placeholder="Search jobs by title, company, or keyword..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-11 pl-10 text-base"
        />
      </div>
    </div>
  )
}

function JobFilterPanel({
  location,
  jobType,
  onLocationChange,
  onJobTypeChange,
}: Omit<JobFiltersProps, "search" | "onSearchChange">) {
  const hasFilters = location || (jobType && jobType !== "all")

  return (
    <aside className="bg-sidebar text-sidebar-foreground border-sidebar-border flex w-64 shrink-0 flex-col overflow-hidden rounded-lg border">
      <SidebarContent className="gap-0">
        <SidebarGroup>
          <SidebarGroupLabel>Filters</SidebarGroupLabel>
          <SidebarGroupContent className="space-y-4 px-2 pb-2">
            <div className="space-y-2">
              <label className="text-sidebar-foreground/70 flex items-center gap-2 text-xs font-medium">
                <MapPinIcon className="size-3.5" />
                Location
              </label>
              <Input
                placeholder="e.g. Remote, NYC"
                value={location}
                onChange={(e) => onLocationChange(e.target.value)}
                className="bg-background h-8 border-none shadow-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sidebar-foreground/70 flex items-center gap-2 text-xs font-medium">
                <BriefcaseIcon className="size-3.5" />
                Job Type
              </label>
              <Select
                value={jobType}
                onValueChange={(v) => onJobTypeChange(v ?? "all")}
              >
                <SelectTrigger className="bg-background h-8 border-none shadow-none">
                  <SelectValue placeholder="Job type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All types</SelectItem>
                  <SelectItem value="full-time">Full-time</SelectItem>
                  <SelectItem value="part-time">Part-time</SelectItem>
                  <SelectItem value="contract">Contract</SelectItem>
                  <SelectItem value="freelance">Freelance</SelectItem>
                  <SelectItem value="internship">Internship</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {hasFilters && (
              <button
                onClick={() => {
                  onLocationChange("")
                  onJobTypeChange("all")
                }}
                className="text-sidebar-foreground/70 hover:text-sidebar-foreground flex items-center gap-1.5 text-xs transition-colors"
              >
                <XIcon className="size-3" />
                Clear filters
              </button>
            )}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </aside>
  )
}

export { JobSearchBar, JobFilterPanel }
export type { JobFiltersProps }
