# 🧠 AI Interview Agent — Ultra-Detailed Full-Stack Implementation Prompt

---

## 🎯 MISSION

You are an expert full-stack AI engineer. Build a **complete, production-quality AI Interview Agent web application** for the ABTalks AI Cohort hackathon. This is NOT a prototype — every feature must be fully implemented, tested, and deployment-ready.

The app conducts personalized multi-turn technical interviews based on a candidate's real learning journey through a 31-day AI Engineering cohort. It must feel like a real human interviewer, generate structured feedback, and expose the exact HTTP API defined in the technical specification below.

---

## 🛠️ TECH STACK

### Frontend
- **Framework**: Next.js 14 App Router
- **Styling**: Tailwind CSS v3 + custom CSS variables
- **Animations**: Framer Motion v11
- **State**: Zustand v4
- **Icons**: Lucide React
- **HTTP**: Native fetch with async/await
- **Fonts**: Google Fonts — Inter (body) + JetBrains Mono (code/IDs)
- **Avatars**: DiceBear Avataaars API — `https://api.dicebear.com/7.x/avataaars/svg?seed={name}`

### Backend
- **Runtime**: Node.js via Next.js API Routes
- **AI Model**: **Groq API** — model: `llama-3.3-70b-versatile` (free tier, blazing fast)
- **Groq SDK**: `groq-sdk` npm package
- **Session Store**: In-memory `Map<string, InterviewSession>` (no DB required)
- **Validation**: Zod v3
- **ID Generation**: `crypto.randomUUID()`

### Package Manager & Dev
- **Package Manager**: npm
- **Node Version**: 18+
- **TypeScript**: strict mode enabled

---

## 📁 COMPLETE FILE STRUCTURE

```
/
├── app/
│   ├── globals.css                         # Design tokens, base styles, animations
│   ├── layout.tsx                          # Root layout with font loading, metadata
│   ├── page.tsx                            # Landing — candidate selection grid
│   ├── interview/
│   │   └── [candidateId]/
│   │       └── page.tsx                   # Live interview chat interface
│   └── feedback/
│       └── [sessionId]/
│           └── page.tsx                   # Post-interview feedback report
│
├── app/api/
│   └── interview/
│       └── route.ts                       # POST /api/interview — THE required endpoint
│
├── components/
│   ├── CandidateCard.tsx                  # Candidate selection card with avatar + stats
│   ├── ChatBubble.tsx                     # Individual message bubble (interviewer/candidate)
│   ├── TypingIndicator.tsx                # Three-dot animated typing indicator
│   ├── InterviewHeader.tsx                # Progress bar, timer, question counter
│   ├── TopicTracker.tsx                   # Live sidebar showing days/topics covered
│   ├── FeedbackReport.tsx                 # Full feedback display component
│   ├── ScoreRing.tsx                      # Animated circular score display
│   └── ProgressBar.tsx                    # Animated horizontal progress bar
│
├── lib/
│   ├── groq.ts                            # Groq client initialization + chat wrapper
│   ├── agent.ts                           # Core interview agent: session, questions, context
│   ├── prompts.ts                         # All system prompt builders
│   ├── feedback.ts                        # Feedback generation + structured output parsing
│   ├── curriculum.ts                      # Curriculum loader, day lookup, topic helpers
│   ├── candidates.ts                      # Candidate profile loader + mission analysis
│   └── session.ts                         # In-memory session store + expiry logic
│
├── data/
│   ├── curriculum.json                    # PROVIDED BELOW — complete 31-day curriculum
│   └── candidates.json                    # PROVIDED BELOW — all 20 real candidate profiles
│
├── types/
│   └── index.ts                           # All TypeScript interfaces
│
├── .env.local                             # Environment variables
├── .env.local.example                     # Example env file for docs
├── README.md                              # Setup + API docs
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

---

## 🔑 ENVIRONMENT VARIABLES

### .env.local
```bash
# Groq API (free tier — get key at console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Groq Model — llama-3.3-70b-versatile is free and fast
GROQ_MODEL=llama-3.3-70b-versatile

