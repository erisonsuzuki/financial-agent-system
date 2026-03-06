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
        return Promise.resolve(
          new Response(
            JSON.stringify({
              total_quantity: 10,
              average_price: "5.5",
              current_market_price: "6.5",
              financial_return_value: "10.0",
              financial_return_percent: "20.0",
              total_dividends_received: "1.2",
              total_return_value: "11.2",
              total_return_percent: "22.4",
              fetched_at: "2026-01-01T10:00:00Z",
              is_stale: false,
            }),
          ),
        );
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
      {
        id: 1,
        name: "Ok Asset",
        ticker: "OK",
        units: 10,
        averagePrice: 5.5,
        currentPrice: 6.5,
        plValue: 10,
        plPercent: 20,
        dividends: 1.2,
        totalReturnValue: 11.2,
        totalReturnPercent: 22.4,
        priceFetchedAt: "2026-01-01T10:00:00Z",
        isStale: false,
      },
      {
        id: 2,
        name: "Bad Asset",
        ticker: "BAD",
        units: 0,
        averagePrice: 0,
        currentPrice: null,
        plValue: null,
        plPercent: null,
        dividends: 0,
        totalReturnValue: null,
        totalReturnPercent: null,
        priceFetchedAt: null,
        isStale: false,
        error: "analysis_unavailable",
      },
    ]);
    expect(consoleSpy).toHaveBeenCalled();
  });

  it("forwards refresh=true to analysis endpoint", async () => {
    const fetchMock = vi.fn();
    global.fetch = fetchMock as unknown as typeof fetch;

    fetchMock.mockImplementation((url: string) => {
      if (url.includes("/assets/") && !url.includes("/analysis")) {
        return Promise.resolve(new Response(JSON.stringify([{ id: 1, ticker: "OK", name: "Ok Asset" }])));
      }
      if (url.includes("/assets/OK/analysis?refresh=true")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              total_quantity: 10,
              average_price: "5.5",
              current_market_price: null,
              financial_return_value: null,
              financial_return_percent: null,
            }),
          ),
        );
      }
      return Promise.reject(new Error("unexpected url " + url));
    });

    const request = new NextRequest(
      new Request("http://localhost/api/assets-summary?refresh=true", { headers: { cookie: "fas_token=testtoken" } }),
    );

    const res = await getAssetsSummary(request);
    const body = await res.json();
    expect(res.status).toBe(200);
    expect(body[0].dividends).toBe(0);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/assets/OK/analysis?refresh=true"),
      expect.any(Object),
    );
  });
});
