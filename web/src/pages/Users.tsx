import { useEffect, useState } from "react";
import { api } from "../api";
import { Card, CardContent, Typography, Stack, Button, TextField, Chip, Dialog, DialogContent, DialogTitle } from "@mui/material";
import ConfirmDialog from "../components/ConfirmDialog";

type User = { id:number; username:string; email:string|null; active:boolean; principals:string[] };

export default function Users(){
  const [rows, setRows] = useState<User[]>([]);
  const [open, setOpen] = useState(false);
  const [del, setDel] = useState<User|undefined>();
  const [form, setForm] = useState({ username:"", email:"", password:"" });

  const load = async ()=>{ const {data}=await api.get<User[]>("/api/v1/users"); setRows(data); };
  useEffect(()=>{ load(); },[]);

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1}>
        <Button variant="contained" onClick={()=>setOpen(true)}>New User</Button>
        <Button onClick={load}>Refresh</Button>
      </Stack>

      {rows.map(r=>(
        <Card key={r.id}><CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <div>
              <Typography variant="h6">{r.username}</Typography>
              <Typography color="text.secondary">{r.email || "—"}</Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap:"wrap" }}>
                {r.principals.map(p=><Chip key={p} label={p} size="small" />)}
              </Stack>
            </div>
            <Stack direction="row" spacing={1}>
              <Button color="error" onClick={()=>setDel(r)}>Delete</Button>
            </Stack>
          </Stack>
        </CardContent></Card>
      ))}

      <Dialog open={open} onClose={()=>setOpen(false)}>
        <DialogTitle>New User</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt:1, width: 360 }}>
            <TextField label="Username" value={form.username} onChange={e=>setForm(f=>({...f, username:e.target.value}))}/>
            <TextField label="Email" value={form.email} onChange={e=>setForm(f=>({...f, email:e.target.value}))}/>
            <TextField label="Password (optional)" type="password" value={form.password} onChange={e=>setForm(f=>({...f, password:e.target.value}))}/>
            <Button variant="contained" onClick={async ()=>{
              await api.post("/api/v1/users", form);
              setOpen(false); setForm({username:"", email:"", password:""}); load();
            }}>Create</Button>
          </Stack>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!del}
        title={`Delete user ${del?.username}?`}
        onClose={()=>setDel(undefined)}
        onConfirm={async ()=>{ await api.delete(`/api/v1/users/${del!.id}`); setDel(undefined); load(); }}
      />
    </Stack>
  )
}
