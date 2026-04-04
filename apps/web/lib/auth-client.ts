import { createAuthClient } from "better-auth/react"

import { auth } from "@/lib/auth"

export const authClient = createAuthClient({
  basePath: "/api/auth",
})

export const { useSession, signIn, signOut } = authClient