# Session configuration
SESSION_TIMEOUT_MS=7200000        # 2 hours
MAX_QUESTIONS_PER_SESSION=14
MIN_QUESTIONS_REQUIRED=8
MIN_DAYS_REQUIRED=4

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_APP_NAME="AI Interview Agent"
```

---

## 📦 PACKAGE.JSON DEPENDENCIES

```json
{
  "name": "ai-interview-agent",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.5",
    "react": "^18",
    "react-dom": "^18",
    "groq-sdk": "^0.5.0",
    "framer-motion": "^11.0.0",
    "zustand": "^4.5.0",
    "lucide-react": "^0.400.0",
    "zod": "^3.23.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "tailwindcss": "^3.4.0",
    "eslint": "^8",
    "eslint-config-next": "14.2.5"
  }
}
```

---

## 🗃️ DATA FILES (USE EXACTLY AS-IS)

### data/curriculum.json — COMPLETE 31-DAY CURRICULUM (verbatim)

```json
{
  "cohort": "AI Cohort · 31 days · 8 modules",
  "modules": [
    { "n": 1, "title": "Environment & Tooling", "days": [1, 3] },
    { "n": 2, "title": "Data Foundations", "days": [4, 6] },
    { "n": 3, "title": "Embeddings & Vector Search", "days": [7, 10] },
    { "n": 4, "title": "LLM Core, Prompting & Fine-Tuning", "days": [11, 15] },
    { "n": 5, "title": "Chatbot Application Build", "days": [16, 20] },
    { "n": 6, "title": "Agentic AI & MCP", "days": [21, 24] },
    { "n": 7, "title": "Evaluation, Security & Deployment", "days": [25, 28] },
    { "n": 8, "title": "Production & Capstone", "days": [29, 31] }
  ],
  "days": [
    {
      "day": 1, "title": "VS Code & Python Environment Setup", "type": "SETUP",
      "tools": ["VS Code", "Python", "Python Extension", "Pylance", "Virtual Environment"],
      "objectives": [
        "Install VS Code and Python on your machine",
        "Configure the Python extension and Pylance",
        "Create and activate a project virtual environment (.venv)",
        "Run and debug your first Python program inside VS Code",
        "Verify the development environment is ready for the remaining course"
      ]
    },
    {
      "day": 2, "title": "Local LLM & AI Coding Assistant Setup", "type": "SETUP",
      "tools": ["Ollama", "Qwen2.5-Coder", "GitHub Copilot", "Cline"],
      "objectives": [
        "Install Ollama and download a local coding model",
        "Verify the local model works through the Ollama CLI",
        "Connect VS Code to the local model using GitHub Copilot or Cline",
        "Generate code using the local AI assistant",
        "Confirm the complete AI coding workflow works offline"
      ]
    },
    {
      "day": 3, "title": "First AI Project, React Frontend & GitHub", "type": "BUILD",
      "tools": ["Python", "Ollama", "FastAPI", "React", "Vite", "Git", "GitHub"],
      "objectives": [
        "Build a command-line chatbot powered by your local Ollama model",
        "Scaffold a FastAPI backend with a health endpoint",
        "Create a React application using Vite",
        "Connect the React frontend with the FastAPI backend",
        "Initialize Git, commit the project, and publish it to GitHub"
      ]
    },
    {
      "day": 4, "title": "Reading & Processing Structured Data", "type": "BUILD",
      "tools": ["Pandas", "SQLite", "SQL", "SQLAlchemy"],
      "objectives": [
        "Create synthetic healthcare plans and claims datasets",
        "Load and clean structured CSV data using Pandas",
        "Store the processed data in a SQLite database",
        "Write SQL queries to answer common healthcare questions",
        "Document reusable SQL queries for later chatbot integration"
      ]
    },
    {
      "day": 5, "title": "Reading & Processing Unstructured Data", "type": "BUILD",
      "tools": ["pdfplumber", "PyPDF", "python-docx", "Tesseract OCR", "BeautifulSoup", "Requests"],
      "objectives": [
        "Extract text from healthcare PDFs and Word documents",
        "Perform OCR on scanned enrollment forms",
        "Scrape useful content from a public healthcare webpage",
        "Clean and normalize extracted text from multiple sources",
        "Store the processed text files for knowledge-base creation"
      ]
    },
    {
      "day": 6, "title": "Building the Knowledge Base", "type": "BUILD",
      "tools": ["LangChain Text Splitters", "JSONL", "Python"],
      "objectives": [
        "Convert structured and unstructured healthcare data into a unified knowledge base",
        "Split long documents into retrieval-friendly chunks",
        "Attach metadata such as source, plan type, and document section to every chunk",
        "Export all processed records into a knowledge_base.jsonl file",
        "Validate chunk quality before using them for embeddings"
      ]
    },
    {
      "day": 7, "title": "Embeddings Explained", "type": "AI_CORE",
      "tools": ["Sentence Transformers", "OpenAI Embeddings", "Scikit-learn", "Matplotlib"],
      "objectives": [
        "Understand how text is converted into vector embeddings",
        "Generate embeddings for every knowledge base chunk",
        "Store embeddings alongside the original documents",
        "Visualize embedding clusters using PCA",
        "Analyze whether similar healthcare concepts cluster together"
      ]
    },
    {
      "day": 8, "title": "Vector Databases Overview", "type": "BUILD",
      "tools": ["ChromaDB", "Pinecone"],
      "objectives": [
        "Learn the role of vector databases in RAG applications",
        "Set up a local Chroma vector database",
        "Create a cloud-based Pinecone index for comparison",
        "Compare local and managed vector database solutions",
        "Select the most suitable database for the chatbot project"
      ]
    },
    {
      "day": 9, "title": "Building & Populating the Vector Database", "type": "BUILD",
      "tools": ["ChromaDB", "Sentence Transformers"],
      "objectives": [
        "Load knowledge base embeddings into the vector database",
        "Store documents together with metadata for filtering",
        "Verify that every knowledge base chunk has been indexed",
        "Test semantic search with healthcare-related questions",
        "Evaluate retrieval quality and metadata filtering"
      ]
    },
    {
      "day": 10, "title": "The Retrieval & Matching Engine", "type": "SHIP_IT",
      "tools": ["SQLite", "ChromaDB", "Python"],
      "objectives": [
        "Build a query router that decides between SQL, vector search, or hybrid retrieval",
        "Implement structured data lookup for plans and claims",
        "Implement semantic retrieval from the vector database",
        "Merge and deduplicate results from multiple retrieval sources",
        "Evaluate retrieval accuracy using a diverse set of healthcare questions"
      ]
    },
    {
      "day": 11, "title": "RAG End-to-End & LLM API Basics", "type": "BUILD",
      "tools": ["OpenAI SDK", "Ollama", "Groq", "Python"],
      "objectives": [
        "Connect the retrieval engine to an LLM to build a complete RAG pipeline",
        "Configure a local or hosted LLM provider using the OpenAI-compatible SDK",
        "Create a grounded prompt that answers only from retrieved context",
        "Generate answers using retrieved knowledge",
        "Evaluate chatbot responses against the retrieval-only baseline"
      ]
    },
    {
      "day": 12, "title": "Prompt Engineering Fundamentals", "type": "LEARN",
      "tools": ["LLMs", "Prompt Templates"],
      "objectives": [
        "Understand zero-shot, few-shot, and chain-of-thought prompting",
        "Design multiple system prompt variations for the chatbot",
        "Compare prompts based on accuracy, compliance, and tone",
        "Evaluate prompt performance using a fixed question set",
        "Finalize the production-ready system prompt"
      ]
    },
    {
      "day": 13, "title": "Advanced Prompting: Function Calling & Structured Outputs", "type": "BUILD",
      "tools": ["OpenAI Function Calling", "Pydantic", "Python"],
      "objectives": [
        "Define tool schemas for healthcare-related chatbot functions",
        "Implement LLM function calling with automatic tool execution",
        "Validate structured outputs using Pydantic models",
        "Log tool calls for debugging and auditing",
        "Test different user queries to verify correct tool selection"
      ]
    },
    {
      "day": 14, "title": "Fine-Tuning: Concepts & When to Use It", "type": "LEARN",
      "tools": ["JSONL", "OpenAI", "LoRA", "QLoRA"],
      "objectives": [
        "Understand when fine-tuning is more appropriate than prompting or RAG",
        "Identify chatbot issues that fine-tuning can solve",
        "Create a high-quality fine-tuning dataset",
        "Validate and organize the dataset into training and test sets",
        "Prepare the project for model fine-tuning"
      ]
    },
    {
      "day": 15, "title": "Fine-Tuning: Hands-On with LoRA & QLoRA", "type": "SHIP_IT",
      "tools": ["PEFT", "Transformers", "BitsAndBytes", "OpenAI Fine-Tuning", "LoRA"],
      "objectives": [
        "Train or fine-tune an LLM using LoRA or the OpenAI fine-tuning workflow",
        "Load and evaluate the fine-tuned model",
        "Compare the base model and fine-tuned model on unseen test cases",
        "Measure improvements in tone, consistency, and response quality",
        "Document whether fine-tuning provides measurable benefits for the chatbot"
      ]
    },
    {
      "day": 16, "title": "Chatbot Backend & API Integration", "type": "BUILD",
      "tools": ["FastAPI", "SQLite", "Python"],
      "objectives": [
        "Create a /chat API endpoint for the healthcare chatbot",
        "Integrate retrieval, function calling, and LLM response generation",
        "Implement session-based conversation management",
        "Build a conversation history endpoint",
        "Test the complete backend API using Postman or cURL"
      ]
    },
    {
      "day": 17, "title": "Chatbot Frontend Development", "type": "BUILD",
      "tools": ["Streamlit", "Requests", "UUID"],
      "objectives": [
        "Build an interactive chat interface for the chatbot",
        "Connect the frontend to the backend chat API",
        "Maintain conversation history across user interactions",
        "Add a healthcare plan selector and new conversation option",
        "Validate end-to-end communication between frontend and backend"
      ]
    },
    {
      "day": 18, "title": "Full-Stack Integration & Streaming Responses", "type": "BUILD",
      "tools": ["FastAPI", "StreamingResponse", "Server-Sent Events", "Streamlit"],
      "objectives": [
        "Implement real-time streaming responses from the LLM",
        "Display generated tokens incrementally in the chat interface",
        "Add loading indicators for a better user experience",
        "Handle interrupted or failed streaming requests gracefully",
        "Verify smooth end-to-end streaming between backend and frontend"
      ]
    },
    {
      "day": 19, "title": "Response Formatting & Rich Outputs", "type": "BUILD",
      "tools": ["Pydantic", "Markdown", "Streamlit"],
      "objectives": [
        "Add citations to chatbot responses using retrieved knowledge",
        "Create structured cards for claims and coverage summaries",
        "Render Markdown content with tables, lists, and formatting",
        "Validate structured outputs before displaying them",
        "Improve chatbot readability and response trustworthiness"
      ]
    },
    {
      "day": 20, "title": "Conversation Memory & Context Management", "type": "SHIP_IT",
      "tools": ["SQLite", "FastAPI", "LLM", "Token Management"],
      "objectives": [
        "Persist conversation history across multiple user sessions",
        "Build context-aware conversations using previous messages",
        "Implement automatic conversation summarization for long chats",
        "Manage token limits while preserving important context",
        "Ensure the chatbot remembers user preferences throughout a conversation"
      ]
    },
    {
      "day": 21, "title": "Agentic Frameworks: LangChain Agents & Tool Use", "type": "BUILD",
      "tools": ["LangChain", "LangChain Agents", "ReAct", "Python"],
      "objectives": [
        "Convert function-calling workflows into a reasoning agent",
        "Wrap chatbot capabilities as reusable LangChain tools",
        "Build a ReAct agent capable of selecting the correct tool automatically",
        "Analyze reasoning traces to understand agent decision making",
        "Evaluate whether the agent chooses the right tools for healthcare queries"
      ]
    },
    {
      "day": 22, "title": "Multi-Agent Orchestration", "type": "BUILD",
      "tools": ["CrewAI", "LangGraph", "Python"],
      "objectives": [
        "Create specialized agents for different healthcare domains",
        "Build a router agent that delegates requests to the correct specialist",
        "Implement a complete multi-agent workflow",
        "Compare multi-agent performance with a single-agent architecture",
        "Identify scenarios where multiple agents provide measurable benefits"
      ]
    },
    {
      "day": 23, "title": "Model Context Protocol (MCP)", "type": "BUILD",
      "tools": ["MCP Python SDK", "Claude Desktop", "Cline", "Python"],
      "objectives": [
        "Understand the purpose of the Model Context Protocol",
        "Build an MCP server exposing healthcare chatbot tools",
        "Connect the MCP server to an MCP-compatible client",
        "Expose multiple chatbot capabilities through standardized MCP tools",
        "Verify successful tool execution through live MCP interactions"
      ]
    },
    {
      "day": 24, "title": "Agentic Chatbot Integration", "type": "SHIP_IT",
      "tools": ["LangChain", "MCP", "FastAPI", "Python"],
      "objectives": [
        "Integrate agents, MCP tools, retrieval, and conversation memory",
        "Replace mock tools with live MCP-powered tool calls",
        "Implement retries, timeouts, and graceful error handling",
        "Perform failure testing to validate chatbot reliability",
        "Build a production-style agentic chatbot pipeline"
      ]
    },
    {
      "day": 25, "title": "Chatbot Evaluation & Testing", "type": "SHIP_IT",
      "tools": ["Python", "Evaluation Dataset", "Automated Testing"],
      "objectives": [
        "Create a benchmark dataset covering representative healthcare questions",
        "Evaluate chatbot responses for accuracy, grounding, and consistency",
        "Measure retrieval quality and end-to-end response performance",
        "Identify common failure cases and document improvement areas",
        "Establish baseline metrics before production deployment"
      ]
    },
    {
      "day": 26, "title": "Performance Optimization & Cost Management", "type": "OPTIMIZE",
      "tools": ["tiktoken", "Python", "FastAPI"],
      "objectives": [
        "Measure token usage across the chatbot pipeline",
        "Optimize retrieval and prompt size to reduce latency and cost",
        "Implement response caching for repeated queries",
        "Benchmark response time before and after optimization",
        "Document performance improvements using measurable metrics"
      ]
    },
    {
      "day": 27, "title": "Security, Privacy & Guardrails", "type": "BUILD",
      "tools": ["FastAPI", "Python", "Authentication", "Input Validation"],
      "objectives": [
        "Secure chatbot APIs against unauthorized access",
        "Validate and sanitize user inputs before processing",
        "Protect sensitive healthcare information throughout the pipeline",
        "Implement prompt-injection and jailbreak safeguards",
        "Test common security scenarios and document mitigation strategies"
      ]
    },
    {
      "day": 28, "title": "Docker & Kubernetes Deployment", "type": "SHIP_IT",
      "tools": ["Docker", "Kubernetes", "FastAPI", "React"],
      "objectives": [
        "Containerize the chatbot backend and frontend using Docker",
        "Deploy the application to a Kubernetes cluster",
        "Configure health checks and environment variables",
        "Verify the deployed chatbot functions correctly",
        "Prepare the application for production hosting"
      ]
    },
    {
      "day": 29, "title": "Monitoring, Logging & Observability", "type": "BUILD",
      "tools": ["Python Logging", "Prometheus", "Grafana"],
      "objectives": [
        "Add structured logging throughout the chatbot pipeline",
        "Monitor API performance and chatbot usage",
        "Track failures, latency, and tool execution metrics",
        "Build dashboards for production observability",
        "Use monitoring insights to improve chatbot reliability"
      ]
    },
    {
      "day": 30, "title": "Production Readiness & Final Testing", "type": "SHIP_IT",
      "tools": ["FastAPI", "Docker", "Kubernetes", "Python"],
      "objectives": [
        "Perform complete end-to-end testing of the chatbot",
        "Validate retrieval, agent workflows, and frontend integration",
        "Fix production issues discovered during testing",
        "Complete deployment and operational documentation",
        "Prepare the chatbot for real-world production usage"
      ]
    },
    {
      "day": 31, "title": "Capstone Project & Final Demo", "type": "CAPSTONE",
      "tools": ["FastAPI", "React", "LangChain", "MCP", "Docker", "Kubernetes"],
      "objectives": [
        "Demonstrate the complete enterprise healthcare chatbot",
        "Showcase retrieval, RAG, agents, MCP, and conversation memory",
        "Present the deployed application with production architecture",
        "Evaluate the chatbot using real-world scenarios",
        "Publish the final project with source code and documentation"
      ]
    }
  ]
}
```

---

### data/candidates.json — ALL 20 REAL CANDIDATE PROFILES (verbatim)

```json
{
  "candidates": [
    {
      "member": { "id": "CAND-001", "name": "Sarah Johnson", "jobRole": "Senior Data Engineer", "yearsExperience": 9, "education": "MS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 1 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 1 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 2 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 4 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 2 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 2 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 3 },
        { "day": 29, "title": "Monitoring, Logging & Observability", "skipped": true },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 28, "missionsCompleted": 30, "missionsFirstTry": 20 }
    },
    {
      "member": { "id": "CAND-002", "name": "Alex Turner", "jobRole": "Backend Software Engineer", "yearsExperience": 5, "education": "B.Tech Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 3 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 2 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 4 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 5 },
        { "day": 13, "title": "Function Calling & Structured Outputs", "passed": true, "attempts": 4 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 1 },
        { "day": 18, "title": "Streaming Responses", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 3 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 2 }
      ],
      "signals": { "commitDays": 22, "missionsCompleted": 29, "missionsFirstTry": 10 }
    },
    {
      "member": { "id": "CAND-003", "name": "Emily Chen", "jobRole": "AI Engineer", "yearsExperience": 6, "education": "MS Artificial Intelligence", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 1 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 1 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 1 },
        { "day": 11, "title": "RAG End-to-End & LLM API Basics", "passed": true, "attempts": 1 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 1 },
        { "day": 13, "title": "Function Calling & Structured Outputs", "passed": true, "attempts": 1 },
        { "day": 21, "title": "LangChain Agents", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 1 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 31, "missionsCompleted": 31, "missionsFirstTry": 30 }
    },
    {
      "member": { "id": "CAND-004", "name": "David Miller", "jobRole": "Business Analyst", "yearsExperience": 8, "education": "MBA", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 4 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 5 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 5 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 3 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 2 },
        { "day": 20, "title": "Conversation Memory & Context Management", "passed": true, "attempts": 3 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 4 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 5 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "skipped": true },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 2 }
      ],
      "signals": { "commitDays": 18, "missionsCompleted": 28, "missionsFirstTry": 6 }
    },
    {
      "member": { "id": "CAND-005", "name": "Michael Brown", "jobRole": "DevOps Engineer", "yearsExperience": 10, "education": "B.Tech Information Technology", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 2 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 2 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 2 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 4 },
        { "day": 18, "title": "Streaming Responses", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 2 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 3 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 1 },
        { "day": 29, "title": "Monitoring, Logging & Observability", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 30, "missionsCompleted": 31, "missionsFirstTry": 22 }
    },
    {
      "member": { "id": "CAND-006", "name": "Wendy Foster", "jobRole": "Marketing Manager", "yearsExperience": 12, "education": "BA Marketing", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 3 },
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 5 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 5 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 4 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 4 },
        { "day": 17, "title": "Chatbot Frontend Development", "passed": true, "attempts": 2 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 5 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "skipped": true },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "skipped": true },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 3 }
      ],
      "signals": { "commitDays": 19, "missionsCompleted": 24, "missionsFirstTry": 2 }
    },
    {
      "member": { "id": "CAND-007", "name": "Ethan Brooks", "jobRole": "Computer Science Intern", "yearsExperience": 0, "education": "BS Computer Science (in progress)", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 1 },
        { "day": 3, "title": "First AI Project, React Frontend & GitHub", "passed": true, "attempts": 1 },
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 2 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 1 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 1 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 1 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "skipped": true },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "skipped": true },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 2 }
      ],
      "signals": { "commitDays": 26, "missionsCompleted": 27, "missionsFirstTry": 22 }
    },
    {
      "member": { "id": "CAND-008", "name": "Harold Whitfield", "jobRole": "Distinguished Engineer", "yearsExperience": 28, "education": "BS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 1 },
        { "day": 4, "title": "Reading & Processing Structured Data", "passed": true, "attempts": 1 },
        { "day": 5, "title": "Reading & Processing Unstructured Data", "passed": true, "attempts": 1 },
        { "day": 14, "title": "Fine-Tuning: Concepts & When to Use It", "skipped": true },
        { "day": 15, "title": "Fine-Tuning: Hands-On with LoRA & QLoRA", "skipped": true },
        { "day": 21, "title": "LangChain Agents", "passed": true, "attempts": 5 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 4 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 5 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "passed": true, "attempts": 1 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 2 }
      ],
      "signals": { "commitDays": 25, "missionsCompleted": 27, "missionsFirstTry": 15 }
    },
    {
      "member": { "id": "CAND-009", "name": "Zara Ahmadi", "jobRole": "AI Engineer", "yearsExperience": 1, "education": "BS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 1 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 1 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 1 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 1 },
        { "day": 13, "title": "Function Calling & Structured Outputs", "passed": true, "attempts": 1 },
        { "day": 21, "title": "LangChain Agents", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 1 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 1 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 31, "missionsCompleted": 31, "missionsFirstTry": 29 }
    },
    {
      "member": { "id": "CAND-010", "name": "Gerald Combs", "jobRole": "IT Support Specialist", "yearsExperience": 20, "education": "AAS Information Technology", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 2 },
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 5 },
        { "day": 8, "title": "Vector Databases Overview", "passed": false, "attempts": 4 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": false, "attempts": 3 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 5 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 4 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": false, "attempts": 3 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "skipped": true },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "skipped": true },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 3 }
      ],
      "signals": { "commitDays": 22, "missionsCompleted": 23, "missionsFirstTry": 1 }
    },
    {
      "member": { "id": "CAND-011", "name": "Mia Alvarez", "jobRole": "UX Researcher", "yearsExperience": 6, "education": "MA Human-Computer Interaction", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 2 },
        { "day": 2, "title": "Local LLM & AI Coding Assistant Setup", "passed": true, "attempts": 1 },
        { "day": 3, "title": "First AI Project, React Frontend & GitHub", "passed": true, "attempts": 3 },
        { "day": 4, "title": "Reading & Processing Structured Data", "passed": true, "attempts": 2 },
        { "day": 7, "title": "Embeddings Explained", "skipped": true },
        { "day": 8, "title": "Vector Databases Overview", "skipped": true },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "skipped": true },
        { "day": 16, "title": "Chatbot Backend & API Integration", "skipped": true },
        { "day": 22, "title": "Multi-Agent Orchestration", "skipped": true },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 4 }
      ],
      "signals": { "commitDays": 9, "missionsCompleted": 14, "missionsFirstTry": 5 }
    },
    {
      "member": { "id": "CAND-012", "name": "Chen Wei", "jobRole": "Mobile App Developer", "yearsExperience": 7, "education": "BS Computer Engineering", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 4 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 5 },
        { "day": 9, "title": "Building & Populating the Vector Database", "passed": true, "attempts": 4 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 4 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 1 },
        { "day": 18, "title": "Streaming Responses", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 2 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 1 },
        { "day": 30, "title": "Production Readiness & Final Testing", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 27, "missionsCompleted": 30, "missionsFirstTry": 14 }
    },
    {
      "member": { "id": "CAND-013", "name": "Ravi Patel", "jobRole": "Software Engineer", "yearsExperience": 15, "education": "MS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 3 },
        { "day": 4, "title": "Reading & Processing Structured Data", "passed": true, "attempts": 2 },
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 3 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 2 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 3 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 2 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 2 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "passed": true, "attempts": 1 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 27, "missionsCompleted": 30, "missionsFirstTry": 13 }
    },
    {
      "member": { "id": "CAND-014", "name": "Bethany Cole", "jobRole": "HR Manager", "yearsExperience": 10, "education": "BA Human Resources", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 4 },
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 5 },
        { "day": 8, "title": "Vector Databases Overview", "skipped": true },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 5 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 4 },
        { "day": 20, "title": "Conversation Memory & Context Management", "passed": true, "attempts": 3 },
        { "day": 22, "title": "Multi-Agent Orchestration", "skipped": true },
        { "day": 27, "title": "Security, Privacy & Guardrails", "skipped": true },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "skipped": true },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 4 }
      ],
      "signals": { "commitDays": 17, "missionsCompleted": 20, "missionsFirstTry": 1 }
    },
    {
      "member": { "id": "CAND-015", "name": "Noah Kim", "jobRole": "Principal Architect", "yearsExperience": 20, "education": "MS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 1 },
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 1 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 1 },
        { "day": 14, "title": "Fine-Tuning: Concepts & When to Use It", "skipped": true },
        { "day": 15, "title": "Fine-Tuning: Hands-On with LoRA & QLoRA", "skipped": true },
        { "day": 21, "title": "LangChain Agents", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 1 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 1 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 29, "missionsCompleted": 29, "missionsFirstTry": 27 }
    },
    {
      "member": { "id": "CAND-016", "name": "Isabella Rossi", "jobRole": "Software Engineer", "yearsExperience": 5, "education": "BS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 2 },
        { "day": 7, "title": "Embeddings Explained", "passed": false, "attempts": 4 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 3 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": false, "attempts": 5 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 2 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": false, "attempts": 4 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "skipped": true },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "skipped": true },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 2 }
      ],
      "signals": { "commitDays": 19, "missionsCompleted": 21, "missionsFirstTry": 2 }
    },
    {
      "member": { "id": "CAND-017", "name": "Tyler Brooks", "jobRole": "Junior Developer", "yearsExperience": 0, "education": "GED + Coding Bootcamp Certificate", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 3 },
        { "day": 3, "title": "First AI Project, React Frontend & GitHub", "passed": true, "attempts": 5 },
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 5 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 5 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 5 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 5 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 4 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 5 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 4 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 3 }
      ],
      "signals": { "commitDays": 30, "missionsCompleted": 31, "missionsFirstTry": 1 }
    },
    {
      "member": { "id": "CAND-018", "name": "Diane Foster", "jobRole": "AI Engineer", "yearsExperience": 4, "education": "MS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 1 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 1 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": true, "attempts": 1 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 1 },
        { "day": 13, "title": "Function Calling & Structured Outputs", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 1 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 1 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "passed": true, "attempts": 1 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 31, "missionsCompleted": 31, "missionsFirstTry": 31 }
    },
    {
      "member": { "id": "CAND-019", "name": "Frank DeLuca", "jobRole": "Legacy Systems Engineer", "yearsExperience": 25, "education": "BS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 2 },
        { "day": 4, "title": "Reading & Processing Structured Data", "passed": true, "attempts": 1 },
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 4 },
        { "day": 8, "title": "Vector Databases Overview", "passed": true, "attempts": 3 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 1 },
        { "day": 17, "title": "Chatbot Frontend Development", "passed": true, "attempts": 5 },
        { "day": 19, "title": "Response Formatting & Rich Outputs", "passed": true, "attempts": 4 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 3 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 2 }
      ],
      "signals": { "commitDays": 26, "missionsCompleted": 29, "missionsFirstTry": 11 }
    },
    {
      "member": { "id": "CAND-020", "name": "Priyanka Sharma", "jobRole": "Software Engineer", "yearsExperience": 5, "education": "BS Computer Science", "status": "COMPLETED" },
      "missions": [
        { "day": 1, "title": "VS Code & Python Environment Setup", "passed": true, "attempts": 1 },
        { "day": 3, "title": "First AI Project, React Frontend & GitHub", "passed": true, "attempts": 1 },
        { "day": 4, "title": "Reading & Processing Structured Data", "skipped": true },
        { "day": 7, "title": "Embeddings Explained", "passed": false, "attempts": 2 },
        { "day": 8, "title": "Vector Databases Overview", "skipped": true },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": true, "attempts": 1 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 1 },
        { "day": 27, "title": "Security, Privacy & Guardrails", "passed": true, "attempts": 1 },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 24, "missionsCompleted": 27, "missionsFirstTry": 19 }
    }
  ]
}
```

---

## 📐 TYPESCRIPT TYPES (types/index.ts)

```typescript
// ─── Curriculum ───────────────────────────────────────────────────────────────
export interface CurriculumDay {
  day: number;
  title: string;
  type: "SETUP" | "BUILD" | "AI_CORE" | "LEARN" | "SHIP_IT" | "OPTIMIZE" | "CAPSTONE";
  tools: string[];
  objectives: string[];
}

