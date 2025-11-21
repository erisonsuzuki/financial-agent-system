import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET as getAssetsSummary } from "../app/api/assets-summary/route";

const originalFetch = global.fetch;

describe("assets-summary route", () => {
  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("returns 401 when no auth token is present", async () => {
    const request = new NextRequest(new Request("http://localhost/api/assets-summary"));
    const res = await getAssetsSummary(request);
    const body = await res.json();

    expect(res.status).toBe(401);
    expect(body).toEqual({ error: "Unauthorized" });
  });

  it("returns data and marks failing analyses with error field", async () => {
    const fetchMock = vi.fn();
    global.fetch = fetchMock as unknown as typeof fetch;

    fetchMock.mockImplementation((url: string) => {
      if (url.includes("/assets/") && !url.includes("/analysis")) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: 1, ticker: "OK", name: "Ok Asset" }, { id: 2, ticker: "BAD", name: "Bad Asset" }])),
        );
      }
      if (url.includes("/assets/OK/analysis")) {
        return Promise.resolve(new Response(JSON.stringify({ total_quantity: 10, average_price: "5.5" })));
      }
      if (url.includes("/assets/BAD/analysis")) {
        return Promise.reject(new Error("upstream failure"));
      }
      return Promise.reject(new Error("unexpected url " + url));
    });

    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const request = new NextRequest(
      new Request("http://localhost/api/assets-summary", { headers: { cookie: "fas_token=testtoken" } }),
    );

    const res = await getAssetsSummary(request);
    const body = await res.json();

    expect(res.status).toBe(200);
    expect(body).toEqual([
      { id: 1, name: "Ok Asset", ticker: "OK", units: 10, averagePrice: 5.5 },
      { id: 2, name: "Bad Asset", ticker: "BAD", units: 0, averagePrice: 0, error: "analysis_unavailable" },
    ]);
    expect(consoleSpy).toHaveBeenCalled();
  });
});
