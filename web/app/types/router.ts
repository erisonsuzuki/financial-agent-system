export interface RouterResponse {
  agent: string;
  confidence?: number | null;
  answer: string;
  routing_metadata?: Record<string, unknown> | null;
}

export interface AgentAction {
  id: number;
  agent_name: string;
  question: string;
  response: string;
  tool_calls?: Record<string, unknown> | null;
  created_at: string;
}
