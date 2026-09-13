import { countryCodes, getCountryByCode } from '../src/data/countryCodes';

describe('Country Codes', () => {
  describe('countryCodes array', () => {
    test('contains India as first option', () => {
      expect(countryCodes[0].code).toBe('+91');
      expect(countryCodes[0].country).toBe('India');
    });

    test('all entries have required fields', () => {
      countryCodes.forEach(country => {
        expect(country).toHaveProperty('code');
        expect(country).toHaveProperty('country');
        expect(country).toHaveProperty('flag');
        expect(country).toHaveProperty('maxLength');
        expect(typeof country.maxLength).toBe('number');
      });
    });

    test('contains major countries', () => {
      const codes = countryCodes.map(c => c.code);
      expect(codes).toContain('+1');  // USA
      expect(codes).toContain('+44'); // UK
      expect(codes).toContain('+91'); // India
      expect(codes).toContain('+971'); // UAE
    });
  });

  describe('getCountryByCode', () => {
    test('returns correct country for valid code', () => {
      const india = getCountryByCode('+91');
      expect(india.country).toBe('India');
      expect(india.maxLength).toBe(10);
    });

    test('returns default (India) for invalid code', () => {
      const result = getCountryByCode('+999');
      expect(result.code).toBe('+91');
    });
  });
});
