"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { BookOpen, ShieldCheck, User as UserIcon, LogOut, Sun, Moon } from "lucide-react";
import { User } from "../types";
import { getMeApi, clearToken } from "../lib/api";

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    getMeApi()
      .then(setUser)
      .catch(() => {});

    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setIsDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    setIsDark(!isDark);
    if (!isDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const handleLogout = () => {
    clearToken();
    window.location.href = "/auth/login";
  };

  return (
    <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-4 flex items-center justify-between z-20 sticky top-0">
      <div className="flex items-center space-x-3">
        <Link href="/" className="flex items-center space-x-2 font-bold text-slate-900 dark:text-white">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-sm">
            <BookOpen className="w-4 h-4" />
          </div>
          <span className="text-base tracking-tight hidden sm:inline">Multi-Doc RAG</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 font-mono font-medium border border-sky-200 dark:border-sky-800">
            v1.0
          </span>
        </Link>
      </div>

      <div className="flex items-center space-x-3">
        <Link
          href="/admin"
          className="flex items-center space-x-1.5 text-xs font-medium px-2.5 py-1.5 rounded-md text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
          <span className="hidden sm:inline">Admin & Eval</span>
        </Link>

        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="p-1.5 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
        </button>

        {user ? (
          <div className="flex items-center space-x-2 pl-2 border-l border-slate-200 dark:border-slate-800">
            <div className="flex items-center space-x-1.5 text-xs text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-full">
              <UserIcon className="w-3 h-3 text-sky-500" />
              <span className="max-w-[120px] truncate">{user.email}</span>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <Link
            href="/auth/login"
            className="text-xs font-semibold px-3 py-1.5 rounded-md bg-sky-600 hover:bg-sky-500 text-white transition shadow-sm"
          >
            Sign In
          </Link>
        )}
      </div>
    </header>
  );
}
