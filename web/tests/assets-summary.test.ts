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

  it("returns bulk summary data and preserves asset errors", async () => {
    const fetchMock = vi.fn();
    global.fetch = fetchMock as unknown as typeof fetch;

    fetchMock.mockImplementation((url: string) => {
      if (url.includes("/assets/summary")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              {
                id: 1,
                ticker: "OK",
                name: "Ok Asset",
                units: 10,
                average_price: "5.5",
                current_price: "6.5",
                pl_value: "10.0",
                pl_percent: "20.0",
                dividends: "1.2",
                total_return_value: "11.2",
                total_return_percent: "22.4",
                price_fetched_at: "2026-01-01T10:00:00Z",
                is_stale: false,
              },
              {
                id: 2,
                ticker: "BAD",
                name: "Bad Asset",
                units: 0,
                average_price: "0",
                current_price: null,
                pl_value: null,
                pl_percent: null,
                dividends: "0",
                total_return_value: null,
                total_return_percent: null,
                price_fetched_at: null,
                is_stale: false,
                error: "analysis_unavailable",
              },
            ]),
          ),
        );
      }
      return Promise.reject(new Error("unexpected url " + url));
    });

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
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/assets/summary"), expect.any(Object));
  });

  it("forwards refresh=true to the bulk summary endpoint", async () => {
    const fetchMock = vi.fn();
    global.fetch = fetchMock as unknown as typeof fetch;

    fetchMock.mockImplementation((url: string) => {
      if (url.includes("/assets/summary?refresh=true")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              {
                id: 1,
                ticker: "OK",
                name: "Ok Asset",
                units: 10,
                average_price: "5.5",
                current_price: null,
                pl_value: null,
                pl_percent: null,
                dividends: "0",
                total_return_value: null,
                total_return_percent: null,
                price_fetched_at: null,
                is_stale: false,
              },
            ]),
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
      expect.stringContaining("/assets/summary?refresh=true"),
      expect.any(Object),
    );
  });
});
