# Implementation Blueprint: Agent UI Interface

## Overview
Build a secure Next.js web interface that lets users submit natural-language prompts, auto-routes requests to the correct AI agent through existing FastAPI endpoints, logs each invocation (agent, inputs, outputs) into Postgres, and lays the groundwork for future Google OAuth while starting with username/password authentication.

## Implementation Phases

### Phase 1: Backend Action Logging & Persistence
**Objective**: Extend the current SQLAlchemy models, schemas, and CRUD utilities to persist every UI-triggered agent invocation (agent, payload, response, timestamps, user), using the same synchronous DB patterns already present, then expose a FastAPI router for recording and listing those entries.
**Code Proposal**:
```python
# app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    google_sub = Column(String, unique=True, nullable=True)
    actions = relationship("AgentAction", back_populates="user")

class AgentAction(Base):
    __tablename__ = "agent_actions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    tool_calls = Column(JSON, nullable=True)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="actions")

# app/schemas.py
class AgentActionCreate(BaseModel):
    agent_name: str
    question: str
    tool_calls: dict | None = None
    response: str

class AgentAction(AgentActionCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# app/crud.py
def create_agent_action(db: Session, user_id: int, payload: schemas.AgentActionCreate) -> models.AgentAction:
    db_action = models.AgentAction(user_id=user_id, **payload.model_dump())
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action

def get_agent_actions(db: Session, user_id: int, limit: int = 100) -> list[models.AgentAction]:
    return (
        db.query(models.AgentAction)
        .filter(models.AgentAction.user_id == user_id)
        .order_by(models.AgentAction.created_at.desc())
        .limit(limit)
        .all()
    )

# app/routers/agent_actions.py
@router.post("/", response_model=schemas.AgentAction)
def create_action(action_in: schemas.AgentActionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.create_agent_action(db, user_id=user.id, payload=action_in)

@router.get("/", response_model=list[schemas.AgentAction])
def list_actions(db: Session = Depends(get_db), user=Depends(get_current_user), limit: int = 100):
    return crud.get_agent_actions(db, user_id=user.id, limit=limit)
```
**Tests**:
- Unit-test repository functions using in-memory SQLite to ensure logs persist and filter by user.
- API tests verifying POST `/agent-actions/` stores entries and GET returns user-scoped data.

### Phase 2: Router Agent & FastAPI Endpoint
**Objective**: Introduce a router agent that uses the same configuration pattern as the existing YAML files in `app/agents/configs/`, ensuring the orchestrator dynamically loads it and exposes a FastAPI endpoint that returns the chosen agent plus metadata for the UI logs.
**Code Proposal**:
```python
# app/agents/configs/router_agent.yaml
agent_name: "RouterAgent"
description: "Classifies natural language queries and selects the correct downstream agent."

llm:
  provider: ${LLM_PROVIDER}
  model_name: ${GOOGLE_MODEL}
  temperature: 0.0

tools:
  - "classify_agent_request"

prompt_template: |
  You are a routing assistant for the financial agent system. Examine the user's query and determine which agent (registration_agent, management_agent, or analysis_agent) should respond. 
  
  Output JSON only:
  {
    "agent_name": "<agent_name>",
    "confidence": <0-1 float>,
    "reasoning": "<short explanation>"
  }

  Question: {input}
  Thought:{agent_scratchpad}

# app/routers/agent.py
class AgentResponseWithMetadata(BaseModel):
    agent: str
    confidence: float | None = None
    answer: str
    routing_metadata: dict | None = None

@router.post("/query/router", response_model=AgentResponseWithMetadata)
def query_router(request: AgentQuery, db: Session = Depends(get_db), user=Depends(get_current_user)):
    raw_classification = orchestrator_agent.invoke_agent("router_agent", request.question, timeout=15)
    try:
        classification = json.loads(raw_classification)
    except json.JSONDecodeError:
        classification = {
            "agent_name": "analysis_agent",
            "confidence": None,
            "reasoning": "Fallback: router output was not valid JSON."
        }

    agent_name = classification.get("agent_name") or "analysis_agent"
    agent_answer = orchestrator_agent.invoke_agent(agent_name, request.question, timeout=60)

    crud.create_agent_action(
        db,
        user_id=user.id,
        payload=schemas.AgentActionCreate(
            agent_name=agent_name,
            question=request.question,
            tool_calls=classification,
            response=agent_answer,
        ),
    )
    return {
        "agent": agent_name,
        "confidence": classification.get("confidence"),
        "answer": agent_answer,
        "routing_metadata": classification,
    }
```
**Tests**:
- Mock router outputs to ensure the pipeline executes the expected agent.
- Verify uncertainty handling (e.g., fallback to manual choice when confidence < threshold).

### Phase 3: Authentication Foundation with Upgrade Path to OAuth
**Objective**: Implement username/password authentication using FastAPI dependencies and the existing Postgres infrastructure, expose JWT-based auth for the UI, and structure the user model and API contracts so we can later swap/augment with Google OAuth (e.g., storing `google_sub`, using NextAuth.js in the UI) without breaking changes.
**Code Proposal**:
```python
# app/security.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    ...

# app/routers/auth.py
@router.post("/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/auth/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    hashed = get_password_hash(user_in.password)
    return crud.create_user(db, email=user_in.email, password_hash=hashed)

# app/dependencies.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    payload = decode_token(token)
    user = crud.get_user(db, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user
```
**Tests**:
- Unit tests for password hashing/verification and JWT creation.
- API tests for `/auth/login` success/failure cases and protected routes requiring tokens.

