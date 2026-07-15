import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET as getSession } from "../app/api/auth/session/route";
import { POST as logout } from "../app/api/auth/logout/route";

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

describe("logout route", () => {
  it("expires the auth cookie for same-origin requests", async () => {
    const request = new NextRequest(new Request("http://localhost/api/auth/logout", { method: "POST", headers: { origin: "http://localhost" } }));

    const response = await logout(request);

    expect(response.status).toBe(204);
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(response.headers.get("set-cookie")).toContain("fas_token=");
    expect(response.headers.get("set-cookie")).toContain("Max-Age=0");
    expect(response.headers.get("set-cookie")).toContain("HttpOnly");
    expect(response.headers.get("set-cookie")).toContain("Path=/");
    expect(response.headers.get("set-cookie")).toContain("SameSite=lax");
  });

  it("rejects missing or cross-origin requests", async () => {
    const missingOrigin = new NextRequest(new Request("http://localhost/api/auth/logout", { method: "POST" }));
    const crossOrigin = new NextRequest(new Request("http://localhost/api/auth/logout", { method: "POST", headers: { origin: "https://example.com" } }));

    expect((await logout(missingOrigin)).status).toBe(403);
    expect((await logout(crossOrigin)).status).toBe(403);
  });
});
