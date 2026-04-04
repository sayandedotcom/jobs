import { getAuthenticatedUserId } from "@/lib/auth-server"
import { prisma } from "@workspace/database"

export async function PATCH(
  _request: Request,
  { params }: { params: Promise<{ id: string; resultId: string }> }
) {
  const { id, resultId } = await params
  const userId = await getAuthenticatedUserId()
  if (!userId) return Response.json({ error: "Unauthorized" }, { status: 401 })

  const agent = await prisma.agent.findFirst({
    where: { id, userId },
    select: { id: true },
  })
  if (!agent) {
    return Response.json({ error: "Agent not found" }, { status: 404 })
  }

  await prisma.agentResult.update({
    where: { id: resultId, agentId: id },
    data: { isViewed: true },
  })

  return new Response(null, { status: 204 })
}