export interface CurriculumModule {
  n: number;
  title: string;
  days: [number, number]; // [startDay, endDay] inclusive
}

export interface Curriculum {
  cohort: string;
  modules: CurriculumModule[];
  days: CurriculumDay[];
}

// ─── Candidate ────────────────────────────────────────────────────────────────
export interface CandidateMember {
  id: string;
  name: string;
  jobRole: string;
  yearsExperience: number;
  education: string;
  status: "COMPLETED" | "IN_PROGRESS";
}

export interface Mission {
  day: number;
  title: string;
  passed?: boolean;
  skipped?: boolean;
  attempts?: number;
}

export interface CandidateSignals {
  commitDays: number;
  missionsCompleted: number;
  missionsFirstTry: number;
}

export interface Candidate {
  member: CandidateMember;
  missions: Mission[];
  signals: CandidateSignals;
}

export interface CandidatesFile {
  candidates: Candidate[];
}

// ─── Session ──────────────────────────────────────────────────────────────────
export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface InterviewMessage {
  role: "interviewer" | "candidate";
  content: string;
  timestamp: string;
  dayReference?: number;
  questionType?: "opening" | "technical" | "follow_up" | "probing" | "synthesis" | "closing";
}

export interface InterviewSession {
  sessionId: string;
  candidateId: string;
  candidate: Candidate;
  createdAt: number;           // Date.now()
  lastActivityAt: number;
  status: "active" | "completed" | "expired";
  messages: InterviewMessage[];   // Full display transcript
  groqHistory: ChatMessage[];     // Sent to Groq — rolling window of last 12
  questionsAsked: number;
  daysCovered: Set<number>;
  currentDayFocus?: number;
  interviewComplete: boolean;
  feedback?: FeedbackReport;
}

