import { useMemo, useState } from "react";

const TIME_OF_DAY_OPTIONS = [
  { label: "Morning", value: "morning", time: "08:30" },
  { label: "Day", value: "day", time: "13:00" },
  { label: "Evening", value: "evening", time: "18:30" },
  { label: "Night", value: "night", time: "23:00" },
];

const stageFromAge = (weeks) => {
  if (weeks <= 12) return "Early puppy";
  if (weeks <= 24) return "Growing puppy";
  if (weeks <= 52) return "Adolescent";
  return "Adult";
};

export default function App() {
  const [ageWeeks, setAgeWeeks] = useState(12);
  const [timeOfDay, setTimeOfDay] = useState("morning");
  const [lastActivityMinutes, setLastActivityMinutes] = useState(60);
  const [response, setResponse] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const localTime = useMemo(() => {
    const match = TIME_OF_DAY_OPTIONS.find((option) => option.value === timeOfDay);
    return match ? match.time : "12:00";
  }, [timeOfDay]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus("loading");
    setError("");

    const hoursSinceLastActivity = Number(lastActivityMinutes) / 60;

    try {
      const res = await fetch("http://localhost:8000/next-action", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          puppy_age_weeks: Number(ageWeeks),
          hours_since_last_potty: hoursSinceLastActivity,
          hours_since_last_meal: hoursSinceLastActivity,
          local_time: localTime,
        }),
      });

      if (!res.ok) {
        throw new Error("Unable to fetch a recommendation.");
      }

      const data = await res.json();
      setResponse({
        ...data,
        stage: data.stage ?? stageFromAge(Number(ageWeeks)),
      });
    } catch (err) {
      setError(err.message || "Something went wrong.");
      setResponse(null);
    } finally {
      setStatus("idle");
    }
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

          <button type="submit" disabled={status === "loading"}>
            {status === "loading" ? "Checking..." : "Get next action"}
          </button>
          <p className="helper">
            We&apos;ll reuse this timing for potty and meal history to keep the demo
            simple.
          </p>
        </form>

        {error ? <p className="error">{error}</p> : null}

        {response ? (
          <section className="response">
            <h2>Recommendation</h2>
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
                <dt>Next check in</dt>
                <dd>{response.next_check_in_minutes} minutes</dd>
              </div>
              <div>
                <dt>Stage</dt>
                <dd>{response.stage}</dd>
              </div>
            </dl>
          </section>
        ) : null}
      </main>
    </div>
  );
}
