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

  switch (page) {
    case "interview":
      return <Interview onNavigate={navigate} />;
    case "feedback":
      return <Feedback onNavigate={navigate} />;
    default:
      return <Landing onNavigate={navigate} />;
  }
}

export default function App() {
  return (
    <InterviewProvider>
      <AppShell />
    </InterviewProvider>
  );
}

export { useInterview };