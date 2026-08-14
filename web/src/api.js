import axios from "axios";

const client = axios.create({ baseURL: "/api" });

export async function createJob(file) {
  const body = new FormData();
  body.append("file", file);
  const { data } = await client.post("/jobs", body);
  return data;
}

export async function readJob(id) {
  const { data } = await client.get(`/jobs/${id}`);
  return data;
}

export async function readMapping(id) {
  const { data } = await client.get(`/jobs/${id}/mapping`);
  return data;
}

export async function downloadDocx(id, name) {
  const { data } = await client.get(`/jobs/${id}/download`, { responseType: "blob" });
  const url = URL.createObjectURL(data);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

export function errorMessage(error) {
  return error?.response?.data?.error || error?.message || "Something went wrong";
}
