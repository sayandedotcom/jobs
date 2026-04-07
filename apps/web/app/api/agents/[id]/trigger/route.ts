import { getAuthenticatedUserId } from "@/lib/auth-server"
import { env } from "@/env"
import { prisma } from "@workspace/database"

const PYTHON_API_URL = env.PYTHON_API_URL

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const userId = await getAuthenticatedUserId()
  if (!userId) return Response.json({ error: "Unauthorized" }, { status: 401 })

  const agent = await prisma.agent.findFirst({
    where: { id, userId },
    select: { id: true },
  })
  if (!agent)
    return Response.json({ error: "Agent not found" }, { status: 404 })

  const res = await fetch(
    `${PYTHON_API_URL}/api/agents/${id}/trigger?userId=${userId}`,
    { method: "POST" }
  )

  if (!res.ok) {
    const text = await res.text()
    return Response.json(
      { error: "Trigger failed", detail: text },
      { status: res.status }
    )
  }

  const data = await res.json()
  return Response.json({
    ...data,
    startedAt: data.startedAt ? new Date(data.startedAt).toISOString() : null,
    finishedAt: data.finishedAt
      ? new Date(data.finishedAt).toISOString()
      : null,
  })
}
