import { Outlet, Link, useLocation } from "react-router-dom";
import { AppBar, Toolbar, Typography, Container, Button, Stack } from "@mui/material";

export default function AppShell() {
  const loc = useLocation();
  const tabs = [
    { to: "/", label: "Dashboard" },
    { to: "/users", label: "Users" },
    { to: "/principals", label: "Principals" },
    { to: "/hosts", label: "Hosts" },
    { to: "/sign", label: "Sign" },
  ];
  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>SSH CA</Typography>
          <Stack direction="row" spacing={1}>
            {tabs.map(t => (
              <Button key={t.to} component={Link} to={t.to} variant={loc.pathname===t.to ? "contained":"text"} color="inherit">
                {t.label}
              </Button>
            ))}
          </Stack>
        </Toolbar>
      </AppBar>
      <Container sx={{ py: 3 }}>
        <Outlet />
      </Container>
    </>
  );
}
