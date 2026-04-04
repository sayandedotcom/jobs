import { getAuthenticatedUserId } from "@/lib/auth-server"
import { prisma } from "@workspace/database"

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const userId = await getAuthenticatedUserId()
  if (!userId) return Response.json({ error: "Unauthorized" }, { status: 401 })

  const result = await prisma.savedSearch.deleteMany({
    where: { id, userId },
  })
  if (result.count === 0) {
    return Response.json({ error: "Search not found" }, { status: 404 })
  }
  return new Response(null, { status: 204 })
}
