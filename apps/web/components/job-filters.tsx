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

interface JobFiltersProps {
  search: string
  location: string
  jobType: string
  onSearchChange: (value: string) => void
  onLocationChange: (value: string) => void
  onJobTypeChange: (value: string) => void
}

function JobFilters({
  search,
  location,
  jobType,
  onSearchChange,
  onLocationChange,
  onJobTypeChange,
}: JobFiltersProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <Input
        placeholder="Search jobs..."
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        className="sm:w-64"
      />
      <Input
        placeholder="Location..."
        value={location}
        onChange={(e) => onLocationChange(e.target.value)}
        className="sm:w-48"
      />
      <Select
        value={jobType}
        onValueChange={(v) => onJobTypeChange(v ?? "all")}
      >
        <SelectTrigger className="sm:w-44">
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
  )
}

export { JobFilters }
