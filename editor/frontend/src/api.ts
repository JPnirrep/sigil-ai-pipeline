/* KLEIA-UP Book Editor — API Client */

const BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Accept': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`[${res.status}] ${text.slice(0, 200)}`);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    return res.json() as Promise<T>;
  }
  return res.text() as unknown as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  templates: () => request<{ templates: Array<{ name: string; filename: string; size_str: string }> }>('/templates'),

  importDocx: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/import`, { method: 'POST', body: form });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`[${res.status}] ${text.slice(0, 200)}`);
    }
    return res.json();
  },

  getBook: () => request<any>('/book'),

  updateChapter: (id: string, title: string, content_html: string) =>
    request<any>(`/book/chapter/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title, content_html }),
      headers: { 'Content-Type': 'application/json' },
    }),

  addChapter: (title: string, afterId?: string) =>
    request<any>('/book/chapter', {
      method: 'POST',
      body: JSON.stringify({ title, after_id: afterId }),
      headers: { 'Content-Type': 'application/json' },
    }),

  deleteChapter: (id: string) =>
    request<any>(`/book/chapter/${id}`, { method: 'DELETE' }),

  reorderChapters: (chapterIds: string[]) =>
    request<any>('/book/reorder', {
      method: 'PUT',
      body: JSON.stringify({ chapter_ids: chapterIds }),
      headers: { 'Content-Type': 'application/json' },
    }),

  updateStyle: (style: any) =>
    request<any>('/style', {
      method: 'POST',
      body: JSON.stringify(style),
      headers: { 'Content-Type': 'application/json' },
    }),

  getPreviewUrl: () => `${BASE}/preview`,

  exportEpub: () => {
    window.open(`${BASE}/export/epub`, '_blank');
  },

  exportPdf: () => {
    window.open(`${BASE}/export/pdf`, '_blank');
  },

  uploadImage: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/image/upload`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Upload failed');
    return res.json() as Promise<{ url: string; filename: string }>;
  },

  listSessions: () => request<{ sessions: any[] }>('/sessions'),
  loadSession: (id: string) => request<any>(`/session/load`, {
    method: 'POST',
    body: JSON.stringify({ session_id: id }),
    headers: { 'Content-Type': 'application/json' },
  }),

  saveMeta: (title: string, subtitle: string, author: string) =>
    request<{ status: string }>('/book/meta', {
      method: 'POST',
      body: JSON.stringify({ title, subtitle, author }),
      headers: { 'Content-Type': 'application/json' },
    }),

  getCover: () => request<{ url: string | null }>('/book/cover'),

  uploadCover: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/book/cover`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Cover upload failed');
    return res.json() as Promise<{ url: string; filename: string }>;
  },

  listAliases: () => request<{ aliases: string[] }>('/aliases'),

  createAlias: (name: string) =>
    request<{ status: string; aliases: string[] }>('/aliases', {
      method: 'POST',
      body: JSON.stringify({ name }),
      headers: { 'Content-Type': 'application/json' },
    }),
};
