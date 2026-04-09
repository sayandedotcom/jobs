export const SOURCE_ID_ALIASES: Record<string, string> = {
  hackernews: "ycombinator",
}

export function sourceNameToSourceId(sourceName: string): string {
  return SOURCE_ID_ALIASES[sourceName] ?? sourceName
}

export function sourceIdToSourceName(sourceId: string): string {
  for (const [alias, id] of Object.entries(SOURCE_ID_ALIASES)) {
    if (id === sourceId) return alias
  }
  return sourceId
}
