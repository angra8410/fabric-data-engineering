"""Configuration for the job-boards agent. Edit this to customize."""

# RSS feeds of job boards (free, no API keys needed)
FEEDS = [
    # Remote OK
    "https://remoteok.com/remote-dev-jobs.rss",
    # WeWorkRemotely (programming category)
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    # Hacker News "Who is hiring" companion feed
    "https://hnrss.org/jobs",
    # Remotive
    "https://remotive.com/feed/remote/software-development",
    # Remotive — Data / Analytics roles
    "https://remotive.com/feed/remote/data",
    # Remote OK — all jobs (catches analyst/BI titles)
    "https://remoteok.com/remote-jobs.rss",
]

# Keywords that must appear in title or summary (case-insensitive).
# Empty list = accept everything.
MUST_HAVE = [
    "data analyst",
    "data analytics",
    "power bi",
    "powerbi",
    "business intelligence",
    "bi developer",
    "bi analyst",
    "analytics developer",
]

# Keywords that disqualify a job.
EXCLUDE = ["senior staff", "principal", "unpaid", "internship"]

# How many top matches to include in the digest
TOP_N = 10

# Max age of postings to consider (days)
MAX_AGE_DAYS = 7

# LLM provider: "ollama" (local) or "gemini" (needs GOOGLE_API_KEY)
LLM_PROVIDER = "ollama"
