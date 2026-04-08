export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <div className="mx-auto w-full max-w-5xl px-4 py-8">{children}</div>
}
