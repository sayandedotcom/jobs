import { prisma } from "@workspace/database"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const limit = Math.min(
    100,
    Math.max(1, Number(searchParams.get("limit")) || 20)
  )

  const rows = await prisma.scanRun.findMany({
    orderBy: { startedAt: "desc" },
    take: limit,
  })

  return Response.json(
    rows.map((row) => ({
      id: row.id,
      sourceName: row.sourceName,
      status: row.status,
      postsFound: row.postsFound,
      postsNew: row.postsNew,
      jobsAdded: row.jobsAdded,
      errors: row.errors,
      startedAt: row.startedAt.toISOString(),
      finishedAt: row.finishedAt?.toISOString() ?? null,
    }))
  )
}
