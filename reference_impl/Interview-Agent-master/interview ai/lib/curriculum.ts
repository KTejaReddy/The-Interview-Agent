import curriculumData from "@/data/curriculum.json";
import { Curriculum, CurriculumDay, CurriculumModule } from "@/types";

const curriculum = curriculumData as Curriculum;

export function getCurriculum(): Curriculum {
  return curriculum;
}

export function getDayInfo(dayNumber: number): CurriculumDay | undefined {
  return curriculum.days.find((d) => d.day === dayNumber);
}

export function getModuleForDay(dayNumber: number): CurriculumModule | undefined {
  return curriculum.modules.find(
    (m) => dayNumber >= m.days[0] && dayNumber <= m.days[1]
  );
}

/**
 * Build a summary string of a day's context for use in prompts.
 */
export function formatDayContext(dayNumber: number): string {
  const day = getDayInfo(dayNumber);
  if (!day) return "";
  const module = getModuleForDay(dayNumber);
  return `Day ${day.day} — "${day.title}" (Module: ${module?.title ?? "Unknown"})
  Tools: ${day.tools.join(", ")}
  Learning Objectives:
  ${day.objectives.map((o) => `  • ${o}`).join("\n")}`;
}