// ─── API Contract (from technical-spec.md — use EXACTLY) ─────────────────────

// Start Interview Request (first call — no message field)
export interface StartInterviewRequest {
  sessionId: string;
  candidate: Candidate;         // Full candidate object from candidates.json
}

// Conversation Turn Request (subsequent calls)
export interface TurnRequest {
  sessionId: string;
  message: string;              // Candidate's response text
}

// Union type for route handler
export type InterviewRequest = StartInterviewRequest | TurnRequest;

// Response for ongoing interview (done: false)
export interface OngoingInterviewResponse {
  reply: string;
  done: false;
}

// Response when interview is complete (done: true)
export interface CompletedInterviewResponse {
  reply: string;
  done: true;
  feedback: {
    summary: string;
    strengths: string[];
    gaps: string[];
    next: string[];
  };
}

export type InterviewResponse = OngoingInterviewResponse | CompletedInterviewResponse;

// ─── Feedback ─────────────────────────────────────────────────────────────────
export interface FeedbackReport {
  summary: string;
  strengths: string[];
  gaps: string[];
  next: string[];
  // Extended fields for the UI (not part of the API contract)
  overallScore?: number;
  topicScores?: { topic: string; day: number; score: number; note: string }[];
  recommendation?: "strong_hire" | "hire" | "consider" | "needs_growth";
}
```

---

## ⚙️ BACKEND IMPLEMENTATION

### lib/groq.ts — Groq Client

```typescript
import Groq from "groq-sdk";

