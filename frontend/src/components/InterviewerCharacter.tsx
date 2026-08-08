// No React import needed

type InterviewerState = 'idle' | 'thinking' | 'speaking' | 'listening' | 'frustrated';

interface InterviewerCharacterProps {
  state: InterviewerState;
}

export function InterviewerCharacter({ state }: InterviewerCharacterProps) {
  // Alex: Professional interviewer (Navy suit, glasses, mature but warm)
  
  const isThinking = state === 'thinking';
  const isSpeaking = state === 'speaking';
  const isFrustrated = state === 'frustrated';

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <svg viewBox="0 0 200 200" className="w-full h-full drop-shadow-lg">
        {/* Body */}
        <g className={`origin-bottom ${isThinking ? 'animate-breathe scale-[1.02]' : 'animate-breathe'}`}>
          {/* Suit Jacket */}
          <rect x="50" y="90" width="100" height="110" rx="30" fill="#1C1C1C" />
          {/* Shirt */}
          <path d="M 80 90 L 100 130 L 120 90 Z" fill="#FAF9F6" />
          {/* Tie */}
          <path d="M 95 105 L 100 140 L 105 105 Z" fill="#3B82F6" />

          {/* Head & Neck */}
          <g className={`transition-transform duration-500 ${isThinking ? 'rotate-[-5deg] translate-x-1' : ''} ${isFrustrated ? 'translate-y-1' : ''}`}>
            <rect x="90" y="70" width="20" height="30" fill="#E3A68F" />
            <circle cx="100" cy="65" r="32" fill="#E3A68F" />
            
            {/* Hair (Professional, neat) */}
            <path d="M 68 60 C 68 20 132 20 132 60 C 132 40 100 15 68 60 Z" fill="#2D2D2D" />
            
            {/* Glasses */}
            <rect x="75" y="55" width="20" height="12" rx="2" fill="none" stroke="#1C1C1C" strokeWidth="2" />
            <rect x="105" y="55" width="20" height="12" rx="2" fill="none" stroke="#1C1C1C" strokeWidth="2" />
            <line x1="95" y1="61" x2="105" y2="61" stroke="#1C1C1C" strokeWidth="2" />

            {/* Eyes */}
            <g className="animate-blink">
              <circle cx="85" cy="61" r="2" fill="#1C1C1C" />
              <circle cx="115" cy="61" r="2" fill="#1C1C1C" />
            </g>

            {/* Eyebrows */}
            <g className="transition-all duration-300">
              {isFrustrated ? (
                <>
                  <line x1="75" y1="48" x2="90" y2="52" stroke="#1C1C1C" strokeWidth="3" strokeLinecap="round" />
                  <line x1="125" y1="48" x2="110" y2="52" stroke="#1C1C1C" strokeWidth="3" strokeLinecap="round" />
                </>
              ) : isThinking ? (
                <>
                  <line x1="75" y1="50" x2="90" y2="48" stroke="#1C1C1C" strokeWidth="3" strokeLinecap="round" />
                  <line x1="125" y1="48" x2="110" y2="48" stroke="#1C1C1C" strokeWidth="3" strokeLinecap="round" />
                </>
              ) : (
                <>
                  <line x1="75" y1="48" x2="90" y2="48" stroke="#1C1C1C" strokeWidth="3" strokeLinecap="round" />
                  <line x1="125" y1="48" x2="110" y2="48" stroke="#1C1C1C" strokeWidth="3" strokeLinecap="round" />
                </>
              )}
            </g>

            {/* Mouth */}
            <path 
              d={isSpeaking ? "M 92 78 Q 100 85 108 78" : isFrustrated ? "M 92 78 L 108 78" : "M 95 78 L 105 78"} 
              stroke="#1C1C1C" 
              strokeWidth="2" 
              fill={isSpeaking ? "#1C1C1C" : "none"} 
              strokeLinecap="round" 
              className={`transition-all duration-200 ${isSpeaking ? 'animate-pulse' : ''}`}
            />
          </g>
        </g>
      </svg>
    </div>
  );
}
