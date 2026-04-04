import { prisma } from "@workspace/database"

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const listing = await prisma.listing.findUnique({ where: { id } })
  if (!listing) {
    return Response.json({ error: "Job not found" }, { status: 404 })
  }
  return Response.json({
    id: listing.id,
    title: listing.title,
    company: listing.company,
    description: listing.description,
    location: listing.location,
    salary: listing.salary,
    url: listing.url,
    jobType: listing.jobType,
    applyUrl: listing.applyUrl,
    postedAt: listing.postedAt?.toISOString() ?? null,
    createdAt: listing.createdAt.toISOString(),
  })
}
