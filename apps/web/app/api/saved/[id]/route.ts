import { getAuthenticatedUserId } from "@/lib/auth-server"
import { prisma } from "@workspace/database"

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const userId = await getAuthenticatedUserId()
  if (!userId) return Response.json({ error: "Unauthorized" }, { status: 401 })

  const body = (await request.json()) as { status?: string; notes?: string }
  if (!body.status && body.notes === undefined) {
    return Response.json({ error: "No fields to update" }, { status: 400 })
  }

  const existing = await prisma.userSavedJob.findFirst({
    where: { id, userId },
  })
  if (!existing) {
    return Response.json({ error: "Saved job not found" }, { status: 404 })
  }

  const row = await prisma.userSavedJob.update({
    where: { id },
    data: {
      ...(body.status ? { status: body.status } : {}),
      ...(body.notes !== undefined ? { notes: body.notes } : {}),
    },
    include: { listing: true },
  })

  return Response.json({
    id: row.id,
    listingId: row.listingId,
    status: row.status,
    notes: row.notes,
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
  })
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const userId = await getAuthenticatedUserId()
  if (!userId) return Response.json({ error: "Unauthorized" }, { status: 401 })

  const result = await prisma.userSavedJob.deleteMany({
    where: { id, userId },
  })
  if (result.count === 0) {
    return Response.json({ error: "Saved job not found" }, { status: 404 })
  }
  return new Response(null, { status: 204 })
}
