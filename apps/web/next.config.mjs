/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@workspace/ui", "@workspace/database"],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
      {
        protocol: "https",
        hostname: "cdn.brandfetch.io",
      },
    ],
  },
}

if (process.env.NODE_ENV === "development") {
  const pythonUrl = process.env.PYTHON_API_URL || "http://localhost:8000"

  nextConfig.rewrites = async () => [
    {
      source: "/api/scan/trigger",
      destination: `${pythonUrl}/api/scan/trigger`,
    },
    {
      source: "/api/agents/:id/trigger",
      destination: `${pythonUrl}/api/agents/:id/trigger`,
    },
    {
      source: "/api/cron/:path*",
      destination: `${pythonUrl}/api/cron/:path*`,
    },
  ]
}

export default nextConfig