// Initialize once — reuse across all requests
const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY!,
});

export const GROQ_MODEL = process.env.GROQ_MODEL || "llama-3.3-70b-versatile";

/**
 * Send a chat completion request to Groq.
 * @param messages  Full message history to send
 * @param temperature  0.0–1.0, use 0.7 for interviews, 0.1 for feedback
 * @param maxTokens  Token limit for the response
 */
export async function groqChat(
  messages: { role: "system" | "user" | "assistant"; content: string }[],
  temperature = 0.7,
  maxTokens = 1024
): Promise<string> {
  const completion = await groq.chat.completions.create({
    model: GROQ_MODEL,
    messages,
    temperature,
    max_tokens: maxTokens,
  });
  return completion.choices[0]?.message?.content ?? "";
}

export default groq;
```

---

### lib/session.ts — In-Memory Session Store

```typescript
import { InterviewSession } from "@/types";

// Global session map — survives across API calls within the same process
const sessions = new Map<string, InterviewSession>();

const SESSION_TIMEOUT_MS = parseInt(process.env.SESSION_TIMEOUT_MS || "7200000");

export function createSession(sessionId: string, candidate: Candidate): InterviewSession {
  const session: InterviewSession = {
    sessionId,
    candidateId: candidate.member.id,
    candidate,
    createdAt: Date.now(),
    lastActivityAt: Date.now(),
    status: "active",
    messages: [],
    groqHistory: [],
    questionsAsked: 0,
    daysCovered: new Set(),
    interviewComplete: false,
  };
  sessions.set(sessionId, session);
  return session;
}

export function getSession(sessionId: string): InterviewSession | null {
  const session = sessions.get(sessionId);
  if (!session) return null;

  // Check expiry
  if (Date.now() - session.lastActivityAt > SESSION_TIMEOUT_MS) {
    session.status = "expired";
    return null;
  }

  return session;
}

export function updateSession(session: InterviewSession): void {
  session.lastActivityAt = Date.now();
  sessions.set(session.sessionId, session);
}

export function getAllSessions(): InterviewSession[] {
  return Array.from(sessions.values());
}
```

---

### lib/curriculum.ts — Curriculum Helpers

```typescript
import curriculumData from "@/data/curriculum.json";
import { Curriculum, CurriculumDay, CurriculumModule } from "@/types";

const curriculum = curriculumData as Curriculum;

export function getCurriculum(): Curriculum {
  return curriculum;
}

export function getDayInfo(dayNumber: number): CurriculumDay | undefined {
  return curriculum.days.find((d) => d.day === dayNumber);
}

export function getModuleForDay(dayNumber: number): CurriculumModule | undefined {
  return curriculum.modules.find(
    (m) => dayNumber >= m.days[0] && dayNumber <= m.days[1]
  );
}

/**
 * Build a summary string of a day's context for use in prompts.
 */
export function formatDayContext(dayNumber: number): string {
  const day = getDayInfo(dayNumber);
  if (!day) return "";
  const module = getModuleForDay(dayNumber);
  return `Day ${day.day} — "${day.title}" (Module: ${module?.title ?? "Unknown"})
  Tools: ${day.tools.join(", ")}
  Learning Objectives:
  ${day.objectives.map((o) => `  • ${o}`).join("\n")}`;
}
```

---

### lib/candidates.ts — Candidate Helpers

```typescript
import candidatesData from "@/data/candidates.json";
import { Candidate, CandidatesFile, Mission } from "@/types";

const data = candidatesData as CandidatesFile;

export function getAllCandidates(): Candidate[] {
  return data.candidates;
}

export function getCandidateById(id: string): Candidate | undefined {
  return data.candidates.find((c) => c.member.id === id);
}

/**
 * Get only the missions where passed === true (exclude skipped and failed).
 * These are the ONLY missions we can interview about.
 */
export function getPassedMissions(candidate: Candidate): Mission[] {
  return candidate.missions.filter((m) => m.passed === true);
}

/**
 * Get missions that were difficult (high attempts) — these are
 * interesting topics to probe deeper on.
 */
export function getDifficultMissions(candidate: Candidate): Mission[] {
  return candidate.missions.filter(
    (m) => m.passed === true && (m.attempts ?? 1) >= 3
  );
}

/**
 * Get skipped or failed missions — do NOT interview about these.
 */
export function getExcludedDays(candidate: Candidate): number[] {
  return candidate.missions
    .filter((m) => m.skipped === true || m.passed === false)
    .map((m) => m.day);
}

/**
 * Derive a "difficulty" label for use in the system prompt.
 * missions with attempts >= 4 were clearly hard for the candidate.
 */
export function getMissionDifficultyLabel(mission: Mission): string {
  const a = mission.attempts ?? 1;
  if (a === 1) return "mastered on first try";
  if (a === 2) return "required one retry";
  if (a === 3) return "needed multiple attempts";
  if (a >= 4) return "very challenging — struggled significantly";
  return "completed";
}

/**
 * Compute overall engagement score from signals.
 */
export function computeEngagementScore(candidate: Candidate): number {
  const { commitDays, missionsCompleted, missionsFirstTry } = candidate.signals;
  return Math.round(
    (commitDays / 31) * 40 +
    (missionsCompleted / 31) * 40 +
    (missionsFirstTry / Math.max(missionsCompleted, 1)) * 20
  );
}
```

---

### lib/prompts.ts — System Prompt Builder

```typescript
import { Candidate, InterviewSession } from "@/types";
import { formatDayContext } from "./curriculum";
import {
  getPassedMissions,
  getDifficultMissions,
  getExcludedDays,
  getMissionDifficultyLabel,
  computeEngagementScore,
} from "./candidates";

