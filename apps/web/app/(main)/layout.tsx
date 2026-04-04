import Link from "next/link"
import Image from "next/image"
import { auth } from "@/lib/auth"
import { headers } from "next/headers"
import { redirect } from "next/navigation"

export default async function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth.api.getSession({
    headers: await headers(),
  })
  if (!session) redirect("/login")

  return (
    <div className="min-h-svc">
      <header className="bg-background/95 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 border-b backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/jobs" className="text-lg font-bold">
            JobAgg
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/jobs"
              className="text-muted-foreground hover:text-foreground text-sm"
            >
              Jobs
            </Link>
            <Link
              href="/saved"
              className="text-muted-foreground hover:text-foreground text-sm"
            >
              Saved
            </Link>
            <Link
              href="/alerts"
              className="text-muted-foreground hover:text-foreground text-sm"
            >
              Alerts
            </Link>
            {session.user?.image && (
              <Image
                src={session.user.image}
                alt={session.user.name ?? ""}
                width={32}
                height={32}
                className="h-8 w-8 rounded-full"
              />
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  )
}
