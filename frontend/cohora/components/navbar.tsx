"use client";

import Link from "next/link";
import { Menu, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const routes = [
  {
    href: "/",
    label: "Home",
  },
  {
    href: "/chat",
    label: "Chat",
  },
];

export function Navbar() {
  return (
    <header className="absolute top-2 left-1/2 -translate-x-1/2 z-50 max-w-screen-lg w-full border bg-background/95 backdrop-blur mx-auto rounded-full supports-[backdrop-filter]:bg-background/60 p-4 py-2">
      <div className="container flex h-14 items-center justify-between">
        <Link href="/" className="flex-1 items-center space-x-2">
          <img src="/cohora.svg" alt="Cohora" width={120} height={30} />
        </Link>
        <nav className="flex items-center space-x-4">
          {routes.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className="transition-colors text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg px-4 py-2 hover:no-underline"
            >
              {route.label}
            </Link>
          ))}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="default" className="relative h-12 w-12 rounded-full ml-4">
                <span className="sr-only">Open user menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuItem>Profile</DropdownMenuItem>
              <DropdownMenuItem>Settings</DropdownMenuItem>
              <DropdownMenuItem>Log out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </nav>
      </div>
    </header>
  );
}
