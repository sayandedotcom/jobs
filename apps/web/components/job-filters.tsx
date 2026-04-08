"use client"

import * as React from "react"
import { Input } from "@workspace/ui/components/input"
import {
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from "@workspace/ui/components/sidebar"
import {
  MultiSelect,
  type MultiSelectOption,
} from "@workspace/ui/components/multi-select"
import {
  SearchIcon,
  MapPinIcon,
  BriefcaseIcon,
  GlobeIcon,
  FilterIcon,
  LinkIcon,
  CalendarIcon,
  TrendingUpIcon,
  XIcon,
} from "lucide-react"
import { Separator } from "@workspace/ui/components/separator"
import { source } from "@/config/source"

const SOURCE_ID_ALIASES: Record<string, string> = {
  hackernews: "ycombinator",
}

const SOURCE_OPTIONS: MultiSelectOption[] = source
  .filter((s) => s.active)
  .map((s) => ({
    value: s.id,
    label: s.name,
    icon: (
      <img
        src={s.src}
        alt={s.name}
        className="size-4 rounded-sm object-contain"
      />
    ),
  }))

const WORK_MODE_OPTIONS: MultiSelectOption[] = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "Onsite" },
]

const JOB_TYPE_OPTIONS: MultiSelectOption[] = [
  { value: "full-time", label: "Full-time" },
  { value: "part-time", label: "Part-time" },
  { value: "contract", label: "Contract" },
  { value: "freelance", label: "Freelance" },
  { value: "internship", label: "Internship" },
]

const EXPERIENCE_OPTIONS: MultiSelectOption[] = [
  { value: "junior", label: "Junior" },
  { value: "mid", label: "Mid" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead" },
  { value: "manager", label: "Manager" },
]

function generateDateOptions(): MultiSelectOption[] {
  const now = new Date()
  const options: MultiSelectOption[] = []
  for (let i = 0; i < 3; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const label = d.toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    })
    const value = d.toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    })
    options.push({ value, label })
  }
  return options
}

const DATE_OPTIONS = generateDateOptions()

function sourceIdToSourceName(sourceId: string): string {
  for (const [alias, id] of Object.entries(SOURCE_ID_ALIASES)) {
    if (id === sourceId) return alias
  }
  return sourceId
}

interface JobFiltersProps {
  search: string
  location: string
  selectedSources: string[]
  selectedWorkModes: string[]
  selectedJobTypes: string[]
  selectedExperience: string[]
  selectedDates: string[]
  onSearchChange: (value: string) => void
  onLocationChange: (value: string) => void
  onSelectedSourcesChange: (values: string[]) => void
  onSelectedWorkModesChange: (values: string[]) => void
  onSelectedJobTypesChange: (values: string[]) => void
  onSelectedExperienceChange: (values: string[]) => void
  onSelectedDatesChange: (values: string[]) => void
  onClearAll?: () => void
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
  selectedSources,
  selectedWorkModes,
  selectedJobTypes,
  selectedExperience,
  selectedDates,
  onLocationChange,
  onSelectedSourcesChange,
  onSelectedWorkModesChange,
  onSelectedJobTypesChange,
  onSelectedExperienceChange,
  onSelectedDatesChange,
  onClearAll,
}: Omit<JobFiltersProps, "search" | "onSearchChange">) {
  const hasFilters =
    location ||
    selectedSources.length > 0 ||
    selectedWorkModes.length > 0 ||
    selectedJobTypes.length > 0 ||
    selectedExperience.length > 0 ||
    selectedDates.length > 0

  return (
    <aside className="bg-sidebar text-sidebar-foreground border-sidebar-border flex w-full shrink-0 flex-col overflow-hidden rounded-lg border">
      <SidebarContent className="gap-0">
        <SidebarGroup>
          <SidebarGroupLabel className="flex items-center gap-2 text-sm font-semibold">
            <FilterIcon className="size-4" />
            Filters
          </SidebarGroupLabel>
          <Separator />
          <SidebarGroupContent className="space-y-4 px-2 py-2">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sidebar-foreground/70 flex items-center gap-2 text-xs font-medium">
                  <CalendarIcon className="size-3.5" />
                  Date Posted
                </label>
                {selectedDates.length > 0 && (
                  <button
                    onClick={() => onSelectedDatesChange([])}
                    className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
              <MultiSelect
                options={DATE_OPTIONS}
                selected={selectedDates}
                onSelectedChange={onSelectedDatesChange}
                placeholder="All dates"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sidebar-foreground/70 flex items-center gap-2 text-xs font-medium">
                  <LinkIcon className="size-3.5" />
                  Source
                </label>
                {selectedSources.length > 0 && (
                  <button
                    onClick={() => onSelectedSourcesChange([])}
                    className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
              <MultiSelect
                options={SOURCE_OPTIONS}
                selected={selectedSources}
                onSelectedChange={onSelectedSourcesChange}
                placeholder="All sources"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sidebar-foreground/70 flex items-center gap-2 text-xs font-medium">
                  <GlobeIcon className="size-3.5" />
                  Work Mode
                </label>
                {selectedWorkModes.length > 0 && (
                  <button
                    onClick={() => onSelectedWorkModesChange([])}
                    className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
              <MultiSelect
                options={WORK_MODE_OPTIONS}
                selected={selectedWorkModes}
                onSelectedChange={onSelectedWorkModesChange}
                placeholder="All modes"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sidebar-foreground/70 flex items-center gap-2 text-xs font-medium">
                  <BriefcaseIcon className="size-3.5" />
                  Job Type
                </label>
                {selectedJobTypes.length > 0 && (
                  <button
                    onClick={() => onSelectedJobTypesChange([])}
                    className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
              <MultiSelect
                options={JOB_TYPE_OPTIONS}
                selected={selectedJobTypes}
                onSelectedChange={onSelectedJobTypesChange}
                placeholder="All types"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sidebar-foreground/70 flex items-center gap-2 text-xs font-medium">
                  <TrendingUpIcon className="size-3.5" />
                  Experience Level
                </label>
                {selectedExperience.length > 0 && (
                  <button
                    onClick={() => onSelectedExperienceChange([])}
                    className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
              <MultiSelect
                options={EXPERIENCE_OPTIONS}
                selected={selectedExperience}
                onSelectedChange={onSelectedExperienceChange}
                placeholder="All levels"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sidebar-foreground/70 flex items-center gap-2 text-xs font-medium">
                <MapPinIcon className="size-3.5" />
                Location
              </label>
              <Input
                placeholder="e.g. NYC, Berlin"
                value={location}
                onChange={(e) => onLocationChange(e.target.value)}
                className="bg-background h-8 border-none shadow-none"
              />
            </div>

            {hasFilters && (
              <button
                onClick={() => onClearAll?.()}
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

export { JobSearchBar, JobFilterPanel, sourceIdToSourceName }
export type { JobFiltersProps }
