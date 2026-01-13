import { useState } from "react";

const TIME_OF_DAY_OPTIONS = [
  { label: "Morning", value: "morning" },
  { label: "Day", value: "day" },
  { label: "Evening", value: "evening" },
  { label: "Night", value: "night" },
];

const MOOD_OPTIONS = ["calm", "chaotic", "overwhelmed"];
const SESSION_KEY = "petcoach_session_id";

export default function App() {
  const [ageWeeks, setAgeWeeks] = useState(12);
  const [timeOfDay, setTimeOfDay] = useState("morning");
  const [lastActivityMinutes, setLastActivityMinutes] = useState(60);
  const [mood, setMood] = useState("calm");
  const [notes, setNotes] = useState("");
  const [sessionId, setSessionId] = useState(() => localStorage.getItem(SESSION_KEY) || "");
  const [response, setResponse] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus("loading");
    setError("");

    const payload = {
      weeks: Number(ageWeeks),
      time_of_day: timeOfDay,
      last_activity_minutes_ago: Number(lastActivityMinutes),
      mood,
      notes: notes.trim(),
    };

    if (sessionId) {
      payload.session_id = sessionId;
    }

    try {
      const res = await fetch("http://localhost:8000/next-action", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error("Unable to fetch a recommendation.");
      }

      const data = await res.json();
      setResponse(data);

      if (data.session_id) {
        localStorage.setItem(SESSION_KEY, data.session_id);
        setSessionId(data.session_id);
      }
    } catch (err) {
      setError(err.message || "Something went wrong.");
      setResponse(null);
    } finally {
      setStatus("idle");
    }
  };

  const handleResetSession = () => {
    localStorage.removeItem(SESSION_KEY);
    setSessionId("");
  };

  return (
    <div className="page">
      <main className="card">
        <header>
          <p className="eyebrow">PetCoach</p>
          <h1>Find your puppy&apos;s next best action.</h1>
          <p className="subhead">
            Share a few quick details and we&apos;ll call your local PetCoach API for
            guidance.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="form">
          <label className="field">
            Puppy age (weeks)
            <input
              type="number"
              min="6"
              max="104"
              value={ageWeeks}
              onChange={(event) => setAgeWeeks(event.target.value)}
              required
            />
          </label>

          <label className="field">
            Time of day
            <select value={timeOfDay} onChange={(event) => setTimeOfDay(event.target.value)}>
              {TIME_OF_DAY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            Last activity (minutes ago)
            <input
              type="number"
              min="0"
              value={lastActivityMinutes}
              onChange={(event) => setLastActivityMinutes(event.target.value)}
              required
            />
          </label>

          <label className="field">
            How are things right now?
            <select value={mood} onChange={(event) => setMood(event.target.value)}>
              {MOOD_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            Notes
            <textarea
              rows="4"
              placeholder="Share anything that feels important right now..."
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
            />
          </label>

          <div className="actions">
            <button type="submit" disabled={status === "loading"}>
              {status === "loading" ? "Checking..." : "Get next action"}
            </button>
            <button className="reset" type="button" onClick={handleResetSession}>
              Reset session
            </button>
          </div>
          <p className="helper">
            Session {sessionId ? "active" : "not set"} — we&apos;ll reuse it on future
            check-ins.
          </p>
        </form>

        {error ? <p className="error">{error}</p> : null}

        {response ? (
          <section className="response">
            <h2>Recommendation</h2>
            {response.scenario ? (
              <span className="badge">{response.scenario}</span>
            ) : null}
            {response.reassurance ? <p className="reassurance">{response.reassurance}</p> : null}
            <dl>
              <div>
                <dt>Action</dt>
                <dd>{response.action}</dd>
              </div>
              <div>
                <dt>Reason</dt>
                <dd>{response.reason}</dd>
              </div>
              <div>
                <dt>What to avoid</dt>
                <dd>{response.what_to_avoid}</dd>
              </div>
              <div>
                <dt>Next check in</dt>
                <dd>{response.next_check_in_minutes} minutes</dd>
              </div>
            </dl>
          </section>
        ) : null}
      </main>
    </div>
  );
}
