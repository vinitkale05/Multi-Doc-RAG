"use client";

import React from "react";
import Navbar from "../../components/Navbar";
import AdminDashboard from "../../components/AdminDashboard";

export default function AdminPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <main className="flex-1 overflow-y-auto">
        <AdminDashboard />
      </main>
    </div>
  );
}
