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

  const agent = await prisma.agent.findFirst({
    where: { id, userId },
    select: { id: true },
  })
  if (!agent) {
    return Response.json({ error: "Agent not found" }, { status: 404 })
  }

  const page = Math.max(1, Number(searchParams.get("page")) || 1)
  const pageSize = Math.min(
    100,
    Math.max(1, Number(searchParams.get("pageSize")) || 20)
  )

  const rows = await prisma.agentResult.findMany({
    where: { agentId: id },
    orderBy: { relevanceScore: "desc" },
    skip: (page - 1) * pageSize,
    take: pageSize,
    include: { listing: true },
  })

  return Response.json(
    rows.map((row) => ({
      id: row.id,
      agentId: row.agentId,
      listingId: row.listingId,
      relevanceScore: row.relevanceScore,
      matchReason: row.matchReason,
      isViewed: row.isViewed,
      createdAt: row.createdAt.toISOString(),
      listing: {
        id: row.listing.id,
        title: row.listing.title,
        company: row.listing.company,
        description: row.listing.description,
        location: row.listing.location,
        salary: row.listing.salary,
        url: row.listing.url,
        jobType: row.listing.jobType,
        applyUrl: row.listing.applyUrl,
        postedAt: row.listing.postedAt?.toISOString() ?? null,
        createdAt: row.listing.createdAt.toISOString(),
      },
    }))
  )
}
