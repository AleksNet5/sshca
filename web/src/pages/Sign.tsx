import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { Stack, Typography, TextField, Chip, Button } from "@mui/material";

export default function Sign(){
  const [username, setUsername] = useState("");
  const [principals, setPrincipals] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [ttl, setTtl] = useState("8h");
  const [keyId, setKeyId] = useState("");
  const [pubKey, setPubKey] = useState("");
  const [result, setResult] = useState<{ certificate:string; key_id:string }|null>(null);

  useEffect(()=>{
    if(!username){ setPrincipals([]); setSelected([]); return; }
    const t = setTimeout(async ()=>{
      const {data} = await api.get("/api/v1/user-principals",{ params:{ username } });
      setPrincipals(data.principals || []);
      setSelected([]);
    }, 250);
    return ()=>clearTimeout(t);
  },[username]);

  const canSubmit = useMemo(()=> username && pubKey && selected.length>0, [username, pubKey, selected]);

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Sign SSH Public Key</Typography>
      <TextField label="Username" value={username} onChange={e=>setUsername(e.target.value)} />
      <Stack direction="row" spacing={1} sx={{ flexWrap:"wrap" }}>
        {principals.map(p=>(
          <Chip key={p} label={p}
            variant={selected.includes(p) ? "filled":"outlined"}
            onClick={()=>setSelected(s => s.includes(p) ? s.filter(x=>x!==p):[...s,p])}
          />
        ))}
      </Stack>
      <TextField label="TTL" value={ttl} onChange={e=>setTtl(e.target.value)} />
      <TextField label="Key ID (optional)" value={keyId} onChange={e=>setKeyId(e.target.value)} />
      <TextField label="SSH Public Key" value={pubKey} onChange={e=>setPubKey(e.target.value)} multiline minRows={4} />
      <Button disabled={!canSubmit} variant="contained" onClick={async ()=>{
        const payload = {
          username,
          public_key: pubKey.trim(),
          principals: selected,
          ttl,
          key_id: keyId || `${username}-${Math.floor(Date.now()/1000)}`
        };
        const {data} = await api.post("/api/v1/sign", payload);
        setResult(data);
      }}>Sign</Button>
      {result && (
        <TextField
          label={`Signed certificate (key_id=${result.key_id})`}
          value={result.certificate}
          multiline minRows={3}
        />
      )}
    </Stack>
  );
}
