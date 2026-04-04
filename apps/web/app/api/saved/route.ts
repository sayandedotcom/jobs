import { prisma } from "@workspace/database"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const rows = await prisma.userSavedJob.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
    include: { listing: true },
  })

  const result = rows.map((row) => ({
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
  }))

  return Response.json(result)
}

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const body = (await request.json()) as { listingId: string }
  if (!body.listingId) {
    return Response.json({ error: "listingId required" }, { status: 400 })
  }

  const listing = await prisma.listing.findUnique({
    where: { id: body.listingId },
  })
  if (!listing) {
    return Response.json({ error: "Listing not found" }, { status: 404 })
  }

  try {
    const row = await prisma.userSavedJob.create({
      data: { userId, listingId: body.listingId, status: "saved" },
    })
    return Response.json(
      {
        id: row.id,
        listingId: row.listingId,
        status: row.status,
        notes: row.notes,
        createdAt: row.createdAt.toISOString(),
        listing: {
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
        },
      },
      { status: 201 }
    )
  } catch {
    return Response.json({ error: "Job already saved" }, { status: 409 })
  }
}
