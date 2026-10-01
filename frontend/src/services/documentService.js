/**
 * Document (receipt/bill) upload API calls, isolated from components.
 */
import api from "./api";

export async function uploadDocument(file, onUploadProgress) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
  return data;
}

export async function fetchDocuments() {
  const { data } = await api.get("/documents");
  return data;
}

export async function fetchDocument(id) {
  const { data } = await api.get(`/documents/${id}`);
  return data;
}

export async function deleteDocument(id) {
  await api.delete(`/documents/${id}`);
}
