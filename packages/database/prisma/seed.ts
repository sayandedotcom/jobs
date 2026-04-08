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
    },
  })

  await prisma.source.upsert({
    where: { name: "x" },
    update: {},
    create: {
      name: "x",
      type: "x",
    },
  })

  const hackerNews = await prisma.source.upsert({
    where: { name: "hackernews" },
    update: {},
    create: {
      name: "hackernews",
      type: "hackernews",
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
      },
    })
    console.log(`  Added subreddit: ${name}`)
  }

  await prisma.subSource.deleteMany({
    where: {
      sourceId: hackerNews.id,
      type: "whoishiring",
      NOT: {
        name: "latest",
      },
    },
  })

  await prisma.subSource.upsert({
    where: {
      sourceId_name: {
        sourceId: hackerNews.id,
        name: "latest",
      },
    },
    update: {
      type: "whoishiring",
    },
    create: {
      sourceId: hackerNews.id,
      name: "latest",
      type: "whoishiring",
    },
  })
  console.log('  Added Hacker News "latest" hiring thread')

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
