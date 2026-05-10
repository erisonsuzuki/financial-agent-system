import { describe, expect, it } from "vitest";
import { formatUtcTimestamp } from "../app/lib/datetime";

describe("formatUtcTimestamp", () => {
  it("formats ISO timestamp in deterministic UTC format", () => {
    expect(formatUtcTimestamp("2026-01-01T10:20:30Z")).toBe("2026-01-01 10:20:30 UTC");
  });

  it("normalizes timezone offsets into UTC", () => {
    expect(formatUtcTimestamp("2026-01-01T10:20:30-03:00")).toBe("2026-01-01 13:20:30 UTC");
  });

  it("returns fallback for null and invalid values", () => {
    expect(formatUtcTimestamp(null, "Price time unavailable")).toBe("Price time unavailable");
    expect(formatUtcTimestamp("not-a-date", "Price time unavailable")).toBe("Price time unavailable");
  });
});
