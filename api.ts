export type Mode='scene_description'|'read_text'|'identify_object';
export interface Result {success:boolean;mode:Mode;description:string|null;extracted_text:string|null;objects:{label:string;confidence:number}[];warnings:string[]}
const BASE=(import.meta.env.VITE_API_BASE_URL||'http://localhost:8000').replace(/\/$/,'');
export async function analyzeImage(file:File,mode:Mode):Promise<Result>{const body=new FormData();body.append('image',file);body.append('mode',mode);let r:Response;try{r=await fetch(`${BASE}/api/analyze-image`,{method:'POST',body})}catch{throw new Error('Cannot connect to the backend. Check that the Python server is running.')}const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.detail||`Request failed (${r.status}).`);return data as Result}
export async function health(){try{return (await fetch(`${BASE}/health`)).ok}catch{return false}}
