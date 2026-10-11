const gbp = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  maximumFractionDigits: 0,
});

const signedGbp = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  maximumFractionDigits: 0,
  signDisplay: 'exceptZero',
});

const gbpPence = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const integer = new Intl.NumberFormat('en-GB');

export const formatGbp = (value: number): string => gbp.format(value);
export const formatSignedGbp = (value: number): string => signedGbp.format(value);
export const formatGbpPence = (value: number): string => gbpPence.format(value);
export const formatInteger = (value: number): string => integer.format(value);
