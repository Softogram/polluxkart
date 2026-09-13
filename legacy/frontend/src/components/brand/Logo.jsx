import React from 'react';

const Logo = ({ size = 'default', showText = true, className = '' }) => {
  const sizes = {
    small: { icon: 28, text: 'text-lg' },
    default: { icon: 36, text: 'text-xl' },
    large: { icon: 48, text: 'text-2xl' },
    xlarge: { icon: 64, text: 'text-3xl' },
  };

  const { icon: iconSize, text: textSize } = sizes[size] || sizes.default;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Logo Icon - Shopping bag with PK initials */}
      <svg
        width={iconSize}
        height={iconSize}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        <defs>
          <linearGradient id="bgGradLogo" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="hsl(174, 72%, 40%)" />
            <stop offset="100%" stopColor="hsl(174, 72%, 32%)" />
          </linearGradient>
          <linearGradient id="bagGradLogo" x1="20" y1="8" x2="44" y2="48" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="100%" stopColor="#F0FDFA" />
          </linearGradient>
          <linearGradient id="accentGradLogo" x1="44" y1="8" x2="56" y2="20" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="hsl(90, 60%, 55%)" />
            <stop offset="100%" stopColor="hsl(90, 60%, 45%)" />
          </linearGradient>
        </defs>
        
        {/* Background */}
        <rect x="4" y="4" width="56" height="56" rx="14" fill="url(#bgGradLogo)" />
        
        {/* Shopping bag top */}
        <path d="M22 18C22 14.6863 24.6863 12 28 12H36C39.3137 12 42 14.6863 42 18V20H22V18Z" fill="url(#bagGradLogo)" fillOpacity="0.9" />
        
        {/* Shopping bag body */}
        <rect x="20" y="20" width="24" height="30" rx="3" fill="url(#bagGradLogo)" fillOpacity="0.95" />
        
        {/* Bag handle */}
        <path d="M26 16V12C26 10.8954 26.8954 10 28 10H36C37.1046 10 38 10.8954 38 12V16" stroke="url(#bagGradLogo)" strokeWidth="2.5" strokeLinecap="round" fill="none" />
        
        {/* K design inside */}
        <path d="M28 28V42M28 35L36 28M32 35L36 42" stroke="hsl(174, 72%, 35%)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        
        {/* Star sparkle */}
        <circle cx="50" cy="14" r="6" fill="url(#accentGradLogo)" />
        <path d="M50 10L51 13H54L51.5 15L52.5 18L50 16L47.5 18L48.5 15L46 13H49L50 10Z" fill="white" fillOpacity="0.95" />
        
        {/* Cart wheels */}
        <circle cx="26" cy="52" r="3" fill="white" fillOpacity="0.85" />
        <circle cx="38" cy="52" r="3" fill="white" fillOpacity="0.85" />
        
        {/* Small sparkles */}
        <circle cx="48" cy="26" r="1.5" fill="url(#accentGradLogo)" fillOpacity="0.8" />
      </svg>

      {/* Logo Text */}
      {showText && (
        <span className={`font-heading font-bold ${textSize}`}>
          <span className="text-foreground">Pollux</span>
          <span className="text-primary">Kart</span>
        </span>
      )}
    </div>
  );
};

// Simplified icon-only version for favicon/small spaces
export const LogoIcon = ({ size = 32, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <defs>
      <linearGradient id="bgGradIcon" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#14B8A6" />
        <stop offset="100%" stopColor="#0D9488" />
      </linearGradient>
      <linearGradient id="bagGradIcon" x1="20" y1="8" x2="44" y2="48" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#FFFFFF" />
        <stop offset="100%" stopColor="#F0FDFA" />
      </linearGradient>
      <linearGradient id="accentGradIcon" x1="44" y1="8" x2="56" y2="20" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#A3E635" />
        <stop offset="100%" stopColor="#84CC16" />
      </linearGradient>
    </defs>
    
    <rect x="4" y="4" width="56" height="56" rx="14" fill="url(#bgGradIcon)" />
    <path d="M22 18C22 14.6863 24.6863 12 28 12H36C39.3137 12 42 14.6863 42 18V20H22V18Z" fill="url(#bagGradIcon)" fillOpacity="0.9" />
    <rect x="20" y="20" width="24" height="30" rx="3" fill="url(#bagGradIcon)" fillOpacity="0.95" />
    <path d="M26 16V12C26 10.8954 26.8954 10 28 10H36C37.1046 10 38 10.8954 38 12V16" stroke="url(#bagGradIcon)" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    <path d="M28 28V42M28 35L36 28M32 35L36 42" stroke="#0D9488" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="50" cy="14" r="6" fill="url(#accentGradIcon)" />
    <path d="M50 10L51 13H54L51.5 15L52.5 18L50 16L47.5 18L48.5 15L46 13H49L50 10Z" fill="white" fillOpacity="0.95" />
    <circle cx="26" cy="52" r="3" fill="white" fillOpacity="0.85" />
    <circle cx="38" cy="52" r="3" fill="white" fillOpacity="0.85" />
  </svg>
);

export default Logo;
