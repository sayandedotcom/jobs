import { prisma } from "@workspace/database"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const rows = await prisma.savedSearch.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
  })

  return Response.json(
    rows.map((row) => ({
      id: row.id,
      keywords: row.keywords,
      location: row.location,
      jobType: row.jobType,
      isActive: row.isActive,
      createdAt: row.createdAt.toISOString(),
    }))
  )
}

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const body = (await request.json()) as {
    keywords?: string
    location?: string
    jobType?: string
  }

  const row = await prisma.savedSearch.create({
    data: {
      userId,
      keywords: body.keywords ?? null,
      location: body.location ?? null,
      jobType: body.jobType ?? null,
    },
  })

  return Response.json(
    {
      id: row.id,
      keywords: row.keywords,
      location: row.location,
      jobType: row.jobType,
      isActive: row.isActive,
      createdAt: row.createdAt.toISOString(),
    },
    { status: 201 }
  )
}
