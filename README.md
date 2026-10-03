# 🤖 LeadGen Agent

> **An AI-powered, human-in-the-loop lead generation and outreach pipeline built with Python, FastAPI, n8n, LLMs, LinkedIn and Slack.**

LeadGen Agent is an automation system designed to turn **LinkedIn activity into structured, enriched and personalized sales opportunities**.

Instead of manually searching for prospects, researching their companies, writing outreach messages and deciding what to send, the system connects several specialized agents and services into one workflow.

The goal is not simply to automate outreach — it is to build a pipeline where **AI handles the repetitive work while humans remain in control of the final communication.**

---

## ✨ What does it do?

At a high level:

```text
LinkedIn Activity
       │
       ▼
┌──────────────────────┐
│  LinkedIn Listener   │
│  Detect relevant     │
│  posts / activity    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    Lead Writer       │
│ Generate content /   │
│ identify prospects   │
└──────────┬───────────┘
           │
           ├──────────────────┐
           ▼                  ▼
┌──────────────────┐   ┌──────────────────┐
│  Lead Enrichment │   │ AI Outreach      │
│                  │   │                  │
│ Find email       │   │ Analyze intent   │
│ Company          │   │ Generate DM      │
│ Role             │   │ Follow-ups       │
└────────┬─────────┘   │ Connection note  │
         │             └────────┬─────────┘
         └──────────────┬───────┘
                        ▼
               ┌──────────────────┐
               │ Slack Approval   │
               │                  │
               │ Human reviews    │
               │ AI suggestions   │
               └────────┬─────────┘
                        │
                 Approve / Decline
                        │
                        ▼
               ┌──────────────────┐
               │ Outreach / Warm  │
               │ Lead Management  │
               └──────────────────┘
```

---

# 🧠 The idea

Traditional lead generation often involves a lot of repetitive work:

* Finding potential customers
* Reading their LinkedIn activity
* Understanding their interests
* Finding company/contact information
* Writing personalized messages
* Creating follow-ups
* Tracking lead status
* Deciding which messages are worth sending

LeadGen Agent turns this into an **orchestrated pipeline**.

Each component has a specific responsibility, while **n8n acts as the workflow orchestrator** connecting the different services.

---

# 🚀 Core Features

### 🔎 LinkedIn listening

The system can listen for LinkedIn activity and feed relevant information into the lead generation pipeline.

The LinkedIn listener acts as the entry point for the workflow.

```text
LinkedIn
   ↓
Listener
   ↓
LeadGen Pipeline
```

---

### ✍️ AI-powered content generation

The Writer and Outreach agents use LLMs to generate personalized content based on the available lead and post context.

The system can generate:

* LinkedIn DMs
* LinkedIn connection notes
* Follow-up messages
* Calendly follow-ups
* Comment suggestions

The goal is to generate **short, contextual and human-sounding messages rather than generic templates**.

---

### 🧠 Intent & interest classification

The Outreach Agent analyzes a LinkedIn post and attempts to identify:

* The main topic
* Relevant business/service area
* Potential intent
* A useful angle for outreach

Current service areas include:

```text
lead generation
sales
business development
marketing automation
automation
generative AI
AI agents
generative engine optimization
```

This allows the generated outreach to be connected to **what the prospect actually talks about**.

---

### 📧 Lead enrichment

The `EnricherAgent` takes newly discovered leads and attempts to enrich them with additional information.

For example:

```text
Name
  +
LinkedIn profile
  +
Company
       ↓
Domain guessing
       ↓
Email enrichment
       ↓
Company / role information
       ↓
Enriched Lead
```

The enrichment process can try several domain candidates before giving up.

For example:

```text
company.com
linkedin.com
gmail.com
yahoo.com
```

The enriched information is then persisted in the database and the lead status is updated.

---

### 💬 Personalized outreach

The `OutreachAgent` generates several types of communication.

#### LinkedIn DM

A short personalized message based on:

* Lead name
* Role
* Company
* LinkedIn post
* Detected topic
* Relevant service area

#### Connection note

The system generates a short LinkedIn invitation note with a strict character limit.

#### Follow-ups

Two lightweight follow-up messages are generated for leads who have not responded.

#### Warm lead follow-up

For leads that become warm, the system can generate a Calendly-based follow-up message.

---

# 👤 Human-in-the-loop approval

One of the most important design decisions in this project is that **AI does not blindly send everything it generates.**

Instead, generated outreach can be sent to a Slack approval channel.

The reviewer can see:

