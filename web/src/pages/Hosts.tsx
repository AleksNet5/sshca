import { useEffect, useState } from "react";
import { api } from "../api";
import { Stack, Card, CardContent, Typography, Button, TextField, Chip } from "@mui/material";

type Host = { id:number; hostname:string; principals:string[]; has_token:boolean };

export default function Hosts(){
  const [rows, setRows] = useState<Host[]>([]);
  const [hostname, setHostname] = useState("");
  const load = async ()=>{ const {data}=await api.get<Host[]>("/api/v1/hosts"); setRows(data); };
  useEffect(()=>{ load(); },[]);

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1}>
        <TextField label="Hostname" value={hostname} onChange={e=>setHostname(e.target.value)} />
        <Button variant="contained" onClick={async ()=>{
          if(!hostname.trim()) return;
          await api.post("/api/v1/hosts",{hostname}); setHostname(""); load();
        }}>Add</Button>
        <Button onClick={load}>Refresh</Button>
      </Stack>

      {rows.map(h=>(
        <Card key={h.id}><CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <div>
              <Typography variant="h6">{h.hostname}</Typography>
              <Stack direction="row" spacing={1} sx={{ mt:1, flexWrap:"wrap" }}>
                {h.principals.map(p=><Chip key={p} label={p} size="small" />)}
              </Stack>
            </div>
            <Stack direction="row" spacing={1}>
              <Button onClick={async ()=>{ const {data}=await api.post(`/api/v1/hosts/${h.id}/rotate-token`); alert(`New token:\n${data.api_token}`); load(); }}>Rotate token</Button>
              <Button color="error" onClick={async ()=>{ await api.delete(`/api/v1/hosts/${h.id}`); load(); }}>Delete</Button>
            </Stack>
          </Stack>
        </CardContent></Card>
      ))}
    </Stack>
  );
}
