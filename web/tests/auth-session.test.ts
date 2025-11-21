import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET as getSession } from "../app/api/auth/session/route";

const originalFetch = global.fetch;

describe("auth session route", () => {
  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("returns 401 when no token is present", async () => {
    const request = new NextRequest(new Request("http://localhost/api/auth/session"));
    const res = await getSession(request);
    const body = await res.json();

    expect(res.status).toBe(401);
    expect(body).toEqual({ authenticated: false });
  });

  it("returns 401 when upstream responds 401", async () => {
    global.fetch = vi.fn().mockResolvedValue(new Response("", { status: 401 })) as unknown as typeof fetch;
    const request = new NextRequest(new Request("http://localhost/api/auth/session", { headers: { cookie: "fas_token=bad" } }));

    const res = await getSession(request);
    const body = await res.json();

    expect(res.status).toBe(401);
    expect(body).toEqual({ authenticated: false });
  });

  it("returns 503 when upstream is unavailable", async () => {
    global.fetch = vi.fn().mockResolvedValue(new Response("oops", { status: 500 })) as unknown as typeof fetch;
    const request = new NextRequest(new Request("http://localhost/api/auth/session", { headers: { cookie: "fas_token=down" } }));

    const res = await getSession(request);
    const body = await res.json();

    expect(res.status).toBe(503);
    expect(body).toEqual({ authenticated: false, error: "upstream_unavailable" });
  });
});
