"use client"

import * as React from "react"
import { Input } from "@workspace/ui/components/input"
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
import { source } from "@/config/source"
import { sourceIdToSourceName } from "@/lib/source-mapping"
import { Button } from "@workspace/ui/components/button"
import { Separator } from "@workspace/ui/components/separator"

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
  onApply?: (filters: {
    location: string
    sources: string[]
    workModes: string[]
    jobTypes: string[]
    experience: string[]
    dates: string[]
  }) => void
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

function FilterItem({
  icon: Icon,
  label,
  selected,
  onSelectedChange,
  children,
}: {
  icon: React.ElementType
  label: string
  selected: string[]
  onSelectedChange: (values: string[]) => void
  children?: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Icon className="size-4" />
          <span>{label}</span>
        </div>
        {selected.length > 0 && (
          <button
            onClick={() => onSelectedChange([])}
            className="text-muted-foreground hover:text-foreground cursor-pointer text-xs transition-colors"
          >
            Clear all
          </button>
        )}
      </div>
      {children}
    </div>
  )
}

function arraysEqual(a: string[], b: string[]) {
  if (a.length !== b.length) return false
  return a.every((v, i) => v === b[i])
}

function FilterPanel({
  location,
  selectedSources,
  selectedWorkModes,
  selectedJobTypes,
  selectedExperience,
  selectedDates,
  onClearAll,
  onApply,
}: Omit<
  JobFiltersProps,
  | "search"
  | "onSearchChange"
  | "onLocationChange"
  | "onSelectedSourcesChange"
  | "onSelectedWorkModesChange"
  | "onSelectedJobTypesChange"
  | "onSelectedExperienceChange"
  | "onSelectedDatesChange"
>) {
  const [draftLocation, setDraftLocation] = React.useState(location)
  const [draftSources, setDraftSources] = React.useState(selectedSources)
  const [draftWorkModes, setDraftWorkModes] = React.useState(selectedWorkModes)
  const [draftJobTypes, setDraftJobTypes] = React.useState(selectedJobTypes)
  const [draftExperience, setDraftExperience] =
    React.useState(selectedExperience)
  const [draftDates, setDraftDates] = React.useState(selectedDates)

  const committedRef = React.useRef({
    location,
    selectedSources,
    selectedWorkModes,
    selectedJobTypes,
    selectedExperience,
    selectedDates,
  })

  if (
    location !== committedRef.current.location ||
    !arraysEqual(selectedSources, committedRef.current.selectedSources) ||
    !arraysEqual(selectedWorkModes, committedRef.current.selectedWorkModes) ||
    !arraysEqual(selectedJobTypes, committedRef.current.selectedJobTypes) ||
    !arraysEqual(selectedExperience, committedRef.current.selectedExperience) ||
    !arraysEqual(selectedDates, committedRef.current.selectedDates)
  ) {
    committedRef.current = {
      location,
      selectedSources,
      selectedWorkModes,
      selectedJobTypes,
      selectedExperience,
      selectedDates,
    }
    setDraftLocation(location)
    setDraftSources(selectedSources)
    setDraftWorkModes(selectedWorkModes)
    setDraftJobTypes(selectedJobTypes)
    setDraftExperience(selectedExperience)
    setDraftDates(selectedDates)
  }

  const isDirty =
    draftLocation !== location ||
    !arraysEqual(draftSources, selectedSources) ||
    !arraysEqual(draftWorkModes, selectedWorkModes) ||
    !arraysEqual(draftJobTypes, selectedJobTypes) ||
    !arraysEqual(draftExperience, selectedExperience) ||
    !arraysEqual(draftDates, selectedDates)

  const hasAnyFilter =
    draftLocation ||
    draftSources.length > 0 ||
    draftWorkModes.length > 0 ||
    draftJobTypes.length > 0 ||
    draftExperience.length > 0 ||
    draftDates.length > 0

  const apply = React.useCallback(() => {
    onApply?.({
      location: draftLocation,
      sources: draftSources,
      workModes: draftWorkModes,
      jobTypes: draftJobTypes,
      experience: draftExperience,
      dates: draftDates,
    })
  }, [
    draftLocation,
    draftSources,
    draftWorkModes,
    draftJobTypes,
    draftExperience,
    draftDates,
    onApply,
  ])

  const clearDraftAndApply = React.useCallback(() => {
    setDraftLocation("")
    setDraftSources([])
    setDraftWorkModes([])
    setDraftJobTypes([])
    setDraftExperience([])
    setDraftDates([])
    onClearAll?.()
  }, [onClearAll])

  return (
    <aside className="bg-card sticky top-0 flex h-svh w-72 shrink-0 flex-col overflow-y-auto border-l p-4">
      <div className="mb-4 flex items-center gap-2">
        <div className="bg-primary text-primary-foreground flex size-8 items-center justify-center rounded-lg">
          <FilterIcon className="size-4" />
        </div>
        <span className="text-sm font-semibold">Filters</span>
      </div>
      <Separator />

      <div className="my-4 flex flex-col gap-4">
        <FilterItem
          icon={CalendarIcon}
          label="Date Posted"
          selected={draftDates}
          onSelectedChange={setDraftDates}
        >
          <MultiSelect
            options={DATE_OPTIONS}
            selected={draftDates}
            onSelectedChange={setDraftDates}
            placeholder="All dates"
          />
        </FilterItem>

        <FilterItem
          icon={LinkIcon}
          label="Source"
          selected={draftSources}
          onSelectedChange={setDraftSources}
        >
          <MultiSelect
            options={SOURCE_OPTIONS}
            selected={draftSources}
            onSelectedChange={setDraftSources}
            placeholder="All sources"
          />
        </FilterItem>

        <FilterItem
          icon={GlobeIcon}
          label="Work Mode"
          selected={draftWorkModes}
          onSelectedChange={setDraftWorkModes}
        >
          <MultiSelect
            options={WORK_MODE_OPTIONS}
            selected={draftWorkModes}
            onSelectedChange={setDraftWorkModes}
            placeholder="All modes"
          />
        </FilterItem>

        <FilterItem
          icon={BriefcaseIcon}
          label="Job Type"
          selected={draftJobTypes}
          onSelectedChange={setDraftJobTypes}
        >
          <MultiSelect
            options={JOB_TYPE_OPTIONS}
            selected={draftJobTypes}
            onSelectedChange={setDraftJobTypes}
            placeholder="All types"
          />
        </FilterItem>

        <FilterItem
          icon={TrendingUpIcon}
          label="Experience Level"
          selected={draftExperience}
          onSelectedChange={setDraftExperience}
        >
          <MultiSelect
            options={EXPERIENCE_OPTIONS}
            selected={draftExperience}
            onSelectedChange={setDraftExperience}
            placeholder="All levels"
          />
        </FilterItem>

        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-sm font-medium">
            <MapPinIcon className="size-4" />
            <span>Location</span>
          </div>
          <Input
            placeholder="e.g. NYC, Berlin"
            value={draftLocation}
            onChange={(e) => setDraftLocation(e.target.value)}
          />
        </div>
      </div>

      <div className="mt-auto border-t pt-3">
        {hasAnyFilter && (
          <button
            onClick={clearDraftAndApply}
            className="text-muted-foreground hover:text-foreground mb-2 flex w-full items-center justify-center gap-1.5 text-xs transition-colors"
          >
            <XIcon className="size-3" />
            Clear filters
          </button>
        )}
        <Button
          className="w-full cursor-pointer"
          disabled={!isDirty}
          onClick={apply}
        >
          Apply filters
        </Button>
      </div>
    </aside>
  )
}

export { JobSearchBar, FilterPanel, sourceIdToSourceName }
export type { JobFiltersProps }
