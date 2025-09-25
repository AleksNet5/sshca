import { Dialog, DialogTitle, DialogContent, DialogActions, Button } from "@mui/material";

export default function ConfirmDialog({
  open, title, children, onClose, onConfirm
}: {
  open: boolean; title: string; children?: React.ReactNode;
  onClose: ()=>void; onConfirm: ()=>void;
}) {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent dividers>{children}</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onConfirm} variant="contained" color="error">Delete</Button>
      </DialogActions>
    </Dialog>
  );
}
