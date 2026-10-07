# AiRuleScraper: Automated Coding Rules Miner ⛏️

An intelligent, asynchronous background worker system designed to scrape, process, and vectorize software engineering rules and best practices.

This service acts as the data ingestion pipeline for the **AiReviewer** ecosystem, feeding high-quality, AI-extracted coding standards into a `pgvector` database for Retrieval-Augmented Generation (RAG).

## 📖 Overview

Instead of manually defining code review guidelines, **AiRuleScraper** automates the knowledge-gathering process.

The system:

1. Crawls documentation URLs provided through `seeds.txt`.
2. Extracts meaningful architectural, formatting, and software engineering rules.
3. Uses LLMs such as **Groq** and **Google Gemini** to transform raw documentation into structured coding rules.
4. Generates vector embeddings for the extracted rules.
5. Stores the rules and embeddings in PostgreSQL with the `pgvector` extension.
6. Provides the resulting knowledge base to the **AiReviewer** system for semantic retrieval and AI-assisted code review.

## ✨ Key Features

* **Autonomous Crawling**
  Reads URLs from `seeds.txt` and safely tracks processed targets in `seeds_done.txt` to prevent redundant scraping.

* **AI-Powered Mining**
  Utilizes advanced LLMs to intelligently parse raw HTML/text and extract strict, actionable code review rules with **Bad vs Good** code examples.

* **Vector Embeddings (RAG Ready)**
  Automatically generates mathematical representations of extracted rules and stores them in PostgreSQL using `pgvector` for fast semantic search.

* **Microservice Worker Architecture**
  The `crawler` and `miner` services are decoupled and can be executed independently or scheduled through cron jobs.

