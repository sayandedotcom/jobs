import NextAuth from "next-auth"
import type { NextAuthConfig } from "next-auth"
import type { Session } from "next-auth"
import Google from "next-auth/providers/google"
import { PrismaAdapter } from "@auth/prisma-adapter"
import { prisma } from "@workspace/database"

declare module "next-auth" {
  interface Session {
    user: {
      id: string
      email: string
      name?: string | null
      image?: string | null
    }
  }
}

export const config: NextAuthConfig = {
  adapter: PrismaAdapter(prisma),
  providers: [Google],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    session({ session, user }) {
      session.user.id = user.id
      return session
    },
  },
  session: {
    strategy: "database",
  },
}

const nextAuthResult = NextAuth(config)

export const handlers = nextAuthResult.handlers
export const signOut = nextAuthResult.signOut

export async function auth(): Promise<Session | null> {
  return nextAuthResult.auth()
}

export async function signIn(
  provider?: string,
  options?: Record<string, unknown>
) {
  return nextAuthResult.signIn(provider, options)
}
