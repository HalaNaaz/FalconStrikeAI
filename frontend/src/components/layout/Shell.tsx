"use client";

import React from "react";
import { Sidebar } from "./Sidebar";
import { TopNavbar } from "./TopNavbar";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-text-primary">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNavbar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}

