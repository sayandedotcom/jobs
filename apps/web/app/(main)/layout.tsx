import { auth } from "@/lib/auth"
import { headers } from "next/headers"
import { redirect } from "next/navigation"
import { SidebarLayout } from "@/components/sidebar-layout"

export default async function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth.api.getSession({
    headers: await headers(),
  })
  if (!session) redirect("/")

  const user = {
    name: session.user?.name ?? "User",
    email: session.user?.email ?? "",
    avatar: session.user?.image ?? "",
  }

  return <SidebarLayout user={user}>{children}</SidebarLayout>
}