### Phase 4: Next.js UI for Agent Interaction
**Objective**: Build a Next.js App Router project (TypeScript, Server Components by default, Client Components only when interaction is required) that mirrors the repo’s best practices: leverage Route Handlers for server-to-server calls, reuse the FastAPI endpoints described in README/Makefile, and keep styling consistent with the broader product (Tailwind or the team’s design system). The UI must authenticate via username/password initially using HTTP-only cookies (ready to swap to Google OAuth), display which agent was chosen, show routed metadata, and surface the action logs.
**Code Proposal**:
```tsx
// app/(auth)/login/page.tsx (Server Component feeding a small Client form)
export default function LoginPage() {
  return (
    <div className="card">
      <LoginForm />
    </div>
  );
}

// app/(auth)/login/LoginForm.tsx (Client Component)
"use client";
export function LoginForm() {
  const router = useRouter();
  const action = async (formData: FormData) => {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });
    if (res.ok) {
      const { access_token } = await res.json();
      await setAuthCookie(access_token); // server action writing HTTP-only cookie
      router.push("/dashboard");
    }
  };
  return (
    <form action={action} className="space-y-4">
      {/* inputs */}
      <Button type="submit">Sign in</Button>
    </form>
  );
}

// app/dashboard/page.tsx (Server Component fetching initial logs)
export default async function Dashboard() {
  const session = await requireSession();
  const initialLogs = await fetchFromApi<AgentAction[]>("/agent-actions/", session.token);
  return (
    <main className="grid gap-6">
      <ClientChat initialLogs={initialLogs} />
    </main>
  );
}

// app/dashboard/ClientChat.tsx
"use client";
export function ClientChat({ initialLogs }: { initialLogs: AgentAction[] }) {
  const [messages, setMessages] = useState(initialLogs);
  const sendMessage = async (question: string) => {
    const result = await fetch("/api/router-query", {
      method: "POST",
      body: JSON.stringify({ question }),
    }).then((res) => res.json());
    setMessages((prev) => [{ ...result, question }, ...prev]);
  };
  return (
    <>
      <ChatInput onSubmit={sendMessage} />
      <ActionLogTable entries={messages} />
    </>
  );
}

// app/(auth)/actions.ts (Server Action helper)
"use server";
import { cookies } from "next/headers";

export async function setAuthCookie(token: string) {
  cookies().set("fas_token", token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });
}

// app/api/router-query/route.ts (Route Handler, uses fetch to FastAPI)
import { cookies } from "next/headers";

export async function POST(request: NextRequest) {
  const { question } = await request.json();
  const token = cookies().get("fas_token")?.value;
  const apiResponse = await fastapiFetch("/agent/query/router", {
    method: "POST",
    body: JSON.stringify({ question }),
    headers: { Authorization: `Bearer ${token}` },
  });
  return NextResponse.json(apiResponse);
}
```
**Tests**:
- React Testing Library tests for ChatInput and routing logic.
- Integration test mocking the API proxy to ensure agent metadata renders correctly.

### Phase 5: Deployment & Observability Enhancements
**Objective**: Prepare Docker/Render configs for both FastAPI and Next.js deployments, wire environment variables (DB URL, API base), and add structured logging for agent routing + auth events.
**Code Proposal**:
```dockerfile
# web/Dockerfile
FROM node:24-alpine AS builder
WORKDIR /app
COPY web/package*.json ./
RUN npm install
COPY web .
RUN npm run build

FROM node:24-alpine
WORKDIR /app
COPY --from=builder /app/.next .next
COPY --from=builder /app/public public
CMD ["npm", "run", "start"]
```
**Tests**:
- Smoke-test deployment via Render preview environments.
- Observability tests verifying logs emit agent name, request ID, and latency metrics.

## Consolidated Checklist
- [x] Update database schema and repository layer for agent action logging.
- [x] Expose FastAPI routes for creating/listing agent actions scoped to authenticated users.
- [x] Implement router agent classification endpoint with logging and fallback behavior.
- [x] Add username/password authentication plus JWT middleware, keeping fields ready for Google OAuth.
- [x] Scaffold Next.js app with auth pages, chat dashboard, router query proxy, and action logs UI.
- [x] Add deployment artifacts (Dockerfiles/Render configs) and structured logging adjustments.

## Notes
- Ensure Alembic migration scripts are created for new tables (`users`, `agent_actions`) and applied in Docker containers (e.g., `alembic revision -m "add users table"`, `alembic revision -m "add agent actions table"`, followed by `alembic upgrade head` in the entrypoint).
- Router agent confidence should be logged; consider threshold-based manual confirmation in UI if classification is ambiguous.
- Keep secrets (JWT keys, DB URL, OAuth IDs) managed via Render environment variables; avoid hardcoding.
- Prepare adapters for swapping username/password auth with NextAuth Google provider by abstracting token verification logic on the FastAPI side.
- Persist authentication via HTTP-only cookies set by Next.js Route Handlers so tokens never leak to client JS and swapping to OAuth later is trivial.
- Document migration order (create `users` table before `agent_actions` because of FK dependency) and add instructions to run Alembic inside Docker entrypoint so Render deploys automatically apply schema changes.
