"use client"

import * as React from "react"
import { useSearchParams, usePathname, useRouter } from "next/navigation"

type ParamConfig = {
  key: string
  type: "array" | "string"
  defaultValue: string | string[]
}

const PARAMS: ParamConfig[] = [
  { key: "q", type: "string", defaultValue: "" },
  { key: "location", type: "string", defaultValue: "" },
  { key: "page", type: "string", defaultValue: "1" },
  { key: "sources", type: "array", defaultValue: [] },
  { key: "workModes", type: "array", defaultValue: [] },
  { key: "jobTypes", type: "array", defaultValue: [] },
  { key: "experience", type: "array", defaultValue: [] },
  { key: "dates", type: "array", defaultValue: [] },
]

function parseValue(config: ParamConfig, raw: string | null) {
  if (raw === null) return config.defaultValue
  if (config.type === "array") {
    return raw ? raw.split(",") : []
  }
  return raw
}

export function useQueryFilters() {
  const searchParams = useSearchParams()
  const pathname = usePathname()
  const router = useRouter()

  const values = React.useMemo(() => {
    const result: Record<string, string | string[]> = {}
    for (const config of PARAMS) {
      result[config.key] = parseValue(config, searchParams.get(config.key))
    }
    return result
  }, [searchParams])

  const updateParams = React.useCallback(
    (updates: Record<string, string | string[]>) => {
      const params = new URLSearchParams(searchParams.toString())
      for (const [key, value] of Object.entries(updates)) {
        if (
          value === "" ||
          (Array.isArray(value) && value.length === 0) ||
          value === "1"
        ) {
          params.delete(key)
        } else if (Array.isArray(value)) {
          params.set(key, value.join(","))
        } else {
          params.set(key, value)
        }
      }
      const qs = params.toString()
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
    },
    [searchParams, pathname, router]
  )

  const search = values["q"] as string
  const location = values["location"] as string
  const page = parseInt((values["page"] as string) || "1", 10)
  const selectedSources = values["sources"] as string[]
  const selectedWorkModes = values["workModes"] as string[]
  const selectedJobTypes = values["jobTypes"] as string[]
  const selectedExperience = values["experience"] as string[]
  const selectedDates = values["dates"] as string[]

  const setSearch = React.useCallback(
    (v: string) => updateParams({ q: v, page: "1" }),
    [updateParams]
  )
  const setLocation = React.useCallback(
    (v: string) => updateParams({ location: v, page: "1" }),
    [updateParams]
  )
  const setPage = React.useCallback(
    (v: number) => updateParams({ page: String(v) }),
    [updateParams]
  )
  const setSelectedSources = React.useCallback(
    (v: string[]) => updateParams({ sources: v, page: "1" }),
    [updateParams]
  )
  const setSelectedWorkModes = React.useCallback(
    (v: string[]) => updateParams({ workModes: v, page: "1" }),
    [updateParams]
  )
  const setSelectedJobTypes = React.useCallback(
    (v: string[]) => updateParams({ jobTypes: v, page: "1" }),
    [updateParams]
  )
  const setSelectedExperience = React.useCallback(
    (v: string[]) => updateParams({ experience: v, page: "1" }),
    [updateParams]
  )
  const setSelectedDates = React.useCallback(
    (v: string[]) => updateParams({ dates: v, page: "1" }),
    [updateParams]
  )
  const clearAll = React.useCallback(
    () =>
      updateParams({
        location: "",
        sources: [],
        workModes: [],
        jobTypes: [],
        experience: [],
        dates: [],
        page: "1",
      }),
    [updateParams]
  )

  return {
    search,
    location,
    page,
    selectedSources,
    selectedWorkModes,
    selectedJobTypes,
    selectedExperience,
    selectedDates,
    setSearch,
    setLocation,
    setPage,
    setSelectedSources,
    setSelectedWorkModes,
    setSelectedJobTypes,
    setSelectedExperience,
    setSelectedDates,
    clearAll,
  }
}
