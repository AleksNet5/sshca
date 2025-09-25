import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { theme } from "./theme";
import AppShell from "./shell/AppShell";
import Dashboard from "./pages/Dashboard";
import Users from "./pages/Users";
import Principals from "./pages/Principals";
import Hosts from "./pages/Hosts";
import Sign from "./pages/Sign";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "users", element: <Users /> },
      { path: "principals", element: <Principals /> },
      { path: "hosts", element: <Hosts /> },
      { path: "sign", element: <Sign /> }
    ]
  }
]);

createRoot(document.getElementById("root")!).render(
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <RouterProvider router={router} />
  </ThemeProvider>
);