export function buildSystemPrompt(candidate: Candidate): string {
  const passed = getPassedMissions(candidate);
  const difficult = getDifficultMissions(candidate);
  const excluded = getExcludedDays(candidate);
  const engagement = computeEngagementScore(candidate);
  const { member, signals } = candidate;

  // Build the passed missions context with full curriculum detail
  const passedMissionsContext = passed
    .map((m) => {
      const dayCtx = formatDayContext(m.day);
      const difficulty = getMissionDifficultyLabel(m);
      return `--- Day ${m.day}: "${m.title}" [${difficulty}] ---\n${dayCtx}`;
    })
    .join("\n\n");

  const difficultTopics = difficult
    .map((m) => `  • Day ${m.day}: "${m.title}" (${m.attempts} attempts)`)
    .join("\n");

  const excludedDaysStr = excluded.length
    ? excluded.map((d) => `Day ${d}`).join(", ")
    : "None";

  return `You are Alex, a senior AI engineer conducting a real technical interview for a candidate who completed the ABTalks AI Cohort — a 31-day enterprise AI engineering program.

═══════════════════════════════════════════════
CANDIDATE PROFILE
═══════════════════════════════════════════════
Name: ${member.name}
Role: ${member.jobRole}
Experience: ${member.yearsExperience} year(s)
Education: ${member.education}
Cohort Engagement Score: ${engagement}/100
Commit Days: ${signals.commitDays}/31
Missions Completed: ${signals.missionsCompleted}/31
Passed on First Try: ${signals.missionsFirstTry}

═══════════════════════════════════════════════
MISSIONS THEY PASSED (ONLY ask about these)
═══════════════════════════════════════════════
${passedMissionsContext}

═══════════════════════════════════════════════
TOPICS THEY STRUGGLED WITH (prioritize probing)
═══════════════════════════════════════════════
${difficultTopics || "  None — performed well across the board"}

═══════════════════════════════════════════════
DO NOT ASK ABOUT THESE (skipped or failed)
═══════════════════════════════════════════════
${excludedDaysStr}

═══════════════════════════════════════════════
INTERVIEW RULES — FOLLOW EXACTLY
═══════════════════════════════════════════════
1. Ask EXACTLY ONE question per message. Never list multiple questions.
2. ONLY ask about days listed in "MISSIONS THEY PASSED". Never ask about excluded days.
3. Reference the specific tools and learning objectives from the curriculum when forming questions.
4. After each candidate response, analyze it and either:
   a. Ask a targeted follow-up if the answer was shallow, vague, or contained an error
   b. Acknowledge the answer naturally and move to the next topic
5. Maintain full context of what has already been asked — never repeat a topic.
6. Adapt the difficulty: if ${member.name} is struggling, ask simpler follow-ups. If they excel, go deeper.
7. Use natural, conversational transitions between questions (e.g., "That's interesting — building on that...", "Great. Let's shift to...")
8. Never reveal scores or evaluation criteria during the interview.
9. Keep your messages focused and under 100 words per message.
10. Use the candidate's first name occasionally to keep it natural.

═══════════════════════════════════════════════
QUESTION STRATEGY
═══════════════════════════════════════════════
• Q1-2: Start with topics they passed easily (attempts=1) to build confidence
• Q3-6: Core technical topics from their passed missions — mix of conceptual and applied
• Q7-9: Probe the topics they struggled with (high attempt count)
• Q10+: Synthesis questions combining multiple concepts they covered
• MINIMUM: 8 questions covering at least 4 different days
• MAXIMUM: 14 questions total — don't fatigue the candidate

QUESTION TYPES TO USE:
- Conceptual: "Explain how [X] works in the context of the project you built..."
- Applied: "Walk me through how you used [tool] on Day [N]..."
- Comparative: "What's the difference between [X] and [Y], and when would you choose each?"
- Scenario: "If [real-world scenario], how would you approach it given what you learned?"
- Debug: "A teammate reports that [specific issue]. What would you investigate first?"
- Synthesis: "You used both [tool A from day X] and [tool B from day Y] — how do they complement each other?"

═══════════════════════════════════════════════
ENDING THE INTERVIEW
═══════════════════════════════════════════════
When you have asked 8+ questions covering 4+ different days AND feel you have a thorough picture, naturally close:

"That brings us to the end of our session, ${member.name}. Thank you for your thoughtful answers — you'll receive your detailed feedback shortly."

Then on a new line, output EXACTLY: [INTERVIEW_COMPLETE]

Do NOT output [INTERVIEW_COMPLETE] until you have satisfied the minimum question and day requirements.`;
}

export function buildFeedbackPrompt(session: InterviewSession): string {
  const { candidate } = session;
  const transcript = session.messages
    .filter((m) => m.role !== "system")
    .map((m) => `${m.role === "interviewer" ? "INTERVIEWER" : "CANDIDATE"}: ${m.content}`)
    .join("\n\n");

  const coveredDays = Array.from(session.daysCovered);

  return `You are evaluating a completed technical interview transcript for a candidate who finished the ABTalks AI Cohort.

CANDIDATE: ${candidate.member.name} (${candidate.member.jobRole}, ${candidate.member.yearsExperience} yrs experience)
DAYS COVERED IN INTERVIEW: ${coveredDays.join(", ")}
TOTAL QUESTIONS ASKED: ${session.questionsAsked}

FULL INTERVIEW TRANSCRIPT:
${transcript}

Based on the transcript above, produce a JSON feedback report. Evaluate ONLY based on what was said in the transcript — do not invent information.

Return ONLY valid JSON with this exact structure:
{
  "summary": "3-4 sentence paragraph summarizing the candidate's overall performance, communication clarity, and technical depth",
  "strengths": [
    "Specific strength with a brief example from their actual answer (3-5 items)",
    "...",
    "..."
  ],
  "gaps": [
    "Specific knowledge gap or area where the answer was incomplete or incorrect (2-4 items)",
    "...",
    "..."
  ],
  "next": [
    "Concrete, actionable next step tied to a specific topic from the interview (3-5 items)",
    "...",
    "..."
  ],
  "overallScore": 78,
  "recommendation": "hire",
  "topicScores": [
    { "topic": "Day 7: Embeddings Explained", "day": 7, "score": 8, "note": "brief assessment note" },
    ...
  ]
}

Scoring guidelines:
- overallScore: 0–100 (weighted average of topic scores)
- recommendation: "strong_hire" (90+), "hire" (75–89), "consider" (60–74), "needs_growth" (<60)
- topicScores[].score: 0–10 per topic covered

Be specific and honest. Reference actual things the candidate said.`;
}
```

---

### lib/agent.ts — Core Interview Agent Logic

```typescript
import { InterviewSession, Candidate, InterviewMessage } from "@/types";
import { groqChat } from "./groq";
import { buildSystemPrompt, buildFeedbackPrompt } from "./prompts";
import { createSession, getSession, updateSession } from "./session";
import { generateFeedback } from "./feedback";
import { getPassedMissions } from "./candidates";

const MIN_QUESTIONS = parseInt(process.env.MIN_QUESTIONS_REQUIRED || "8");
const MIN_DAYS = parseInt(process.env.MIN_DAYS_REQUIRED || "4");
const MAX_QUESTIONS = parseInt(process.env.MAX_QUESTIONS_PER_SESSION || "14");

/**
 * Initialize a brand new interview session.
 * Called when the request has no prior session history (start interview).
 */
export async function startInterview(
  sessionId: string,
  candidate: Candidate
): Promise<{ reply: string; session: InterviewSession }> {
  const session = createSession(sessionId, candidate);

  // Build the system prompt with full candidate context
  const systemPrompt = buildSystemPrompt(candidate);

  // Initialize Groq history with system prompt
  session.groqHistory = [
    { role: "system", content: systemPrompt },
    {
      role: "user",
      content: `Please begin the interview. Greet ${candidate.member.name} professionally, introduce yourself as Alex, mention this is a technical interview covering their ABTalks AI Cohort work, and ask your first question.`,
    },
  ];

  // Get opening from Groq
  const reply = await groqChat(session.groqHistory, 0.7, 400);

  // Add assistant reply to history
  session.groqHistory.push({ role: "assistant", content: reply });

  // Track in display messages
  session.messages.push({
    role: "interviewer",
    content: reply,
    timestamp: new Date().toISOString(),
    questionType: "opening",
  });

  session.questionsAsked = 1;
  updateSession(session);

  return { reply, session };
}

/**
 * Process a candidate's response and generate the next interviewer message.
 */
export async function processResponse(
  session: InterviewSession,
  candidateMessage: string
): Promise<{ reply: string; done: boolean; session: InterviewSession }> {
  // Record candidate message in display transcript
  session.messages.push({
    role: "candidate",
    content: candidateMessage,
    timestamp: new Date().toISOString(),
  });

  // Add candidate response to Groq history
  session.groqHistory.push({ role: "user", content: candidateMessage });

  // Keep Groq history bounded — system prompt + last 12 messages
  if (session.groqHistory.length > 13) {
    const systemMsg = session.groqHistory[0]; // always keep system prompt
    session.groqHistory = [systemMsg, ...session.groqHistory.slice(-12)];
  }

  // Get next interviewer message from Groq
  const rawReply = await groqChat(session.groqHistory, 0.7, 600);

  // Check if the interview is signaling completion
  const isComplete =
    rawReply.includes("[INTERVIEW_COMPLETE]") &&
    session.questionsAsked >= MIN_QUESTIONS &&
    session.daysCovered.size >= MIN_DAYS;

  // Strip the completion marker from the displayed message
  const cleanReply = rawReply.replace("[INTERVIEW_COMPLETE]", "").trim();

  // Parse which day was just covered (look for "Day X" in the reply)
  const dayMatch = rawReply.match(/Day (\d+)/i);
  if (dayMatch) {
    session.daysCovered.add(parseInt(dayMatch[1]));
  }

  // Add to Groq history
  session.groqHistory.push({ role: "assistant", content: cleanReply });

  // Add to display messages
  session.messages.push({
    role: "interviewer",
    content: cleanReply,
    timestamp: new Date().toISOString(),
    questionType: isComplete ? "closing" : "technical",
  });

  session.questionsAsked += 1;

  if (isComplete) {
    session.interviewComplete = true;
    session.status = "completed";
  }

  updateSession(session);
  return { reply: cleanReply, done: isComplete, session };
}

