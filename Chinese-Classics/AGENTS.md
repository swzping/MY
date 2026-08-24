# Agent Guidelines for Chinese-Classics Project

## Project Overview

This is a Chinese Classics Fortune Telling AI Agent platform with:
- **Frontend**: React 18, TypeScript, Vite, Ant Design, Tailwind CSS, Three.js/React-Three-Fiber
- **Backend**: FastAPI, Python 3.11, LangChain, LangGraph
- **Database**: PostgreSQL (pgvector), Redis, Milvus (via Docker Compose)

---

## Build / Lint / Test Commands

### Frontend (in `frontend/` directory)

```bash
# Install dependencies
npm install

# Development server (runs on port 6789)
npm run dev

# Build for production (runs TypeScript check first)
npm run build

# Lint with ESLint
npm run lint

# Preview production build
npm run preview
```

### Backend (in `backend/` directory)

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (hot reload on port 8000)
uvicorn app.main:app --reload

# Run all tests
pytest backend/tests

# Run a single test file
pytest backend/tests/test_tools.py

# Run a single test function
pytest backend/tests/test_tools.py::test_iching_tool

# Run tests with verbose output
pytest backend/tests -v
```

### Docker Compose (from project root)

```bash
# Start all services (using convenience script)
./start.sh up-d

# Or use docker-compose directly
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
./start.sh down
```

### Running Single Tests

- **Frontend**: No test framework is currently set up. If adding tests, use Vitest.
- **Backend**: Use `pytest backend/tests/test_tools.py::test_function_name`

---

## Code Style Guidelines

### General Principles

1. **Language**: UI text and user-facing content is in Simplified Chinese
2. **Logging**: Use English for log messages (structured with structlog on backend)
3. **Comments**: Use Chinese comments for business logic, English for technical explanations

---

### Frontend (React + TypeScript)

#### File Organization
```
src/
├── components/     # Reusable UI components
│   └── 3d/         # Three.js/React-Three-Fiber components
├── pages/          # Route pages
├── contexts/       # React contexts (Auth, etc.)
├── hooks/          # Custom React hooks
├── services/       # API service layers
├── types/           # TypeScript type definitions
└── assets/         # Static assets
```

#### Naming Conventions
- **Components**: PascalCase (e.g., `Home.tsx`, `Scene3D.tsx`)
- **Hooks**: camelCase with `use` prefix (e.g., `useAuth.ts`)
- **Types/Interfaces**: PascalCase (e.g., `UserType.ts`)
- **Constants**: SCREAMING_SNAKE_CASE

#### Import Style
- Use path alias `@/` for absolute imports from `src/`
```typescript
import Home from '@/pages/Home';
import { useAuth } from '@/contexts/AuthContext';
```
- Order imports: 1) React/internal, 2) External libraries, 3) Path aliases, 4) Relative

#### TypeScript Guidelines
- Enable strict mode (`strict: true` in tsconfig.json)
- Always define types for props, function parameters, and return values
- Avoid `any`; use `unknown` if type is truly unknown

#### React Patterns
- Use functional components with hooks
- Use `React.FC` or explicit prop types for component typing
- Lazy load heavy components (especially 3D scenes):
```typescript
const Scene3D = lazy(() => import('../components/3d/Scene3D'));
```
- Use `Suspense` with fallback for lazy components

#### Styling
- Use Tailwind CSS for styling
- Use inline styles via Tailwind utilities
- Use `framer-motion` for animations
- Use `clsx` and `tailwind-merge` for conditional classes:
```typescript
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined)[]) {
  return twMerge(clsx(inputs));
}
```

---

### Backend (Python + FastAPI)

#### File Organization
```
backend/
├── app/
│   ├── api/endpoints/   # API route handlers
│   ├── core/            # Core utilities (config, security, RAG)
│   ├── tools/           # LangChain tools (iching, bazi, etc.)
│   ├── agent/           # LangGraph agent logic
│   ├── models.py        # Pydantic models
│   ├── db.py            # Database setup
│   └── main.py          # FastAPI app entry point
├── tests/               # Pytest test files
└── requirements.txt     # Python dependencies
```

#### Naming Conventions
- **Functions/variables**: snake_case (e.g., `get_user`, `user_data`)
- **Classes**: PascalCase (e.g., `IChingTool`, `UserModel`)
- **Constants**: SCREAMING_SNAKE_CASE
- **Private methods**: prefix with `_` (e.g., `_generate_hexagram`)

#### Type Hints
- Use type hints for all function parameters and return values
- Use `typing` module for complex types (List, Dict, Optional, Union)

#### FastAPI Patterns
- Use Pydantic models for request/response validation
- Use async/await for I/O operations
- Include docstrings for endpoints:
```python
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

#### LangChain Tools
- Inherit from `langchain.tools.BaseTool`
- Define input schema using Pydantic `BaseModel`
- Implement `_run()` for sync and `_arun()` for async execution

#### Error Handling
- Return error dictionaries: `{"error": "message"}`
- Use try/except in tool implementations
- Log errors with structlog

---

## API Conventions

### Frontend-Backend Communication
- Backend API prefix: `/api/v1`
- Frontend proxies `/api` to `http://127.0.0.1:8000` (see `vite.config.ts`)

### Common Endpoints
- `GET /api/v1/auth/...` - Authentication
- `GET /api/v1/chat/...` - Chat/Agent
- `GET /api/v1/history/...` - Chat history
- `GET /api/v1/...` - Misc (tutorials, etc.)

---

## Testing Guidelines

### Backend Tests
- Test files in `backend/tests/`
- Use `pytest` with `pytest-asyncio` for async tests
- Add project root to Python path:
```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
```

### Adding Frontend Tests
If adding tests, use **Vitest** (compatible with Vite):
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

---

## Environment Variables

- Copy `.env.example` to `.env` before development
- Never commit secrets to version control
- Frontend env vars: `VITE_*` prefix for client-side
- Backend env vars: Use `pydantic-settings` (see `app/core/config.py`)

---

## Notes for AI Agents

1. **3D Components**: The project uses React-Three-Fiber for 3D visualizations. Be careful when modifying 3D scene code.
2. **Chinese Text**: UI elements are in Chinese; preserve Chinese text when editing.
3. **Docker Services**: The project depends on PostgreSQL, Redis, and Milvus for full functionality.
4. **API Documentation**: FastAPI auto-generates docs at `/docs` when running backend.
5. **LangChain Tools**: The core functionality is in `backend/app/tools/`. Each tool (iching, horoscope, bazi, zodiac, naming) inherits from BaseTool.
