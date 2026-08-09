import { useEffect, useState } from "react";
import { InterviewProvider, useInterview } from "./context/InterviewContext";
import { Feedback } from "./pages/Feedback";
import { Interview } from "./pages/Interview";
import { Landing } from "./pages/Landing";
import type { Page } from "./types";

function AppShell() {
  const [page, setPage] = useState<Page>("landing");
  const { resumedPage } = useInterview();

  // Auto-navigate to the active page when a session is restored from
  // localStorage (page refresh mid-interview).
  useEffect(() => {
    if (resumedPage) {
      setPage(resumedPage);
    }
  }, [resumedPage]);

  const navigate = (next: Page) => {
    setPage(next);
    window.scrollTo({ top: 0 });
  };

  // Subtle cross-fade + rise when switching major application states.
  const pageEl =
    page === "interview"
      ? <Interview onNavigate={navigate} />
      : page === "feedback"
        ? <Feedback onNavigate={navigate} />
        : <Landing onNavigate={navigate} />;

  return (
    <div key={page} className="animate-fade-up" style={{ animationDuration: "0.38s" }}>
      {pageEl}
    </div>
  );
}

export default function App() {
  return (
    <InterviewProvider>
      <AppShell />
    </InterviewProvider>
  );
}

export { useInterview };
