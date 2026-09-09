import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { UserProvider, useUser } from "./context/UserContext";
import IdentityGate from "./components/IdentityGate";
import ItemListPage from "./pages/ItemListPage";
import ItemDetailPage from "./pages/ItemDetailPage";
import CreateListingPage from "./pages/CreateListingPage";
import AdminQueuePage from "./pages/AdminQueuePage";
import "./styles.css";

function NavBar() {
  const { user, logout } = useUser();
  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        PigaBid
      </Link>
      <div className="nav-links">
        <Link to="/">Auctions</Link>
        <Link to="/sell">Sell an item</Link>
        {user?.is_admin && <Link to="/admin">Admin queue</Link>}
        {user && (
          <span className="nav-user">
            {user.display_name}{" "}
            <button className="link-button" onClick={logout}>
              switch user
            </button>
          </span>
        )}
      </div>
    </nav>
  );
}

function AppRoutes() {
  return (
    <IdentityGate>
      <NavBar />
      <Routes>
        <Route path="/" element={<ItemListPage />} />
        <Route path="/items/:itemId" element={<ItemDetailPage />} />
        <Route path="/sell" element={<CreateListingPage />} />
        <Route path="/admin" element={<AdminQueuePage />} />
      </Routes>
    </IdentityGate>
  );
}

export default function App() {
  return (
    <UserProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </UserProvider>
  );
}