* **Blazing-Fast Dependency Management**
  Built and containerized using [`uv`](https://github.com/astral-sh/uv), providing fast dependency resolution and lightweight Docker builds.

## 🛠️ Tech Stack

| Component              | Technology                            |
| ---------------------- | ------------------------------------- |
| **Language**           | Python 3.14                           |
| **Package Manager**    | [uv](https://github.com/astral-sh/uv) |
| **Database**           | PostgreSQL + `pgvector`               |
| **ORM**                | SQLAlchemy 2.0 (Async)                |
| **Migrations**         | Alembic                               |
| **AI / LLM Providers** | Groq API, Google Gemini API           |
| **Infrastructure**     | Docker, Docker Compose                |

## 🏗️ Architecture Flow

The system processes coding standards through the following pipeline:

```text
┌─────────────────┐
│   seeds.txt     │
│   Target URLs   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Crawler     │
│ Fetch HTML/Text │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Raw Documents  │
│ Temporary Data  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      Miner      │
│   LLM Analysis  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Structured Coding Rules │
│ Bad / Good Examples     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│    Embeddings   │
│      Gemini     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ PostgreSQL + pgvector   │
│      RAG Knowledge Base │
└─────────────────────────┘
```

### Processing Steps

1. **Seed Ingestion**
   The Crawler reads target URLs from `seeds.txt`.

2. **Data Extraction**
   Raw HTML or text is fetched and temporarily stored for further processing.

3. **AI Processing**
   The Miner analyzes the extracted content and prompts the configured LLM to identify coding standards and best practices.

4. **Rule Structuring**
   The extracted knowledge is converted into structured rules, including actionable descriptions and **Bad vs Good** code examples.

5. **Vectorization**
   Each rule is converted into a vector embedding using Google Gemini.

6. **Persistence**
   Structured rules and their embeddings are stored in PostgreSQL using `pgvector`.

7. **Seed Tracking**
   Successfully processed URLs are moved to `seeds_done.txt` to prevent unnecessary duplicate processing.

## 🚀 Getting Started

### Prerequisites

Make sure the following are installed and available:

* [Docker](https://www.docker.com/)
* Docker Compose
* PostgreSQL with the `pgvector` extension
* A valid **Groq API key**
* A valid **Google Gemini API key**

> **Note:** When running PostgreSQL through Docker, the required `pgvector` extension can be provided by the PostgreSQL image used by the project.

### Installation

#### 1. Clone the repository

```bash
git clone https://github.com/MiroshYaroslav/AiRuleScraper.git
cd AiRuleScraper
```

#### 2. Create the environment configuration

Copy the example environment file:

```bash
cp .env.example .env
```

#### 3. Configure environment variables

Open `.env` and provide the required database credentials and API keys.

See the [Environment Variables](#environment-variables) section below.

#### 4. Add seed URLs

Add the documentation pages you want to process to:

```text
seeds.txt
```

Use one URL per line:

```text
https://example.com/documentation
https://example.com/style-guide
https://example.com/best-practices
```

Processed URLs are tracked in:

```text
seeds_done.txt
```

This prevents the same source from being unnecessarily processed again.

## ⚙️ Environment Variables

Configure the following variables in your `.env` file.

| Variable          | Description                            | Example                                                |
| ----------------- | -------------------------------------- | ------------------------------------------------------ |
| `DATABASE_URL`    | Async PostgreSQL connection string     | `postgresql+asyncpg://user:password@localhost:5432/db` |
| `GROQ_API_KEYS`   | Comma-separated Groq API keys          | `gsk_key_1,gsk_key_2,gsk_key_3`                        |
| `GEMINI_API_KEYS` | Comma-separated Google Gemini API keys | `AIzaSy_key_1,AIzaSy_key_2`                            |

### Multiple API Keys

Multiple API keys can be provided for load balancing and sticky failover.

For example:

```env
GROQ_API_KEYS=gsk_key_1,gsk_key_2,gsk_key_3
GEMINI_API_KEYS=AIzaSy_key_1,AIzaSy_key_2
```

This allows the workers to distribute requests across multiple credentials and improve resilience when a key reaches its rate limit or becomes temporarily unavailable.

## 💻 Usage

The system is fully containerized and controlled through Docker Compose.

### 1. Database Migrations

Before running the workers for the first time, apply the Alembic migrations to create the required database structures and enable the `pgvector` extension.

```bash
docker compose run --rm crawler alembic upgrade head
```

### 2. Run the Crawler

Start the crawler to fetch data from the URLs listed in `seeds.txt`:

```bash
docker compose up crawler
```

The crawler is responsible for:

* Reading URLs from `seeds.txt`
* Fetching documentation content
* Storing the extracted data for further processing
* Tracking successfully processed seeds

### 3. Run the AI Miner

Start the Miner to process the fetched content:

```bash
docker compose up miner
```

The Miner is responsible for:

* Reading the fetched documents
* Sending relevant content to the configured LLM
* Extracting coding rules and best practices
* Generating **Bad vs Good** examples
* Creating vector embeddings
* Saving structured rules and embeddings to PostgreSQL

## 🔄 Crawler and Miner Workflow

The two workers are intentionally separated:

```text
seeds.txt
   │
   ▼
Crawler
   │
   ▼
Fetched Documentation
   │
   ▼
Miner
   │
   ├──► LLM Rule Extraction
   │
   ├──► Rule Structuring
   │
   └──► Gemini Embeddings
             │
             ▼
      PostgreSQL + pgvector
```

This separation makes it possible to:

* Run crawling and AI processing independently.
* Retry failed mining jobs without re-downloading source pages.
* Schedule workers independently.
* Scale the crawler and miner according to workload.

## 🗄️ Database

The project uses **PostgreSQL** together with the [`pgvector`](https://github.com/pgvector/pgvector) extension.

`pgvector` enables storing vector embeddings directly inside PostgreSQL, allowing the AiReviewer system to perform semantic similarity searches over extracted coding rules.

The resulting database serves as the knowledge base for Retrieval-Augmented Generation (RAG).

### Why pgvector?

Traditional keyword search is often insufficient for coding standards because semantically similar rules may use different wording.

Vector search makes it possible to retrieve rules based on meaning rather than exact keyword matches.

For example:

```text
Query:
"Do not expose mutable internal state"

Possible matching rules:
- Avoid returning mutable collections directly.
- Prefer immutable interfaces for internal data.
- Protect object state from external mutation.
```

## 🤖 AI Processing

AiRuleScraper uses LLMs to transform unstructured documentation into actionable engineering rules.

Instead of simply storing documentation paragraphs, the Miner attempts to produce structured knowledge suitable for automated code review.

A typical extracted rule may conceptually contain:

```text
Rule:
Avoid returning mutable collections directly from public APIs.

Bad:
return this.items;

Good:
return List.copyOf(this.items);

Reason:
Returning the internal collection allows callers to mutate internal state.
```

This structure makes the resulting knowledge much more useful for an AI code reviewer.

## 🧠 RAG Integration

The generated embeddings are intended to be consumed by the **AiReviewer** ecosystem.

A typical RAG workflow looks like:

```text
Developer Code
      │
      ▼
AiReviewer
      │
      ▼
Vector Similarity Search
      │
      ▼
Relevant Coding Rules
      │
      ▼
LLM Context
      │
      ▼
AI Code Review
```

The scraper therefore acts as the **knowledge ingestion layer** for the reviewer.

## 📁 Input Files

### `seeds.txt`

Contains URLs that should be scraped.

Example:

```text
https://docs.python.org/3/
https://google.github.io/styleguide/
https://martinfowler.com/
```

One URL should be placed on each line.

### `seeds_done.txt`

Contains URLs that have already been processed successfully.

This file allows the crawler to avoid processing the same source multiple times.

## 🐳 Docker Architecture

The application is designed around independent Docker Compose services.

Conceptually:

```text
                 ┌──────────────────┐
                 │ Docker Compose   │
                 └─────────┬────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       ┌──────────────┐         ┌──────────────┐
       │    crawler   │         │     miner    │
       └──────┬───────┘         └──────┬───────┘
              │                        │
              │                        │
              └──────────┬─────────────┘
                         ▼
                ┌─────────────────┐
                │   PostgreSQL    │
                │    + pgvector   │
                └─────────────────┘
```

The workers can be started independently depending on the desired workflow.

## 🔧 Development

The project uses [`uv`](https://github.com/astral-sh/uv) for dependency management.

This provides:

* Fast dependency resolution
* Reproducible environments
* Efficient Python package installation
* Lightweight container builds

The project targets:

```text
Python 3.14
```

## 📌 Example Workflow

A typical end-to-end workflow looks like this:

```bash
# 1. Configure the environment
cp .env.example .env

# 2. Add documentation URLs
vim seeds.txt

# 3. Run database migrations
docker compose run --rm crawler alembic upgrade head

# 4. Crawl documentation
docker compose up crawler

# 5. Extract and vectorize coding rules
docker compose up miner
```

After the Miner finishes, the extracted rules and embeddings are available in PostgreSQL for semantic retrieval by the **AiReviewer** system.

## 🔐 Security Notes

Do not commit sensitive API keys or database credentials to version control.

Keep secrets in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/db
GROQ_API_KEYS=gsk_key_1,gsk_key_2
GEMINI_API_KEYS=AIzaSy_key_1,AIzaSy_key_2
```

Make sure `.env` is excluded from Git using `.gitignore`.

## 📄 License

This project was developed for **portfolio and educational purposes**.
