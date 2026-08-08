export function RealisticAvatar({ name, id }: { name: string; id?: string }) {
  // We use deterministic mapping to ensure genders match exactly
  const avatarMap: Record<string, string> = {
    "CAND-001": "/avatars/avatar_1.png", // Sarah (F)
    "CAND-002": "/avatars/avatar_2.png", // Alex (M)
    "CAND-003": "/avatars/avatar_5.png", // Emily (F)
    "CAND-004": "/avatars/avatar_3.png", // David (M)
    "CAND-005": "/avatars/avatar_4.png", // Michael (M)
    "CAND-006": "/avatars/avatar_f3_1786220811963.png", // Wendy (F)
    "CAND-007": "/avatars/avatar_m4_1786220889406.png", // Ethan (M)
    "CAND-008": "https://i.pravatar.cc/150?u=CAND-008", // Harold (M)
    "CAND-009": "/avatars/avatar_f4_1786220823496.png", // Zara (F)
    "CAND-010": "https://i.pravatar.cc/150?u=CAND-010", // Gerald (M)
    "CAND-011": "/avatars/avatar_f5_1786220837500.png", // Mia (F)
    "CAND-012": "https://i.pravatar.cc/150?u=CAND-012", // Chen Wei (M)
    "CAND-013": "https://i.pravatar.cc/150?u=CAND-013", // Ravi Patel (M)
    "CAND-014": "/avatars/avatar_f6_1786220847324.png", // Bethany (F)
    "CAND-015": "https://i.pravatar.cc/150?u=CAND-015", // Noah Kim (M)
    "CAND-016": "/avatars/avatar_f7_1786220857541.png", // Isabella (F)
    "CAND-017": "https://i.pravatar.cc/150?u=CAND-017", // Tyler Brooks (M)
    "CAND-018": "/avatars/avatar_f8_1786220867953.png", // Diane (F)
    "CAND-019": "https://i.pravatar.cc/150?u=CAND-019", // Frank DeLuca (M)
    "CAND-020": "/avatars/avatar_f9_1786220878924.png", // Priyanka (F)
  };

  const fallbackUrl = `https://i.pravatar.cc/150?u=${name}`;
  const avatarUrl = id && avatarMap[id] ? avatarMap[id] : fallbackUrl;

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden rounded-[14px]">
      <img 
        src={avatarUrl} 
        alt={name} 
        className="w-full h-full object-cover transition-transform duration-700 hover:scale-110"
      />
    </div>
  );
}
