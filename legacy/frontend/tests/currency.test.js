import { formatPrice, CURRENCY_SYMBOL, convertToINR } from '../src/utils/currency';

describe('Currency Utils', () => {
  describe('formatPrice', () => {
    test('formats positive numbers with INR symbol', () => {
      expect(formatPrice(1000)).toBe('₹1,000');
      expect(formatPrice(299.99)).toBe('₹299.99');
    });

    test('formats large numbers with Indian numbering system', () => {
      expect(formatPrice(100000)).toBe('₹1,00,000');
      expect(formatPrice(10000000)).toBe('₹1,00,00,000');
    });

    test('handles zero and null values', () => {
      expect(formatPrice(0)).toBe('₹0');
      expect(formatPrice(null)).toBe('₹0');
      expect(formatPrice(undefined)).toBe('₹0');
    });

    test('can hide currency symbol', () => {
      expect(formatPrice(1000, false)).toBe('1,000');
    });
  });

  describe('CURRENCY_SYMBOL', () => {
    test('should be Indian Rupee symbol', () => {
      expect(CURRENCY_SYMBOL).toBe('₹');
    });
  });

  describe('convertToINR', () => {
    test('converts USD to INR with default rate', () => {
      expect(convertToINR(100)).toBe(8300);
    });

    test('converts USD to INR with custom rate', () => {
      expect(convertToINR(100, 85)).toBe(8500);
    });
  });
});
