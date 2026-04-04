import { PrismaClient } from "@prisma/client"

const prisma = new PrismaClient()

async function main() {
  const reddit = await prisma.source.upsert({
    where: { name: "reddit" },
    update: {},
    create: {
      name: "reddit",
      type: "reddit",
      isActive: true,
    },
  })

  const subreddits = [
    "forhire",
    "jobbit",
    "remotejs",
    "remotework",
    "jobs",
    "careerguidance",
    "webdev",
    "javascriptjobs",
    "pythonjobs",
    "reactjs",
    "vuejs",
    "node",
    "golang",
    "rust",
    "datasciencejobs",
    "machinelearningjobs",
    "designjobs",
    "techjobs",
    "startupjobs",
    "big4jobs",
  ]

  for (const name of subreddits) {
    await prisma.subSource.upsert({
      where: {
        sourceId_name: {
          sourceId: reddit.id,
          name,
        },
      },
      update: {},
      create: {
        sourceId: reddit.id,
        name,
        isActive: true,
      },
    })
    console.log(`  Added subreddit: ${name}`)
  }

  console.log("Seed completed!")
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
