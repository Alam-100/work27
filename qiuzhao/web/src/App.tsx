import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { CalendarPage } from "./pages/CalendarPage";
import { EventsPage } from "./pages/EventsPage";
import { JobsPage } from "./pages/JobsPage";
import { MorePage } from "./pages/MorePage";
import { ReviewPage } from "./pages/ReviewPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/jobs" replace />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/applications/:stem" element={<ApplicationsPage />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/review/:stem" element={<ReviewPage />} />
        <Route path="/more" element={<MorePage />} />
      </Routes>
    </AppShell>
  );
}
