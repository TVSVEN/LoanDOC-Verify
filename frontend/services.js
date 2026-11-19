export async function api(path,options={}){
  const response=await fetch(`/api${path}`,options);
  const type=response.headers.get('content-type')||'';
  const payload=type.includes('json')?await response.json():await response.text();
  if(!response.ok)throw new Error(payload?.error||payload||`Request failed (${response.status})`);
  return payload;
}
export function uploadFiles(path,files,onProgress=()=>{}){
  return new Promise((resolve,reject)=>{
    const data=new FormData();[...files].forEach(file=>data.append('files',file));
    const request=new XMLHttpRequest();request.open('POST',`/api${path}`);
    request.upload.onprogress=e=>{if(e.lengthComputable)onProgress(Math.round(e.loaded/e.total*100))};
    request.onload=()=>{let result;try{result=JSON.parse(request.responseText)}catch{result={error:request.responseText}}
      if(request.status>=200&&request.status<300)resolve(result);else reject(new Error(result.error||`Upload failed (${request.status})`));};
    request.onerror=()=>reject(new Error('Network error during upload. Your files are still available to retry.'));
    request.onabort=()=>reject(new Error('Upload cancelled.'));request.send(data);
  });
}
