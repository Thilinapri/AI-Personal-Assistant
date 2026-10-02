export function formatDate(
  value?: string | null,
): string {
  if (!value?.trim()) {
    return "No date";
  }

  const match = value
    .trim()
    .match(
      /^(\d{4})-(\d{2})-(\d{2})$/,
    );

  if (!match) {
    return value;
  }

  const [
    ,
    year,
    month,
    day,
  ] = match;

  const parsed =
    new Date(
      Number(year),
      Number(month) - 1,
      Number(day),
    );

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
    },
  ).format(parsed);
}


export function formatTime(
  value?: string | null,
): string {
  if (!value?.trim()) {
    return "No time";
  }

  const match = value
    .trim()
    .match(
      /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/,
    );

  if (!match) {
    return value;
  }

  const [
    ,
    hour,
    minute,
  ] = match;

  const parsed =
    new Date(
      2000,
      0,
      1,
      Number(hour),
      Number(minute),
    );

  return new Intl.DateTimeFormat(
    "en-US",
    {
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(parsed);
}


export function parseDateTime(
  value?: string | null,
): Date | null {
  if (!value?.trim()) {
    return null;
  }

  const normalized =
    value.includes("T")
      ? value
      : value.replace(
          " ",
          "T",
        );

  const parsed =
    new Date(normalized);

  if (
    Number.isNaN(
      parsed.getTime(),
    )
  ) {
    return null;
  }

  return parsed;
}


export function formatDateTime(
  value?: string | null,
): string {
  const parsed =
    parseDateTime(value);

  if (!parsed) {
    return (
      value?.trim() ||
      "Not scheduled"
    );
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(parsed);
}


export function formatMemorySchedule(
  date?: string | null,
  time?: string | null,
): string {
  const hasDate =
    Boolean(date?.trim());

  const hasTime =
    Boolean(time?.trim());

  if (
    !hasDate &&
    !hasTime
  ) {
    return "No date or time";
  }

  if (
    hasDate &&
    hasTime
  ) {
    return `${formatDate(date)} · ${formatTime(time)}`;
  }

  if (hasDate) {
    return formatDate(date);
  }

  return formatTime(time);
}