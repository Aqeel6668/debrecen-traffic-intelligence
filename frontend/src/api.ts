const API=import.meta.env.VITE_API_URL||'http://localhost:8000';
async function req<T>(path:string):Promise<T>{const r=await fetch(API+path);if(!r.ok)throw new Error(`API request failed (${r.status})`);return r.json()}
export const getSummary=()=>req<any>('/api/summary');export const getSeries=()=>req<any[]>('/api/timeseries?days=7');export const getSensors=()=>req<any[]>('/api/sensors');export const getPredictions=()=>req<any[]>('/api/predictions?horizon=24');export const getAnomalies=()=>req<any[]>('/api/anomalies');
export async function refreshData(){const r=await fetch(API+'/api/refresh',{method:'POST'});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Refresh failed');return d}
