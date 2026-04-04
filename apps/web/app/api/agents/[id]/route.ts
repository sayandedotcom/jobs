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
    include: {
      _count: { select: { results: true } },
      results: { where: { isViewed: false }, select: { id: true } },
      runs: {
        orderBy: { startedAt: "desc" },
        take: 1,
        select: { status: true },
      },
    },
  })
  if (!agent)
    return Response.json({ error: "Agent not found" }, { status: 404 })

  return Response.json({
    id: agent.id,
    userId: agent.userId,
    name: agent.name,
    jobTitle: agent.jobTitle,
    skills: agent.skills,
    location: agent.location,
    openToRelocate: agent.openToRelocate,
    experienceLevel: agent.experienceLevel,
    salaryMin: agent.salaryMin,
    salaryMax: agent.salaryMax,
    jobType: agent.jobType,
    sources: agent.sources,
    scanIntervalMinutes: agent.scanIntervalMinutes,
    isActive: agent.isActive,
    lastRunAt: agent.lastRunAt?.toISOString() ?? null,
    nextRunAt: agent.nextRunAt?.toISOString() ?? null,
    createdAt: agent.createdAt.toISOString(),
    updatedAt: agent.updatedAt.toISOString(),
    totalResults: agent._count.results,
    unviewedResults: agent.results.length,
    latestRunStatus: agent.runs[0]?.status ?? null,
  })
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const body = (await request.json()) as Record<string, unknown>
  if (Object.keys(body).length === 0) {
    return Response.json({ error: "No fields to update" }, { status: 400 })
  }

  const existing = await prisma.agent.findFirst({ where: { id, userId } })
  if (!existing) {
    return Response.json({ error: "Agent not found" }, { status: 404 })
  }

  const data: Record<string, unknown> = {}
  const allowedFields = [
    "name",
    "jobTitle",
    "skills",
    "location",
    "openToRelocate",
    "experienceLevel",
    "salaryMin",
    "salaryMax",
    "jobType",
    "sources",
    "scanIntervalMinutes",
    "isActive",
  ]

  for (const field of allowedFields) {
    if (body[field] !== undefined) {
      data[field] = body[field]
    }
  }

  if (data.scanIntervalMinutes !== undefined) {
    const interval = Number(data.scanIntervalMinutes)
    if (interval < 30) {
      return Response.json(
        { error: "Scan interval must be at least 30 minutes" },
        { status: 400 }
      )
    }
    data.nextRunAt = new Date(Date.now() + interval * 60 * 1000)
  }

  const agent = await prisma.agent.update({
    where: { id },
    data,
    include: {
      _count: { select: { results: true } },
      results: { where: { isViewed: false }, select: { id: true } },
      runs: {
        orderBy: { startedAt: "desc" },
        take: 1,
        select: { status: true },
      },
    },
  })

  return Response.json({
    id: agent.id,
    userId: agent.userId,
    name: agent.name,
    jobTitle: agent.jobTitle,
    skills: agent.skills,
    location: agent.location,
    openToRelocate: agent.openToRelocate,
    experienceLevel: agent.experienceLevel,
    salaryMin: agent.salaryMin,
    salaryMax: agent.salaryMax,
    jobType: agent.jobType,
    sources: agent.sources,
    scanIntervalMinutes: agent.scanIntervalMinutes,
    isActive: agent.isActive,
    lastRunAt: agent.lastRunAt?.toISOString() ?? null,
    nextRunAt: agent.nextRunAt?.toISOString() ?? null,
    createdAt: agent.createdAt.toISOString(),
    updatedAt: agent.updatedAt.toISOString(),
    totalResults: agent._count.results,
    unviewedResults: agent.results.length,
    latestRunStatus: agent.runs[0]?.status ?? null,
  })
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { searchParams } = new URL(_request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const result = await prisma.agent.deleteMany({ where: { id, userId } })
  if (result.count === 0) {
    return Response.json({ error: "Agent not found" }, { status: 404 })
  }
  return new Response(null, { status: 204 })
}
