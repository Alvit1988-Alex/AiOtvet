import { useEffect, useState } from 'react';

interface Dialog {
  id: number;
  status: string;
  last_message_at: string;
}

export default function Home() {
  const [dialogs, setDialogs] = useState<Dialog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/dialogs', { headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` } })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load dialogs');
        return res.json();
      })
      .then(setDialogs)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <main>
      <h1>Dialog feed</h1>
      <ul>
        {dialogs.map((dialog) => (
          <li key={dialog.id}>
            #{dialog.id} — {dialog.status} — {new Date(dialog.last_message_at).toLocaleString()}
          </li>
        ))}
      </ul>
    </main>
  );
}
