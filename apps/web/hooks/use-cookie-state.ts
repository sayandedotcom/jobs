"use client"

import * as React from "react"

function getCookie(name: string): string | undefined {
  const match = document.cookie
    .split("; ")
    .find((c) => c.startsWith(`${name}=`))
  return match
    ? decodeURIComponent(match.split("=").slice(1).join("="))
    : undefined
}

function setCookie(name: string, value: string, days = 365) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
}

export function useCookieState<T>(
  key: string,
  defaultValue: T,
  options?: {
    serialize?: (val: T) => string
    deserialize?: (raw: string) => T
  }
): [T, React.Dispatch<React.SetStateAction<T>>] {
  const serialize = options?.serialize ?? String
  const deserialize =
    options?.deserialize ?? ((raw: string) => raw as unknown as T)

  const [value, setValue] = React.useState<T>(defaultValue)

  React.useEffect(() => {
    const raw = getCookie(key)
    if (raw !== undefined) setValue(deserialize(raw))
  }, [key, deserialize])

  const stableSetValue = React.useCallback<
    React.Dispatch<React.SetStateAction<T>>
  >(
    (action) => {
      setValue((prev) => {
        const next =
          typeof action === "function" ? (action as (p: T) => T)(prev) : action
        setCookie(key, serialize(next))
        return next
      })
    },
    [key, serialize]
  )

  return [value, stableSetValue]
}
