import { prisma } from "@workspace/database"

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { searchParams } = new URL(_request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const limit = Math.min(
    100,
    Math.max(1, Number(searchParams.get("limit")) || 20)
  )

  const agent = await prisma.agent.findFirst({
    where: { id, userId },
    select: { id: true },
  })
  if (!agent) {
    return Response.json({ error: "Agent not found" }, { status: 404 })
  }

  const rows = await prisma.agentRun.findMany({
    where: { agentId: id },
    orderBy: { startedAt: "desc" },
    take: limit,
  })

  return Response.json(
    rows.map((row) => ({
      id: row.id,
      agentId: row.agentId,
      status: row.status,
      postsScanned: row.postsScanned,
      jobsFound: row.jobsFound,
      newJobs: row.newJobs,
      startedAt: row.startedAt.toISOString(),
      finishedAt: row.finishedAt?.toISOString() ?? null,
      error: row.error,
    }))
  )
}
