// Common country codes for phone number selection
export const countryCodes = [
  { code: '+91', country: 'India', flag: '🇮🇳', maxLength: 10 },
  { code: '+1', country: 'USA', flag: '🇺🇸', maxLength: 10 },
  { code: '+44', country: 'UK', flag: '🇬🇧', maxLength: 10 },
  { code: '+61', country: 'Australia', flag: '🇦🇺', maxLength: 9 },
  { code: '+971', country: 'UAE', flag: '🇦🇪', maxLength: 9 },
  { code: '+65', country: 'Singapore', flag: '🇸🇬', maxLength: 8 },
  { code: '+81', country: 'Japan', flag: '🇯🇵', maxLength: 10 },
  { code: '+86', country: 'China', flag: '🇨🇳', maxLength: 11 },
  { code: '+49', country: 'Germany', flag: '🇩🇪', maxLength: 11 },
  { code: '+33', country: 'France', flag: '🇫🇷', maxLength: 9 },
  { code: '+39', country: 'Italy', flag: '🇮🇹', maxLength: 10 },
  { code: '+34', country: 'Spain', flag: '🇪🇸', maxLength: 9 },
  { code: '+55', country: 'Brazil', flag: '🇧🇷', maxLength: 11 },
  { code: '+7', country: 'Russia', flag: '🇷🇺', maxLength: 10 },
  { code: '+27', country: 'South Africa', flag: '🇿🇦', maxLength: 9 },
  { code: '+82', country: 'South Korea', flag: '🇰🇷', maxLength: 10 },
  { code: '+60', country: 'Malaysia', flag: '🇲🇾', maxLength: 10 },
  { code: '+63', country: 'Philippines', flag: '🇵🇭', maxLength: 10 },
  { code: '+66', country: 'Thailand', flag: '🇹🇭', maxLength: 9 },
  { code: '+84', country: 'Vietnam', flag: '🇻🇳', maxLength: 10 },
];

export const getCountryByCode = (code) => {
  return countryCodes.find(c => c.code === code) || countryCodes[0];
};

export default countryCodes;
