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
import { SignInButton } from "@clerk/nextjs";
import { SignedOut } from "@clerk/nextjs";
import { UserButton } from "@clerk/nextjs";
import { SignedIn } from "@clerk/nextjs";
import { SignUpButton } from "@clerk/nextjs";

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
    <header className="max-w-screen-lg w-full border bg-background/95 backdrop-blur mx-auto rounded-full supports-[backdrop-filter]:bg-background/60 p-4 py-2 mt-2">
      <div className="container flex h-14 items-center justify-between">
        <Link href="/" className="flex-1 items-center space-x-2">
          <img src="/cohora.svg" alt="Cohora" width={120} height={30} />
        </Link>
        <nav className="flex items-center space-x-4 mx-2">
          {routes.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className="transition-colors text-muted-foreground hover:text-foreground hover:bg-primary/30 rounded-lg px-4 py-2 hover:no-underline"
            >
              {route.label}
            </Link>
          ))}
          <SignedOut>
            <SignInButton mode="modal">
              <Button
                variant="ghost"
                className="text-md font-normal text-muted-foreground hover:text-foreground hover:bg-primary/30 px-4 py-2 hover:no-underline cursor-pointer"
              >
                Sign in
              </Button>
            </SignInButton>
            <SignUpButton mode="modal">
              <Button
                variant="default"
                className="rounded-full px-4 py-2 h-10 text-md hover:no-underline"
              >
                Sign up
              </Button>
            </SignUpButton>
          </SignedOut>
          <SignedIn>
            <UserButton
              appearance={{
                elements: {
                  avatarBox: "w-16 h-16",
                  avatarImage: "w-16 h-16 mr-2",
                },
              }}
              afterSignOutUrl="/"
            />
          </SignedIn>
        </nav>
      </div>
    </header>
  );
}
