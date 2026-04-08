"use client"

import * as React from "react"
import { Input } from "@workspace/ui/components/input"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  useSidebar,
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
  PanelRightIcon,
} from "lucide-react"
import { source } from "@/config/source"
import { Button } from "@workspace/ui/components/button"

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
  const [draft, setDraft] = React.useState(search)
  const committedRef = React.useRef(search)

  if (search !== committedRef.current) {
    committedRef.current = search
    if (draft !== search) setDraft(search)
  }

  const submit = React.useCallback(() => {
    if (draft !== committedRef.current) {
      committedRef.current = draft
      onSearchChange(draft)
    }
  }, [draft, onSearchChange])

  return (
    <div className="flex flex-1">
      <div className="relative flex-1">
        <SearchIcon className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2" />
        <Input
          placeholder="Search jobs by title, company, or keyword..."
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value)
            if (e.target.value === "" && committedRef.current !== "") {
              committedRef.current = ""
              onSearchChange("")
            }
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit()
          }}
          className="h-11 rounded-r-none pl-10 text-base"
        />
      </div>
      <Button
        variant="default"
        className="h-11 cursor-pointer rounded-l-none px-4 active:translate-y-0"
        onClick={submit}
      >
        <SearchIcon className="size-4" />
      </Button>
    </div>
  )
}

function FilterSidebarProvider({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider
      style={{ "--sidebar-width": "20rem" } as React.CSSProperties}
    >
      {children}
    </SidebarProvider>
  )
}

function FilterSidebarTriggerButton() {
  const { toggleSidebar } = useSidebar()
  return (
    <Button
      data-sidebar="trigger"
      variant="ghost"
      size="icon-sm"
      className="shrink-0 cursor-pointer group-data-[collapsible=icon]:hidden"
      onClick={toggleSidebar}
    >
      <PanelRightIcon />
    </Button>
  )
}

function FilterSidebarCollapsedTrigger() {
  const { toggleSidebar } = useSidebar()
  return (
    <Button
      data-sidebar="trigger"
      variant="ghost"
      size="icon-sm"
      className="invisible col-start-1 row-start-1 cursor-pointer group-hover/icon:visible"
      onClick={toggleSidebar}
    >
      <PanelRightIcon />
    </Button>
  )
}

function FilterSidebarTrigger() {
  const { toggleSidebar } = useSidebar()
  return (
    <Button
      variant="outline"
      size="icon"
      onClick={toggleSidebar}
      className="h-11 w-11 shrink-0"
    >
      <FilterIcon className="size-4" />
    </Button>
  )
}

