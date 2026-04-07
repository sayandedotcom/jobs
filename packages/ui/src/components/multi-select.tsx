"use client"

import * as React from "react"
import { CheckIcon, ChevronsUpDownIcon, XIcon } from "lucide-react"
import { Button } from "@workspace/ui/components/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@workspace/ui/components/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@workspace/ui/components/popover"
import { Badge } from "@workspace/ui/components/badge"
import { cn } from "@workspace/ui/lib/utils"

export interface MultiSelectOption {
  value: string
  label: string
  icon?: React.ReactNode
}

function MultiSelect({
  options,
  selected,
  onSelectedChange,
  placeholder = "Select...",
  className,
}: {
  options: MultiSelectOption[]
  selected: string[]
  onSelectedChange: (values: string[]) => void
  placeholder?: string
  className?: string
}) {
  const [open, setOpen] = React.useState(false)

  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onSelectedChange(selected.filter((s) => s !== value))
    } else {
      onSelectedChange([...selected, value])
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        render={
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className={cn("h-auto min-h-8 w-full justify-between", className)}
          >
            <div className="flex flex-wrap gap-1">
              {selected.length > 0 ? (
                options
                  .filter((o) => selected.includes(o.value))
                  .map((o) => (
                    <Badge
                      key={o.value}
                      variant="outline"
                      className="gap-1 pr-1 text-xs"
                    >
                      {o.icon}
                      {o.label}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleToggle(o.value)
                        }}
                        className="hover:bg-muted ml-0.5 cursor-pointer rounded-sm p-0.5"
                      >
                        <XIcon className="size-3" />
                      </button>
                    </Badge>
                  ))
              ) : (
                <span className="text-muted-foreground font-normal">
                  {placeholder}
                </span>
              )}
            </div>
            <ChevronsUpDownIcon className="ml-1 shrink-0 opacity-50" />
          </Button>
        }
      />
      <PopoverContent
        className="w-[var(--popover-anchor-width)] p-0"
        align="start"
      >
        <Command>
          <CommandInput placeholder="Search sources..." />
          <CommandList>
            <CommandEmpty>No source found.</CommandEmpty>
            <CommandGroup>
              {options.map((option) => {
                const isSelected = selected.includes(option.value)
                return (
                  <CommandItem
                    key={option.value}
                    value={option.value}
                    onSelect={() => handleToggle(option.value)}
                    data-checked={isSelected}
                  >
                    <div
                      className={cn(
                        "flex size-4 shrink-0 items-center justify-center rounded-sm border",
                        isSelected
                          ? "bg-primary border-primary text-primary-foreground"
                          : "border-input"
                      )}
                    >
                      {isSelected && <CheckIcon className="size-3" />}
                    </div>
                    {option.icon}
                    <span>{option.label}</span>
                  </CommandItem>
                )
              })}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}

export { MultiSelect }
