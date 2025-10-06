async function loadDialogs() {
  const response = await fetch('/api/dialogs?status=waiting_operator', {
    headers: { Authorization: `Bearer ${window.localStorage.getItem('token') || ''}` },
  });
  if (!response.ok) {
    document.getElementById('app').innerText = 'Failed to load dialogs';
    return;
  }
  const dialogs = await response.json();
  document.getElementById('app').innerText = `Dialogs in queue: ${dialogs.length}`;
}

loadDialogs();
