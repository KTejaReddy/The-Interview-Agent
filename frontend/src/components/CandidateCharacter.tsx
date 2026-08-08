import { useMemo } from 'react';

interface CandidateCharacterProps {
  name: string;
  role: string;
  readiness: number;
  isHovered?: boolean;
}

export function CandidateCharacter({ name, role, readiness, isHovered }: CandidateCharacterProps) {
  // Use a pseudo-random deterministic generator based on the candidate's name to pick colors/styles
  const seed = useMemo(() => name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0), [name]);

  // Skin tones (warm natural tones)
  const skinTones = ['#F5D0C5', '#E3A68F', '#C6866D', '#8D5B4C', '#5C3826'];
  const skinTone = skinTones[seed % skinTones.length];

  // Shirt colors (muted editorial colors)
  const shirtColors = ['#F26457', '#3B82F6', '#22C55E', '#F59E0B', '#8B5CF6', '#1C1C1C'];
  const shirtColor = shirtColors[(seed * 2) % shirtColors.length];
  
  // Posture logic based on readiness
  const isConfident = readiness >= 70;
  const isDeveloping = readiness < 50;

  // Derive an accessory based on role
  const isData = role.toLowerCase().includes('data');
  const isBackend = role.toLowerCase().includes('backend');
  const isAI = role.toLowerCase().includes('ai');

  return (
    <div className={`relative w-full h-full flex items-center justify-center transition-transform duration-500 ${isHovered ? 'scale-105' : ''}`}>
      <svg viewBox="0 0 200 200" className="w-full h-full drop-shadow-md">
        <defs>
          <clipPath id="body-clip">
            <rect x="50" y="100" width="100" height="100" rx="40" />
          </clipPath>
        </defs>

        {/* Body */}
        <g className="animate-breathe origin-bottom">
          <rect x="50" y="90" width="100" height="110" rx="30" fill={shirtColor} />
          
          {/* Posture adjustments */}
          {isConfident ? (
            // Shoulders back (chest out)
            <path d="M 60 110 Q 100 90 140 110" stroke="rgba(0,0,0,0.1)" strokeWidth="4" fill="none" />
          ) : isDeveloping ? (
            // Slouch
            <path d="M 60 100 Q 100 120 140 100" stroke="rgba(0,0,0,0.1)" strokeWidth="4" fill="none" />
          ) : null}

          {/* Accessory based on role */}
          {isData && (
            <rect x="85" y="140" width="30" height="20" rx="2" fill="#E6DFD3" />
          )}
          {isBackend && (
            <path d="M 70 150 L 130 150 L 120 180 L 80 180 Z" fill="#333333" />
          )}
          {isAI && (
            <circle cx="100" cy="130" r="15" fill="none" stroke="#FAF9F6" strokeWidth="3" opacity="0.8" />
          )}

          {/* Head & Neck */}
          <g className={`transition-transform duration-700 ${isHovered ? 'translate-x-1' : ''}`}>
            <rect x="90" y="70" width="20" height="30" fill={skinTone} />
            <circle cx="100" cy="65" r="35" fill={skinTone} />
            
            {/* Hair (simple shape based on seed) */}
            {seed % 2 === 0 ? (
              <path d="M 65 65 Q 100 10 135 65 Q 140 30 100 20 Q 60 30 65 65" fill="#1C1C1C" />
            ) : (
              <path d="M 62 60 A 38 38 0 0 1 138 60 A 20 20 0 0 0 62 60" fill="#4D4D4D" />
            )}

            {/* Eyes */}
            <g className="animate-blink">
              <circle cx="85" cy="60" r="4" fill="#1A1A1A" />
              <circle cx="115" cy="60" r="4" fill="#1A1A1A" />
              
              {/* Pupils move on hover */}
              <circle cx={isHovered ? 87 : 85} cy="60" r="1.5" fill="white" className="transition-all duration-300" />
              <circle cx={isHovered ? 117 : 115} cy="60" r="1.5" fill="white" className="transition-all duration-300" />
            </g>

            {/* Smile / Expression */}
            <path 
              d={isHovered ? "M 90 75 Q 100 85 110 75" : isDeveloping ? "M 92 78 L 108 78" : "M 92 75 Q 100 80 108 75"} 
              stroke="#1A1A1A" 
              strokeWidth="2" 
              fill="none" 
              strokeLinecap="round" 
              className="transition-all duration-300"
            />
          </g>
        </g>
      </svg>
    </div>
  );
}
