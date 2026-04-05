import { auth } from "@/lib/auth"
import { headers } from "next/headers"
import { redirect } from "next/navigation"
import { Hero } from "@/components/hero"

export default async function Page() {
  const session = await auth.api.getSession({
    headers: await headers(),
  })
  if (session) {
    redirect("/jobs")
  }
  return <Hero />
}
