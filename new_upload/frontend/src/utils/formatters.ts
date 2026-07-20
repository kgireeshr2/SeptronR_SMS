import { format, parseISO, isValid } from 'date-fns';

// ── School-configured date format ───────────────────────────────────────────
// The school stores a token like "DD/MM/YYYY"; date-fns uses "dd/MM/yyyy".
// A single active format is held module-side so formatDate() works everywhere
// (tables, .map() render callbacks, non-component code) without prop-drilling.
// It's seeded from localStorage so there is no flash on hard reload, and updated
// app-wide by useSchoolFormats() once the school settings load.
const DATE_FORMAT_STORAGE_KEY = 'sms-date-format';
const DEFAULT_DATE_FORMAT = 'dd/MM/yyyy';

/** Convert a school date-format token ("DD/MM/YYYY") to a date-fns pattern ("dd/MM/yyyy"). */
export const toDateFnsFormat = (raw?: string | null): string => {
  if (!raw) return DEFAULT_DATE_FORMAT;
  const converted = raw.replace(/D/g, 'd').replace(/Y/g, 'y');
  // Must look like a real day/month/year pattern, else fall back.
  return /d/.test(converted) && /M/.test(converted) && /y/.test(converted)
    ? converted
    : DEFAULT_DATE_FORMAT;
};

let activeDateFormat = DEFAULT_DATE_FORMAT;
try {
  const saved =
    typeof localStorage !== 'undefined' ? localStorage.getItem(DATE_FORMAT_STORAGE_KEY) : null;
  if (saved) activeDateFormat = saved;
} catch {
  /* localStorage unavailable — keep default */
}

/** Set the app-wide active date format (accepts a school token or a date-fns pattern). */
export const setActiveDateFormat = (raw?: string | null): void => {
  const fmt = raw && /[dD]/.test(raw) && /[yY]/.test(raw) ? toDateFnsFormat(raw) : DEFAULT_DATE_FORMAT;
  activeDateFormat = fmt;
  try {
    localStorage.setItem(DATE_FORMAT_STORAGE_KEY, fmt);
  } catch {
    /* ignore */
  }
};

/** The current app-wide date-fns date format. */
export const getActiveDateFormat = (): string => activeDateFormat;

/**
 * Format paise/cents to currency string: 150000 → "₹1,500.00"
 */
export const formatCurrency = (
  paise: number,
  currency = 'INR',
  locale = 'en-IN'
): string => {
  const amount = paise / 100;
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(amount);
};

/**
 * Format an ISO date (string/Date) to the school's configured format.
 * "2024-01-15" → "15/01/2024" (when the school uses DD/MM/YYYY).
 * Pass `fmt` to override the active format for a specific call.
 */
export const formatDate = (
  dateStr?: string | number | Date | null,
  fmt?: string
): string => {
  if (!dateStr) return '—';
  try {
    const date =
      typeof dateStr === 'string' ? parseISO(dateStr) : new Date(dateStr as number | Date);
    if (!isValid(date)) return String(dateStr);
    return format(date, fmt ?? activeDateFormat);
  } catch {
    return String(dateStr);
  }
};

/**
 * Format an ISO datetime to the school's date format + time (HH:mm).
 */
export const formatDateTime = (
  dateStr?: string | number | Date | null,
  fmt?: string
): string => {
  if (!dateStr) return '—';
  return formatDate(dateStr, fmt ?? `${activeDateFormat} HH:mm`);
};

/**
 * Truncate text to a given length with ellipsis
 */
export const truncate = (text: string, length = 50): string =>
  text.length > length ? `${text.slice(0, length)}...` : text;

/**
 * Generate initials from full name: "John Doe" → "JD"
 */
export const getInitials = (name: string): string =>
  name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

/**
 * Format a phone number for display
 */
export const formatPhone = (phone: string): string => {
  if (!phone) return '—';
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 10) {
    return `+91 ${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
  }
  return phone;
};

/**
 * Format number with Indian locale separators
 */
export const formatNumber = (num: number): string =>
  new Intl.NumberFormat('en-IN').format(num);
