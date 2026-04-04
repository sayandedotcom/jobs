import { prisma } from "@workspace/database"

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { searchParams } = new URL(_request.url)
  const userId = searchParams.get("userId")
  if (!userId)
    return Response.json({ error: "userId required" }, { status: 400 })

  const result = await prisma.savedSearch.deleteMany({
    where: { id, userId },
  })
  if (result.count === 0) {
    return Response.json({ error: "Search not found" }, { status: 404 })
  }
  return new Response(null, { status: 204 })
}
