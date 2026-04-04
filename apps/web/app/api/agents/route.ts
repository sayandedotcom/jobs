import { prisma } from "@workspace/database"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const agents = await prisma.agent.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
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

  return Response.json(
    agents.map((a) => ({
      id: a.id,
      userId: a.userId,
      name: a.name,
      jobTitle: a.jobTitle,
      skills: a.skills,
      location: a.location,
      openToRelocate: a.openToRelocate,
      experienceLevel: a.experienceLevel,
      salaryMin: a.salaryMin,
      salaryMax: a.salaryMax,
      jobType: a.jobType,
      sources: a.sources,
      scanIntervalMinutes: a.scanIntervalMinutes,
      isActive: a.isActive,
      lastRunAt: a.lastRunAt?.toISOString() ?? null,
      nextRunAt: a.nextRunAt?.toISOString() ?? null,
      createdAt: a.createdAt.toISOString(),
      updatedAt: a.updatedAt.toISOString(),
      totalResults: a._count.results,
      unviewedResults: a.results.length,
      latestRunStatus: a.runs[0]?.status ?? null,
    }))
  )
}

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const body = (await request.json()) as {
    name: string
    jobTitle: string
    skills?: string[]
    location?: string
    openToRelocate?: boolean
    experienceLevel?: string
    salaryMin?: number
    salaryMax?: number
    jobType?: string
    sources?: string[]
    scanIntervalMinutes?: number
  }

  if (!body.name || !body.jobTitle) {
    return Response.json(
      { error: "name and jobTitle are required" },
      { status: 400 }
    )
  }

  const interval = body.scanIntervalMinutes ?? 1440
  if (interval < 30) {
    return Response.json(
      { error: "Scan interval must be at least 30 minutes" },
      { status: 400 }
    )
  }

  const now = new Date()
  const nextRunAt = new Date(now.getTime() + interval * 60 * 1000)

  const agent = await prisma.agent.create({
    data: {
      userId,
      name: body.name,
      jobTitle: body.jobTitle,
      skills: body.skills ?? [],
      location: body.location ?? null,
      openToRelocate: body.openToRelocate ?? false,
      experienceLevel: body.experienceLevel ?? null,
      salaryMin: body.salaryMin ?? null,
      salaryMax: body.salaryMax ?? null,
      jobType: body.jobType ?? null,
      sources: body.sources ?? ["reddit"],
      scanIntervalMinutes: interval,
      nextRunAt,
    },
  })

  return Response.json(
    {
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
      totalResults: 0,
      unviewedResults: 0,
      latestRunStatus: null,
    },
    { status: 201 }
  )
}
