import {
  Bot,
  Globe,
  Bell,
  Search,
  Zap,
  ArrowRight,
  Shield,
  LucideIcon,
} from "lucide-react"

export const siteConfig = {
  name: "JobAgg",
  description: "AI-powered job aggregation platform",

  hero: {
    badge: {
      icon: Zap,
      text: "AI agents that search for you",
    },
    heading: "Your Job Search",
    headingHighlight: "Copilot",
    headingHighlightClass: "silver",
    subheading:
      "Stop refreshing job boards. Create AI agents that scan Reddit, X, and dozens of other sources to find roles that actually match what you're looking for.",
    cta: {
      text: "Get Started — It's Free",
      icon: ArrowRight,
    },
    ctaSubtext: "No credit card required. Sign in with Google.",
  },

  stats: [
    { value: "10K+", label: "Jobs indexed weekly" },
    { value: "50+", label: "Sources monitored" },
    { value: "< 2min", label: "Time to first match" },
  ],

  features: {
    heading: "Everything you need to land your next role",
    subheading:
      "Powerful features designed to make your job search smarter, not harder.",
    items: [
      {
        icon: Bot,
        title: "AI-Powered Matching",
        description:
          "Describe your ideal role in plain language and our AI agents scan hundreds of sources to find the best matches.",
      },
      {
        icon: Globe,
        title: "Aggregate from Everywhere",
        description:
          "Jobs from Reddit, X, Hacker News, and more — all in one unified feed. No more switching between sites.",
      },
      {
        icon: Bell,
        title: "Smart Alerts",
        description:
          "Create custom agents that monitor for new opportunities 24/7 and notify you instantly when a match is found.",
      },
      {
        icon: Search,
        title: "Deep Filtering",
        description:
          "Filter by role, location, salary range, tech stack, remote policy, and dozens of other criteria.",
      },
      {
        icon: Zap,
        title: "Instant Apply",
        description:
          "Save jobs you love and come back to them. One-click save with notes and application status tracking.",
      },
      {
        icon: Shield,
        title: "Privacy First",
        description:
          "Your data stays yours. No resumé uploads required. Search and discover without sharing personal information.",
      },
    ] as { icon: LucideIcon; title: string; description: string }[],
  },

  testimonials: {
    heading: "Loved by developers",
    subheading: "Hear from people who found their roles through JobAgg.",
    items: [
      {
        quote:
          "Found my dream remote role through a Reddit post I would have never seen manually. JobAgg is a game changer.",
        name: "Sarah K.",
        role: "Frontend Engineer",
      },
      {
        quote:
          "I set up an agent for senior backend roles in fintech. Got notified within an hour of a perfect match.",
        name: "Marcus D.",
        role: "Senior Backend Developer",
      },
      {
        quote:
          "Finally, a job search tool that actually understands what I'm looking for instead of spamming irrelevant listings.",
        name: "Priya R.",
        role: "Full Stack Developer",
      },
    ],
  },

  sources: {
    heading: "Aggregating from sources you already trust",
    logos: [
      "Reddit",
      "X (Twitter)",
      "Hacker News",
      "Product Hunt",
      "LinkedIn",
      "Indeed",
    ],
  },

  bottomCta: {
    heading: "Ready to find your next role?",
    subheading:
      "Set up your first AI agent in under 2 minutes and start getting matched with relevant opportunities.",
    cta: {
      text: "Get Started — It's Free",
      icon: ArrowRight,
    },
  },

  footer: {
    copyrightOwner: "JobAgg",
  },

  auth: {
    provider: "google" as const,
    callbackUrl: "/jobs",
  },
}
