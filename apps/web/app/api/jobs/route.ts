import { getAuthenticatedUserId } from "@/lib/auth-server"
import { prisma } from "@workspace/database"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const search = searchParams.get("search")
  const location = searchParams.get("location")
  const jobType = searchParams.get("jobType")
  const company = searchParams.get("company")
  const page = Math.max(1, Number(searchParams.get("page")) || 1)
  const pageSize = Math.min(
    100,
    Math.max(1, Number(searchParams.get("pageSize")) || 20)
  )
  const userId = await getAuthenticatedUserId()

  const where: Record<string, unknown> = {}
  if (search) {
    where.OR = [
      { title: { contains: search, mode: "insensitive" } },
      { description: { contains: search, mode: "insensitive" } },
      { company: { contains: search, mode: "insensitive" } },
    ]
  }
  if (location) where.location = { contains: location, mode: "insensitive" }
  if (jobType) where.jobType = jobType
  if (company) where.company = { contains: company, mode: "insensitive" }

  const include = userId
    ? { userSavedJobs: { where: { userId }, select: { id: true } } }
    : undefined

  const [total, rows] = await Promise.all([
    prisma.listing.count({ where }),
    prisma.listing.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
      include,
    }),
  ])

  const jobs = rows.map((row) => {
    const {
      userSavedJobs,
      agentResults: _ar,
      rawPosts: _rp,
      ...rest
    } = row as Record<string, unknown> & {
      userSavedJobs?: unknown[]
      agentResults?: unknown[]
      rawPosts?: unknown[]
    }
    return {
      ...rest,
      postedAt: (rest.postedAt as Date | null)?.toISOString?.() ?? null,
      createdAt: (rest.createdAt as Date).toISOString(),
      isSaved: userId ? (userSavedJobs?.length ?? 0) > 0 : false,
    }
  })

  return Response.json({ jobs, total, page, pageSize })
}
