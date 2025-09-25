import { useEffect, useState } from "react";
import { api } from "../api";
import { Card, CardContent, Typography, List, ListItem, ListItemText } from "@mui/material";

type Issue = {
  id:number; username:string; principals:string[]; key_id:string; serial:number; ttl:string; created_at:string;
};

export default function Dashboard(){
  const [items, setItems] = useState<Issue[]>([]);
  useEffect(()=>{ api.get("/api/v1/cert-issues").then(r=>setItems(r.data)); },[]);
  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>Recent Certificates</Typography>
        <List dense>
          {items.map(i=>(
            <ListItem key={i.id} divider>
              <ListItemText
                primary={`${i.username} · ${i.principals.join(", ")} · serial #${i.serial}`}
                secondary={`${i.key_id} · ${new Date(i.created_at).toLocaleString()} · TTL ${i.ttl}`}
              />
            </ListItem>
          ))}
          {items.length===0 && <Typography color="text.secondary">No issues yet.</Typography>}
        </List>
      </CardContent>
    </Card>
  )
}
