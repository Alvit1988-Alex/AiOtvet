export class ApiClient {
  constructor(private readonly token: string | null) {}

  async listDialogs() {
    const response = await fetch('/api/dialogs', {
      headers: { Authorization: `Bearer ${this.token || ''}` },
    });
    if (!response.ok) {
      throw new Error('Failed to fetch dialogs');
    }
    return response.json();
  }
}
