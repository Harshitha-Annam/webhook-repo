import { useEffect, useState } from "react";

function App() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    let lastFetchTime = new Date().toISOString();

    const fetchEvents = async () => {
      console.log(lastFetchTime);
      try {
        const res = await fetch(
          `http://localhost:5000/webhook/events?since=${lastFetchTime}`
        );
        const data = await res.json();
        console.log(data);
        // Update lastFetchTime to now
        lastFetchTime = new Date().toISOString();

        if (Array.isArray(data)) {
          setEvents(data); // overwrite old
        }
      } catch (err) {
        console.error("Failed to fetch events", err);
      }
    };

    fetchEvents();

    const interval = setInterval(fetchEvents, 15000);
    return () => clearInterval(interval);
  }, []);
  return (
    <div style={{ padding: "20px", fontFamily: "Segoe UI, sans-serif" }}>
      <h2>Webhook Events Feed</h2>

      {events.length === 0 && <p>No events in the last 15 seconds.</p>}

      {events.map((event) => (
        <div
          key={event._id}
          style={{
            background: "#f9f9f9",
            color: "black",
            margin: "10px 0",
            padding: "15px",
            borderLeft: `5px solid ${
              event.action === "PUSH"
                ? "#3498db"
                : event.action === "PULL REQUEST"
                ? "#f39c12"
                : event.action === "MERGE"
                ? "#2ecc71"
                : "#ccc"
            }`,
            borderRadius: "8px",
            boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
          }}>
          {event.action == "PUSH" &&
            `${event.author} pushed to ${event.to_branch}`}
          {event.action == "PULL REQUEST" &&
            `${event.author} submitted a pull request from ${event.from_branch} to ${event.to_branch}`}
          {event.action == "MERGE" &&
            `${event.author} merged branch ${event.from_branch} to ${event.to_branch}`}
          <br />
          <small>
            {new Intl.DateTimeFormat("en-GB", {
              day: "2-digit",
              month: "short",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
              hour12: false,
              timeZone: "UTC",
            }).format(new Date(event.timestamp.$date)) + " UTC"}
          </small>
        </div>
      ))}
    </div>
  );
}

export default App;