```text
🧠 New Comment Suggestions

Post → Read the original post

💬 Select ONE comment
   ○ Comment option 1
   ○ Comment option 2
   ○ Comment option 3

🔥 Select ONE reaction
   ○ Reaction 1
   ○ Reaction 2

[ Approve ]    [ Decline ]
```

This creates a **human-in-the-loop architecture**:

```text
AI generates
     ↓
Human reviews
     ↓
Approve / Decline
     ↓
Continue workflow
```

This approach provides a balance between **automation and human judgment**.

---

# 🔗 Architecture

The project is split into two main layers.

### Python / FastAPI

Python contains the application logic and specialized agents.

```text
FastAPI
│
├── LinkedIn Listener
├── Writer
├── EnricherAgent
├── OutreachAgent
├── Leads Management
├── Post Response
│
├── Database
│   └── SQLAlchemy
│
└── External Clients
    ├── LinkedIn / Unipile
    ├── LLM / OpenAI
    └── Email enrichment
```

### n8n

n8n orchestrates the high-level workflow.

```text
Listen
  │
  ├──────────────► Write
  │                  │
  │                  ▼
  │              Slack Approval
  │
  ▼
Enrich
  │
  ▼
Outreach
  │
  ▼
Warm Lead
```

The Python application focuses on **business logic and AI agents**, while n8n handles **workflow orchestration and integration between services**.

---

# 🛠️ Tech Stack

| Technology       | Purpose                               |
| ---------------- | ------------------------------------- |
| 🐍 Python        | Agent and business logic              |
| ⚡ FastAPI        | Backend API                           |
| 🔄 n8n           | Workflow orchestration                |
| 🧠 OpenAI / LLMs | Classification and content generation |
| 💼 LinkedIn      | Lead discovery and engagement         |
| 🔌 Unipile       | LinkedIn/API integration              |
| 📧 Trykitt       | Lead/email enrichment                 |
| 💬 Slack         | Human approval workflow               |
| 🗄️ SQLAlchemy   | Database access                       |
| 🐘 PostgreSQL    | Lead persistence                      |
| 🐳 Docker        | Local infrastructure                  |

---

# 🔌 API Endpoints

The FastAPI application exposes several workflow endpoints.

```text
POST /api/listen_linkedin
POST /api/write
POST /api/enrich
POST /api/outreach/{lead_id}
GET  /api/leads/warm
```

Additional endpoints handle post responses and lead management.

The root endpoint can be used as a simple health check:

```http
GET /
```

Response:

```json
{
  "message": "LeadGen Agent API is running 🚀"
}
```

---

# 🔄 Example Workflow

Imagine a potential customer publishes a LinkedIn post about **AI automation**.

### 1. Listen

The LinkedIn listener detects the relevant activity.

```text
LinkedIn Post
     ↓
Lead detected
```

### 2. Write

The system processes the lead and creates the necessary content/context.

### 3. Enrich

The lead is enriched with additional information:

```text
Name
Company
Role
Email
LinkedIn URL
```

### 4. Analyze

The Outreach Agent analyzes the post:

```json
{
  "theme": "AI automation",
  "area": "automation",
  "reason": "The post discusses automating repetitive business processes."
}
```

### 5. Generate

The LLM generates personalized outreach:

```text
LinkedIn DM
Connection note
Follow-ups
```

### 6. Human approval

The suggestions are sent to Slack.

The operator can choose:

```text
Approve
```

or

```text
Decline
```

### 7. Continue

Approved interactions can continue through the configured outreach pipeline.

---

# 📁 Project Structure

A simplified structure looks like:

```text
leadgen-agent/
│
├── app/
│   ├── agents/
│   │   ├── enricher_agent.py
│   │   └── outreach_agent.py
│   │
│   ├── api/
│   │   ├── listen.py
│   │   ├── write.py
│   │   ├── enrich.py
│   │   ├── outreach.py
│   │   ├── leads.py
│   │   └── post_response.py
│   │
│   ├── clients/
│   │   ├── unipile_client.py
│   │   └── trykitt_client.py
│   │
│   ├── db/
│   │   └── models.py
│   │
│   └── utils/
│       └── config.py
│
├── workflows/
│   └── leadgen_agent.json
│
├── .env.example
├── requirements.txt
└── README.md
```

---

# ⚙️ Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/leadgen-agent.git
cd leadgen-agent
```

## 2. Configure environment variables

Create your environment file:

```bash
cp .env.example .env
```

Configure the required credentials/API keys for your environment.

For example:

```env
OPENAI_API_KEY=your_key
UNIPILE_API_KEY=your_key
TRYKITT_API_KEY=your_key

DATABASE_URL=your_database_url

CALENDLY_BOOKING_URL=your_booking_url
```

**Built to experiment, automate, and learn. 🚀**
