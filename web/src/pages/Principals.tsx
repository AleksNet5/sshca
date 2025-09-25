import { useEffect, useState } from "react";
import { api } from "../api";
import { Stack, Card, CardContent, Typography, TextField, Button } from "@mui/material";

type Principal = { id:number; name:string };

export default function Principals(){
  const [rows, setRows] = useState<Principal[]>([]);
  const [name, setName] = useState("");
  const load = async ()=>{ const {data}=await api.get<Principal[]>("/api/v1/principals"); setRows(data); };
  useEffect(()=>{ load(); },[]);
  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1}>
        <TextField label="New principal" value={name} onChange={e=>setName(e.target.value)} />
        <Button variant="contained" onClick={async ()=>{ if(!name.trim()) return; await api.post("/api/v1/principals",{name}); setName(""); load(); }}>Add</Button>
      </Stack>
      {rows.map(p=>(
        <Card key={p.id}><CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography>{p.name}</Typography>
            <Button color="error" onClick={async ()=>{ await api.delete(`/api/v1/principals/${p.id}`); load(); }}>Delete</Button>
          </Stack>
        </CardContent></Card>
      ))}
    </Stack>
  );
}
