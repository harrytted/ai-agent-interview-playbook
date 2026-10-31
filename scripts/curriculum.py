"""Stable chapter order shared by content and rendered-site validation."""

ADVANCED_CHAPTERS = (
    "01-harness-and-deep-agents",
    "02-durable-execution",
    "03-context-engineering",
    "04-memory-and-skills",
    "05-tool-routing-and-mcp",
    "06-agentic-rag",
    "07-multi-agent-systems",
    "08-coding-and-computer-use",
    "09-evaluation-and-feedback",
    "10-performance-and-serving",
    "11-security-and-governance",
    "12-agent-training",
    "13-model-api-and-output-contracts",
    "14-ingestion-and-index-lifecycle",
    "15-text-to-sql-and-data-analysis",
    "16-service-deployment-and-operations",
    "17-event-driven-and-proactive-agents",
    "18-multimodal-and-realtime-agents",
)
BASE_QUESTIONS = 56
ADVANCED_QUESTIONS = len(ADVANCED_CHAPTERS) * 3
EXPECTED_QUESTIONS = BASE_QUESTIONS + ADVANCED_QUESTIONS
