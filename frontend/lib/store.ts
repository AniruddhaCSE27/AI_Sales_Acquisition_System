import { create } from "zustand";

type AppState = {
  role: string;
  setRole: (role: string) => void;
};

export const useAppStore = create<AppState>((set) => ({
  role: "manager",
  setRole: (role) => set({ role }),
}));