/**
 * Force-check completion: used if the candidate has been going for too long.
 */
export function shouldForceComplete(session: InterviewSession): boolean {
  return session.questionsAsked >= MAX_QUESTIONS;
}
```

---

### lib/feedback.ts — Feedback Generator

```typescript
import { InterviewSession } from "@/types";
import { groqChat } from "./groq";
import { buildFeedbackPrompt } from "./prompts";

export async function generateFeedback(
  session: InterviewSession
): Promise<{
  summary: string;
  strengths: string[];
  gaps: string[];
  next: string[];
  overallScore?: number;
  recommendation?: string;
  topicScores?: any[];
}> {
  const prompt = buildFeedbackPrompt(session);

  // Use low temperature for deterministic, structured feedback
  const raw = await groqChat(
    [
      { role: "system", content: "You are a technical interview evaluator. Respond with valid JSON only." },
      { role: "user", content: prompt },
    ],
    0.1,  // Very low temperature — we want consistent, grounded feedback
    2000
  );

  // Parse JSON from the response — handle edge cases
  try {
    // Extract JSON from the response (Groq sometimes wraps in markdown code blocks)
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("No JSON found in response");
    return JSON.parse(jsonMatch[0]);
  } catch (e) {
    // Fallback if JSON parsing fails
    console.error("Feedback JSON parse error:", e);
    return {
      summary: raw.slice(0, 500),
      strengths: ["Completed the interview session"],
      gaps: ["Detailed feedback unavailable — please try again"],
      next: ["Review the cohort curriculum materials"],
    };
  }
}
```

---

## 🌐 API ROUTE (app/api/interview/route.ts)

> **This is the required endpoint per technical-spec.md — implement it EXACTLY.**

```typescript
import { NextRequest, NextResponse } from "next/server";
import { startInterview, processResponse } from "@/lib/agent";
import { getSession } from "@/lib/session";
import { generateFeedback } from "@/lib/feedback";

// ─── CORS Headers ─────────────────────────────────────────────────────────────
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: corsHeaders });
}

// ─── POST /api/interview ───────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // ── Validate required fields ──────────────────────────────────────────────
    if (!body.sessionId) {
      return NextResponse.json(
        { error: "sessionId is required" },
        { status: 400, headers: corsHeaders }
      );
    }

    const { sessionId } = body;

    // ── START INTERVIEW: body has { sessionId, candidate } ────────────────────
    if (body.candidate) {
      const { candidate } = body;

      // Validate candidate structure
      if (!candidate?.member?.id || !candidate?.missions) {
        return NextResponse.json(
          { error: "Invalid candidate object — must include member and missions" },
          { status: 400, headers: corsHeaders }
        );
      }

      // Start the interview session
      const { reply } = await startInterview(sessionId, candidate);

      // Per spec: { reply, done: false }
      return NextResponse.json(
        { reply, done: false },
        { status: 200, headers: corsHeaders }
      );
    }

    // ── CONVERSATION TURN: body has { sessionId, message } ───────────────────
    if (typeof body.message === "string") {
      // Retrieve existing session
      const session = getSession(sessionId);
      if (!session) {
        return NextResponse.json(
          { error: "Session not found or expired. Start a new interview." },
          { status: 404, headers: corsHeaders }
        );
      }

      if (session.status === "completed") {
        return NextResponse.json(
          { error: "This interview session is already complete." },
          { status: 400, headers: corsHeaders }
        );
      }

      // Process the candidate's response
      const { reply, done } = await processResponse(session, body.message);

      if (done) {
        // Generate structured feedback
        const feedback = await generateFeedback(session);

        // Per spec: { reply, done: true, feedback: { summary, strengths, gaps, next } }
        return NextResponse.json(
          {
            reply,
            done: true,
            feedback: {
              summary: feedback.summary,
              strengths: feedback.strengths,
              gaps: feedback.gaps,
              next: feedback.next,
            },
          },
          { status: 200, headers: corsHeaders }
        );
      }

      // Per spec: { reply, done: false }
      return NextResponse.json(
        { reply, done: false },
        { status: 200, headers: corsHeaders }
      );
    }

    // ── Neither start nor turn — malformed request ────────────────────────────
    return NextResponse.json(
      { error: "Request must include either 'candidate' (to start) or 'message' (to continue)" },
      { status: 400, headers: corsHeaders }
    );

  } catch (error: any) {
    console.error("[/api/interview] Error:", error?.message ?? error);
    return NextResponse.json(
      { error: "Internal server error", detail: error?.message },
      { status: 500, headers: corsHeaders }
    );
  }
}
```

---

## 🎨 DESIGN SYSTEM (app/globals.css)

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  /* Background layers */
  --bg-primary:   #08080F;
  --bg-secondary: #0F0F1A;
  --bg-card:      #14142B;
  --bg-elevated:  #1C1C3A;

  /* Brand colors */
  --violet:       #7C3AED;
  --violet-light: #9D6FEF;
  --violet-dark:  #5B21B6;
  --cyan:         #06B6D4;
  --cyan-light:   #22D3EE;
  --emerald:      #10B981;
  --amber:        #F59E0B;
  --rose:         #F43F5E;

  /* Gradients */
  --gradient-primary:  linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);
  --gradient-card:     linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(6,182,212,0.05) 100%);
  --gradient-hero:     radial-gradient(ellipse at top left, rgba(124,58,237,0.25) 0%, transparent 60%),
                       radial-gradient(ellipse at bottom right, rgba(6,182,212,0.15) 0%, transparent 60%);

  /* Text */
  --text-primary:   #F1F5F9;
  --text-secondary: #94A3B8;
  --text-muted:     #475569;

  /* Glass effect */
  --glass-bg:     rgba(255, 255, 255, 0.03);
  --glass-border: rgba(255, 255, 255, 0.07);
  --glass-blur:   20px;

  /* Shadows */
  --shadow-violet: 0 0 40px rgba(124, 58, 237, 0.25);
  --shadow-card:   0 8px 32px rgba(0, 0, 0, 0.4);
  --shadow-glow:   0 0 20px rgba(124, 58, 237, 0.4);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  font-family: 'Inter', -apple-system, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--violet); border-radius: 2px; }

/* Glassmorphism card */
.glass-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border-radius: 16px;
}

/* Gradient text */
.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Glow button */
.btn-primary {
  background: var(--gradient-primary);
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-glow);
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(124, 58, 237, 0.6);
}
.btn-primary:active {
  transform: translateY(0);
}

/* Animated gradient background */
.animated-bg {
  background: var(--gradient-hero);
  background-attachment: fixed;
}

/* Chat bubbles */
.bubble-interviewer {
  background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(6,182,212,0.1));
  border: 1px solid rgba(124,58,237,0.3);
  border-radius: 16px 16px 16px 4px;
  padding: 16px 20px;
  max-width: 75%;
  align-self: flex-start;
}

.bubble-candidate {
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--glass-border);
  border-radius: 16px 16px 4px 16px;
  padding: 16px 20px;
  max-width: 75%;
  align-self: flex-end;
}

/* Typing indicator */
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-8px); }
}
.typing-dot {
  width: 8px; height: 8px;
  background: var(--violet-light);
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.16s; }
.typing-dot:nth-child(3) { animation-delay: 0.32s; }

/* Progress bar fill animation */
@keyframes fillBar {
  from { width: 0%; }
  to { width: var(--fill-width); }
}

/* Score counter animation */
@keyframes countUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Candidate card hover */
.candidate-card {
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  cursor: pointer;
}
.candidate-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-violet);
  border-color: var(--violet) !important;
}

/* Fade+slide in animation */
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-in {
  animation: fadeSlideUp 0.35s ease forwards;
}
```

---

## 🖥️ PAGE IMPLEMENTATIONS

### Page 1: Landing — Candidate Selection (app/page.tsx)

Build this page with:

**Hero Section (top 30% of screen)**:
- Large gradient animated headline: `"AI Interview Agent"`
- Subheading: `"ABTalks AI Cohort · Technical Assessment Platform"`
- Small badge: `"Powered by Groq · llama-3.3-70b-versatile"`
- Subtle floating particle animation in the background (pure CSS or Framer Motion)

**Candidate Grid (rest of screen)**:
- Section title: `"Select a Candidate Profile"`
- Responsive grid: 4 columns on desktop, 2 on tablet, 1 on mobile
- Render a card for each of the 20 candidates from `candidates.json`

