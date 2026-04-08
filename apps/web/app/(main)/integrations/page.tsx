import { source } from "@/config/source"
import { Card, CardContent } from "@workspace/ui/components/card"
import { Separator } from "@workspace/ui/components/separator"

export default function IntegrationsPage() {
  const active = source.filter((s) => s.active)
  const inactive = source.filter((s) => !s.active)

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Integrations</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Job sources connected to the platform.{" "}
          <span className="text-foreground font-medium">
            {active.length} fetching jobs
          </span>{" "}
          out of {source.length} total.
        </p>
      </div>

      <Separator />

      <section className="flex flex-col gap-4">
        <h2 className="text-lg font-medium">Active</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {active.map((s, i) => (
            <SourceCard key={s.id} idx={i} {...s} />
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="text-lg font-medium">Inactive</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {inactive.map((s) => (
            <SourceCard key={s.id} {...s} />
          ))}
        </div>
      </section>

      <Separator />

      <p className="text-muted-foreground text-center text-sm">
        Want more integrations?{" "}
        <a
          href="https://x.com/sayandedotcom"
          target="_blank"
          rel="noopener noreferrer"
          className="text-foreground hover:text-foreground/80 underline underline-offset-4"
        >
          Reach out to me on X
        </a>
      </p>
    </div>
  )
}

function SourceCard({
  name,
  src,
  url,
  active: isActive,
  idx,
}: (typeof source)[number] & { idx?: number }) {
  const lastFetchHrs = ((idx ?? 0) % 6) + 1
  const nextFetchHrs = ((idx ?? 0) % 5) + 1
  return (
    <a href={url} target="_blank" rel="noopener noreferrer">
      <Card className="hover:bg-accent/50 transition-colors">
        <CardContent className="flex items-center gap-3">
          <img
            src={src}
            alt={name}
            className="bg-muted size-10 shrink-0 rounded-lg object-contain p-1.5"
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate font-medium">{name}</span>
              {isActive ? (
                <span className="relative flex size-3 items-center justify-center">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex size-3 rounded-full bg-emerald-500" />
                </span>
              ) : (
                <span className="relative flex size-3 items-center justify-center">
                  <span className="inline-flex size-3 rounded-full bg-red-500" />
                </span>
              )}
            </div>
            {isActive ? (
              <p className="text-muted-foreground text-xs">
                Fetch {lastFetchHrs}hr ago · Next in {nextFetchHrs}h
              </p>
            ) : (
              <p className="text-muted-foreground truncate text-xs">{url}</p>
            )}
          </div>
        </CardContent>
      </Card>
    </a>
  )
}
