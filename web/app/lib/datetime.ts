function padTwoDigits(value: number): string {
  return value.toString().padStart(2, "0");
}

function toDate(value: string | Date): Date {
  if (value instanceof Date) {
    return value;
  }
  return new Date(value);
}

export function formatUtcTimestamp(
  value: string | Date | null | undefined,
  fallback = "Timestamp unavailable",
): string {
  if (!value) {
    return fallback;
  }

  const parsed = toDate(value);
  if (Number.isNaN(parsed.getTime())) {
    return fallback;
  }

  const year = parsed.getUTCFullYear();
  const month = padTwoDigits(parsed.getUTCMonth() + 1);
  const day = padTwoDigits(parsed.getUTCDate());
  const hours = padTwoDigits(parsed.getUTCHours());
  const minutes = padTwoDigits(parsed.getUTCMinutes());
  const seconds = padTwoDigits(parsed.getUTCSeconds());

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds} UTC`;
}