function FilterSidebar({
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
    <Sidebar side="right" variant="sidebar" collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <div className="flex items-center gap-2">
              <SidebarMenuButton
                size="lg"
                tooltip="Filters"
                className="flex-1 group-data-[collapsible=icon]:hidden"
              >
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <FilterIcon className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">Filters</span>
                </div>
              </SidebarMenuButton>
              <div className="group/icon relative hidden size-8 place-items-center group-data-[collapsible=icon]:grid">
                <div className="bg-sidebar-primary text-sidebar-primary-foreground col-start-1 row-start-1 flex size-8 items-center justify-center rounded-lg group-hover/icon:invisible">
                  <FilterIcon className="size-4" />
                </div>
                <FilterSidebarCollapsedTrigger />
              </div>
              <FilterSidebarTriggerButton />
            </div>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton tooltip="Filter by Date Posted">
                <CalendarIcon className="size-4" />
                <span>Date Posted</span>
              </SidebarMenuButton>
              <div className="group-data-[collapsible=icon]:hidden">
                <div className="flex items-center justify-between px-2 pb-1">
                  {selectedDates.length > 0 && (
                    <button
                      onClick={() => onSelectedDatesChange([])}
                      className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                <div className="px-2 pb-3">
                  <MultiSelect
                    options={DATE_OPTIONS}
                    selected={selectedDates}
                    onSelectedChange={onSelectedDatesChange}
                    placeholder="All dates"
                  />
                </div>
              </div>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton tooltip="Filter by Source">
                <LinkIcon className="size-4" />
                <span>Source</span>
              </SidebarMenuButton>
              <div className="group-data-[collapsible=icon]:hidden">
                <div className="flex items-center justify-between px-2 pb-1">
                  {selectedSources.length > 0 && (
                    <button
                      onClick={() => onSelectedSourcesChange([])}
                      className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                <div className="px-2 pb-3">
                  <MultiSelect
                    options={SOURCE_OPTIONS}
                    selected={selectedSources}
                    onSelectedChange={onSelectedSourcesChange}
                    placeholder="All sources"
                  />
                </div>
              </div>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton tooltip="Filter by Work Mode">
                <GlobeIcon className="size-4" />
                <span>Work Mode</span>
              </SidebarMenuButton>
              <div className="group-data-[collapsible=icon]:hidden">
                <div className="flex items-center justify-between px-2 pb-1">
                  {selectedWorkModes.length > 0 && (
                    <button
                      onClick={() => onSelectedWorkModesChange([])}
                      className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                <div className="px-2 pb-3">
                  <MultiSelect
                    options={WORK_MODE_OPTIONS}
                    selected={selectedWorkModes}
                    onSelectedChange={onSelectedWorkModesChange}
                    placeholder="All modes"
                  />
                </div>
              </div>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton tooltip="Filter by Job Type">
                <BriefcaseIcon className="size-4" />
                <span>Job Type</span>
              </SidebarMenuButton>
              <div className="group-data-[collapsible=icon]:hidden">
                <div className="flex items-center justify-between px-2 pb-1">
                  {selectedJobTypes.length > 0 && (
                    <button
                      onClick={() => onSelectedJobTypesChange([])}
                      className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                <div className="px-2 pb-3">
                  <MultiSelect
                    options={JOB_TYPE_OPTIONS}
                    selected={selectedJobTypes}
                    onSelectedChange={onSelectedJobTypesChange}
                    placeholder="All types"
                  />
                </div>
              </div>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton tooltip="Filter by Experience">
                <TrendingUpIcon className="size-4" />
                <span>Experience Level</span>
              </SidebarMenuButton>
              <div className="group-data-[collapsible=icon]:hidden">
                <div className="flex items-center justify-between px-2 pb-1">
                  {selectedExperience.length > 0 && (
                    <button
                      onClick={() => onSelectedExperienceChange([])}
                      className="text-sidebar-foreground/70 hover:text-sidebar-foreground cursor-pointer text-xs transition-colors"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                <div className="px-2 pb-3">
                  <MultiSelect
                    options={EXPERIENCE_OPTIONS}
                    selected={selectedExperience}
                    onSelectedChange={onSelectedExperienceChange}
                    placeholder="All levels"
                  />
                </div>
              </div>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton tooltip="Filter by Location">
                <MapPinIcon className="size-4" />
                <span>Location</span>
              </SidebarMenuButton>
              <div className="px-2 pb-3 group-data-[collapsible=icon]:hidden">
                <Input
                  placeholder="e.g. NYC, Berlin"
                  value={location}
                  onChange={(e) => onLocationChange(e.target.value)}
                  className="bg-background h-8 border-none shadow-none"
                />
              </div>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      {hasFilters && (
        <SidebarFooter className="border-t px-4 py-3">
          <button
            onClick={() => onClearAll?.()}
            className="text-sidebar-foreground/70 hover:text-sidebar-foreground flex items-center gap-1.5 text-xs transition-colors"
          >
            <XIcon className="size-3" />
            Clear filters
          </button>
        </SidebarFooter>
      )}
      <SidebarRail />
    </Sidebar>
  )
}

export {
  JobSearchBar,
  FilterSidebarProvider,
  FilterSidebar,
  FilterSidebarTrigger,
  sourceIdToSourceName,
}
export type { JobFiltersProps }
