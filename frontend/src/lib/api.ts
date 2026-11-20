const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
export type DocumentRecord = {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  status: string;
  ocr_status: string;
  extraction_status: string;
  extracted_fields: Record<
    string,
    { value: unknown; confidence: number | null; source: string | null }
  > | null;
  raw_extraction: Record<string, unknown> | null;
  validation: { status: string; issues: string[] } | null;
  ocr_result: {
    text: string;
    words: { text: string; bbox: number[]; confidence: number; page: number }[];
    page_count: number;
    mean_confidence: number;
  } | null;
  processing_time_ms: number | null;
  created_at: string;
  error_message: string | null;
};
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
export const api = {
  health: () =>
    request<{ status: string; database: string; extraction_model: string }>(
      "/health",
    ),
  list: () => request<{ items: DocumentRecord[]; total: number }>("/documents"),
  get: (id: string) => request<DocumentRecord>(`/documents/${id}`),
  fileUrl: (id: string) => `${API}/documents/${id}/file`,
  upload: (file: File) => {
    const data = new FormData();
    data.append("file", file);
    return request<DocumentRecord>("/documents/upload", {
      method: "POST",
      body: data,
    });
  },
  process: (id: string) =>
    request<DocumentRecord>(`/documents/${id}/process`, { method: "POST" }),
  remove: (id: string) =>
    request<void>(`/documents/${id}`, { method: "DELETE" }),
};
