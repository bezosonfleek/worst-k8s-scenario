import { createContext, useContext, useState, useEffect } from "react";
import { createUser, getUser } from "../api/client";

const UserContext = createContext(null);

const STORAGE_KEY = "pigabid_user_id";

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedId = localStorage.getItem(STORAGE_KEY);
    if (storedId) {
      getUser(storedId)
        .then(setUser)
        .catch(() => localStorage.removeItem(STORAGE_KEY))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function register(displayName) {
    const newUser = await createUser(displayName);
    localStorage.setItem(STORAGE_KEY, newUser.id);
    setUser(newUser);
    return newUser;
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }

  return (
    <UserContext.Provider value={{ user, loading, register, logout }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