**Each Candidate Card must show**:
- DiceBear avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed={member.name}` (render as `<img>`)
- Candidate name (bold, large)
- Job role + years of experience
- Education
- Passed missions count: out of total missions listed
- `commitDays` / 31 shown as animated mini-bar
- `missionsFirstTry` / `missionsCompleted` ratio as percentage
- List of the specific days they passed (small pill badges)
- "Start Interview" button — navigates to `/interview/{member.id}`
- Skipped days shown with a strikethrough or gray color

**State management (Zustand store)**:
```typescript
// store.ts
interface InterviewStore {
  selectedCandidate: Candidate | null;
  sessionId: string | null;
  messages: InterviewMessage[];
  isLoading: boolean;
  questionsAsked: number;
  daysCovered: number[];
  isComplete: boolean;
  feedback: FeedbackReport | null;
  // actions
  setCandidate: (c: Candidate) => void;
  addMessage: (m: InterviewMessage) => void;
  setLoading: (v: boolean) => void;
  setComplete: (feedback: FeedbackReport) => void;
  reset: () => void;
}
```

---

### Page 2: Live Interview (app/interview/[candidateId]/page.tsx)

This is the main interview UI. Split-panel layout:

**Left Sidebar (25% width, fixed)**:
- Candidate avatar (large, 80px)
- Name + job role + years experience
- Mini stats: commit days, first-try rate
- Section: "Topics Covered" — a live list of days covered so far, each with a ✅ icon when covered. Pre-populate with all their passed missions and highlight covered ones
- Section: "Interview Progress" — circular progress showing questions asked / 8 minimum

**Right Main Panel (75% width)**:
- **Header bar**: 
  - Left: "🤖 Alex — AI Interviewer"
  - Center: Progress bar (`questionsAsked / MAX_QUESTIONS`) — fills left to right with violet gradient
  - Right: Live timer (MM:SS elapsed)
- **Chat area** (scrollable):
  - Messages rendered as `ChatBubble` components
  - Interviewer messages: left-aligned, violet-tinted bubble
  - Candidate messages: right-aligned, dark glass bubble
  - Each message fades in with `animate-in` class + Framer Motion `AnimatePresence`
  - Typing indicator shows while `isLoading === true`
  - Auto-scroll to bottom on new message
- **Input area** (pinned to bottom):
  - Large textarea (`rows={3}`) — placeholder: `"Type your answer here..."`
  - `Shift+Enter` for newline, `Enter` to submit
  - Send button with arrow icon
  - Disabled + loading spinner while waiting for response
  - Character count display
  - "End Interview" button (appears after 8 questions) — triggers completion

**Interview flow**:
1. On mount, check if `sessionId` exists in Zustand. If not, call `POST /api/interview` with `{ sessionId: crypto.randomUUID(), candidate: selectedCandidate }` to start.
2. Display the returned `reply` as the first interviewer message.
3. On candidate submit → POST `{ sessionId, message }` → display returned `reply`.
4. If `done === true` → store feedback → redirect to `/feedback/{sessionId}`.

---

### Page 3: Feedback Report (app/feedback/[sessionId]/page.tsx)

Premium report card design. This page reads from the Zustand store.

**Header**:
- Confetti animation on mount (use a lightweight CSS keyframe or canvas-confetti library)
- `"🎉 Interview Complete"` in large gradient text
- Candidate name + role + date

**Top metrics row (3 cards side by side)**:
1. **Overall Score** — large animated number (count up from 0 to score), circular ring visualization
2. **Recommendation badge** — color-coded:
   - `strong_hire` → emerald green + "⭐ Strong Hire"
   - `hire` → cyan + "✅ Hire"
   - `consider` → amber + "🔶 Consider"
   - `needs_growth` → rose red + "📈 Needs Growth"
3. **Interview Stats** — questions asked, days covered, session duration

**Summary section**:
- Large block quote style: `feedback.summary`

**Topic Scores (if available)**:
- Horizontal bar chart for each topic covered
- Day number + title on left
- Animated fill bar on right (0–10 scale)
- Color-coded: ≥8 green, 5–7 amber, <5 red

**Two-column grid**:
- **Left — Strengths** (emerald): `feedback.strengths` as animated bullet list
- **Right — Gaps** (amber): `feedback.gaps` as animated bullet list

**Next Steps**:
- Numbered list: `feedback.next` — each item is a card with a right arrow icon

**Action buttons**:
- "📄 Download Report" — uses `window.print()` or generates a text file of the feedback
- "🔄 Start New Interview" — resets Zustand store, redirects to landing

---

## 🚀 DEPLOYMENT INSTRUCTIONS

### Local Development
```bash
# Install dependencies
npm install

# Add your Groq API key
cp .env.local.example .env.local
# Edit .env.local and add: GROQ_API_KEY=gsk_...

# Run dev server
npm run dev
# App runs at http://localhost:3000
```

### Vercel Deployment (for Live Demo URL)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variable in Vercel dashboard:
# GROQ_API_KEY = your_groq_api_key
```

### Testing the API Endpoint Standalone
```bash
# Start interview
curl -X POST http://localhost:3000/api/interview \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "candidate": {
      "member": { "id": "CAND-003", "name": "Emily Chen", "jobRole": "AI Engineer", "yearsExperience": 6, "education": "MS Artificial Intelligence", "status": "COMPLETED" },
      "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 1 },
        { "day": 11, "title": "RAG End-to-End", "passed": true, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": true, "attempts": 1 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": true, "attempts": 1 }
      ],
      "signals": { "commitDays": 31, "missionsCompleted": 31, "missionsFirstTry": 30 }
    }
  }'

# Continue conversation
curl -X POST http://localhost:3000/api/interview \
  -H "Content-Type: application/json" \
  -d '{ "sessionId": "test-session-001", "message": "Embeddings are numerical vector representations of text that capture semantic meaning..." }'
```

---

## 📋 DELIVERABLES CHECKLIST

Before submitting, verify every item:

**API Contract (from technical-spec.md)**
- [ ] `POST /api/interview` responds to start request `{ sessionId, candidate }` with `{ reply, done: false }`
- [ ] `POST /api/interview` responds to turn request `{ sessionId, message }` with `{ reply, done: false }`
- [ ] `POST /api/interview` returns `{ reply, done: true, feedback: { summary, strengths, gaps, next } }` when complete
- [ ] `sessionId` is maintained and tracked throughout the session
- [ ] Endpoint is CORS-enabled (callable from any client)

**Interview Quality (Minimum Requirements)**
- [ ] Minimum 8 questions asked before completion
- [ ] Minimum 4 different curriculum days covered
- [ ] Follow-up questions generated based on previous responses
- [ ] Context maintained — no repeated topics within a session
- [ ] Agent NEVER asks about skipped or failed missions

**Frontend**
- [ ] Landing page shows all 20 candidates from `candidates.json`
- [ ] Each card shows real mission data (passed, attempts, signals)
- [ ] Live interview page with split-panel layout, typing indicator, progress bar
- [ ] Feedback page with all 4 required fields displayed (summary, strengths, gaps, next)
- [ ] Responsive design (works on tablet and desktop)

**Data**
- [ ] `data/curriculum.json` contains all 31 days verbatim (as provided)
- [ ] `data/candidates.json` contains all 20 candidates verbatim (as provided)
- [ ] Agent reads from these files — does NOT hardcode questions

**Submission Requirements**
- [ ] Public GitHub repository with commit history
- [ ] `.env.local.example` with `GROQ_API_KEY=` placeholder
- [ ] `README.md` with setup steps and API documentation
- [ ] Live demo URL deployed (Vercel)
- [ ] `AI_USAGE_LOG.md` documenting AI tools used during development

---

## ⚠️ CRITICAL CONSTRAINTS — DO NOT VIOLATE

1. **The API contract from technical-spec.md is law.** The exact JSON fields (`reply`, `done`, `feedback.summary`, `feedback.strengths`, `feedback.gaps`, `feedback.next`) must match exactly — judges will test this with automated tools.

2. **Use `groq-sdk` with model `llama-3.3-70b-versatile`.** Get a free key at [console.groq.com](https://console.groq.com). This model is fast, free, and capable — do not use Gemini, OpenAI, or any paid model.

3. **Never ask about skipped or failed missions.** The `getExcludedDays()` function handles this — the system prompt enforces it.

4. **Never ask multiple questions in a single message.** The system prompt enforces this — verify it in testing by checking every Groq response.

5. **All 20 candidate profiles must be selectable from the landing page.** The data is given verbatim above — use it directly.

6. **The feedback must be generated from the actual conversation transcript**, not fabricated. Low temperature (0.1) in `generateFeedback()` ensures this.

7. **Session must be maintained using the provided `sessionId`.** Never generate a new sessionId internally — use the one provided by the client.

---

*This prompt uses the exact curriculum.json (31 days, 8 modules), candidates.json (20 real candidates), and technical-spec.md API contract from the hackathon resources. All data is synthetic and intended for the hackathon only.*
