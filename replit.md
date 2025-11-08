# AI가 찾은 스타 애널리스트 어워즈 시스템

## Overview
This is an AI-powered analyst awards system that evaluates and ranks financial analysts based on their reports and predictions. The system consists of a Next.js frontend and a FastAPI backend.

## Recent Changes (November 8, 2025)
- **Migrated from Vercel to Replit** ✅ COMPLETED
  - Configured Next.js to run on port 5000 with host 0.0.0.0 for Replit compatibility
  - Fixed CSS import path in Navbar component (../../styles/fnguide.css)
  - Fixed JavaScript strict mode error in dashboard page (renamed 'eval' variable to 'evaluation')
  - Installed Node.js 20, Python 3.11, and pnpm 8.10.0
  - Set up PostgreSQL database using Replit's built-in database
  - Configured deployment settings for production (autoscale)
  - Added API keys for OpenAI, Anthropic, Google AI, and Perplexity

- **Backend Migration Fixes** ✅ COMPLETED
  - Fixed missing typing imports (List, Dict, Optional, Any, date) across multiple files
  - Resolved circular import between evaluation_service.py and evaluation_tasks.py (using lazy imports)
  - Fixed SQLAlchemy model issues: renamed `metadata` to `extra_data` in Company, Prediction, Evaluation, DataSource, ActualResult models
  - Fixed EvaluationScore import path in report_generation_agent.py
  - Installed missing dependencies (email-validator)
  - Backend now successfully starts and serves API on port 8000
  - All critical runtime issues resolved; remaining LSP warnings are SQLAlchemy type hints (non-blocking)

## Project Architecture

### Monorepo Structure
- `apps/web/` - Next.js 14 frontend (TypeScript, Tailwind CSS, React Query)
- `apps/api/` - FastAPI backend (Python, SQLAlchemy, Celery)

### Frontend (apps/web)
- **Framework**: Next.js 14 with App Router
- **UI Libraries**: Tailwind CSS, Recharts for data visualization
- **State Management**: TanStack React Query
- **Key Pages**:
  - Dashboard - Overview statistics and charts
  - Analysts - Analyst management
  - Reports - Report upload and extraction
  - Evaluations - Evaluation execution and results
  - Scorecards - Scorecard viewing and rankings
  - Awards - Awards selection and display
  - Data Collection - Data collection management

### Backend (apps/api)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery with Redis
- **AI Services**: OpenAI, Anthropic, Google Generative AI, Perplexity
- **Document Processing**: PDF extraction, OCR support

## Environment Configuration

### Required Environment Variables
- `DATABASE_URL` - PostgreSQL connection string (auto-configured by Replit)
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models
- `GOOGLE_API_KEY` - Google Generative AI API key
- `PERPLEXITY_API_KEY` - Perplexity AI API key
- `NEXT_PUBLIC_API_URL` - Backend API URL (optional, defaults to localhost:8000)

### Development
- Frontend runs on port 5000: `cd apps/web && pnpm run dev`
- Backend runs on port 8000: `cd apps/api && uvicorn app.main:app --reload`

### Production Deployment
- Build command: `cd apps/web && pnpm install && pnpm run build`
- Start command: `cd apps/web && pnpm run start`
- Deployment type: Autoscale (stateless)

## Database Management
- Schema defined in `apps/api/app/models/`
- Migrations managed with Alembic
- Use `cd apps/api && alembic upgrade head` to run migrations

## User Preferences
- Language: Korean (primary UI language)
- Code style: TypeScript with strict mode enabled
- Project uses monorepo structure with pnpm workspaces
