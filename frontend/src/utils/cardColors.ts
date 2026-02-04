/**
 * Bank-to-color mapping utility for credit card UI.
 *
 * Provides stable brand colors for known banks with a neutral fallback.
 * Normalizes bank names using accent folding and whitespace removal.
 */

/**
 * Normalizes a bank name by:
 * 1. Trimming whitespace
 * 2. Converting to lowercase
 * 3. Removing diacritic marks (accent folding)
 * 4. Removing all whitespace
 *
 * @example
 * normalizeBankName("Ualá") // returns "uala"
 * normalizeBankName("  ICBC  ") // returns "icbc"
 * normalizeBankName("Mercado Pago") // returns "mercadopago"
 * normalizeBankName("Banco Nación") // returns "banconacion"
 */
function normalizeBankName(bank: string): string {
  return bank
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove combining diacritical marks
    .replace(/\s+/g, ''); // Remove all whitespace
}

/**
 * Map of normalized bank names to their brand colors.
 */
const BANK_COLORS: Record<string, string> = {
  icbc: '#D90000',
  santander: '#EC0000',
  bbva: '#004481',
  galicia: '#FF6600',
  naranja: '#FF5000',
  uala: '#7B2CBF',
  mercadopago: '#009EE3',
  banconacion: '#003087',
  bersa: '#007A33',
  bancodesantafe: '#00843D',
  bancociudad: '#FFB800',
};

/**
 * Fallback color for unknown or empty bank names.
 */
const FALLBACK_COLOR = '#6B7280';

/**
 * Returns the brand background color for a given bank name.
 *
 * @param bank - The bank name (e.g., "ICBC", "Ualá", "Mercado Pago")
 * @returns The bank's brand color, or a neutral gray fallback if unknown
 *
 * @example
 * getCardBackgroundColor('ICBC') // returns '#D90000'
 * getCardBackgroundColor('Ualá') // returns '#7B2CBF'
 * getCardBackgroundColor('Unknown Bank') // returns '#6B7280'
 */
export function getCardBackgroundColor(bank: string): string {
  if (!bank) {
    return FALLBACK_COLOR;
  }

  const normalized = normalizeBankName(bank);
  return BANK_COLORS[normalized] || FALLBACK_COLOR;
}

/**
 * Returns a style object with the bank's brand color as the background.
 *
 * @param bank - The bank name (e.g., "ICBC", "Ualá", "Mercado Pago")
 * @returns An object with a background property set to the bank's brand color
 *
 * @example
 * getCardStyle('ICBC') // returns { background: '#D90000' }
 * getCardStyle('Unknown Bank') // returns { background: '#6B7280' }
 */
export function getCardStyle(bank: string): { background: string } {
  return {
    background: getCardBackgroundColor(bank),
  };
}
