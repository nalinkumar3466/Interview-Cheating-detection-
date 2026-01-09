import { Sun, Moon } from "lucide-react";
import { useTheme } from "../context/ThemeContect";

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="p-2 rounded-xl bg-white/10 hover:bg-white/20 transition"
      title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
    >
      {theme === "dark" ? (
        <Sun size={18} className="text-yellow-300" />
      ) : (
        <Moon size={18} className="text-blue-600" />
      )}
    </button>
  );
}
