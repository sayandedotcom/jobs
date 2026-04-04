import { PrismaClient } from "@prisma/client"

import { subreddits } from "./subreddits.config.js"

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
