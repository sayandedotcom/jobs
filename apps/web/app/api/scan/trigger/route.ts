import { env } from "@/env"
import { sourceIdToSourceName } from "@/lib/source-mapping"

const PYTHON_API_URL = env.PYTHON_API_URL

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url)
  let source = searchParams.get("source")
  if (!source) {
    return Response.json({ error: "source is required" }, { status: 400 })
  }

  source = sourceIdToSourceName(source)

  const res = await fetch(
    `${PYTHON_API_URL}/api/scan/trigger?source=${encodeURIComponent(source)}`,
    { method: "POST" }
  )

  if (!res.ok) {
    const text = await res.text()
    return Response.json(
      { error: "Scan trigger failed", detail: text },
      { status: res.status }
    )
  }

  const data = await res.json()
  return Response.json(data)
}
