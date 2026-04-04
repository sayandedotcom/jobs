import { createAuthClient } from "better-auth/react"

type AuthClient = ReturnType<typeof createAuthClient>

export const authClient: AuthClient = createAuthClient({
  basePath: "/api/auth",
})

export const { useSession, signIn, signOut } = authClient
