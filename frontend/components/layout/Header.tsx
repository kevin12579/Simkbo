"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "오늘의 경기" },
  { href: "/stats", label: "통계" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header style={{
      borderBottom: "1px solid #dce4f0",
      background: "#ffffff",
      position: "sticky",
      top: 0,
      zIndex: 50,
    }}>
      <div style={{
        maxWidth: 1280,
        margin: "0 auto",
        padding: "0 32px",
        height: 64,
        display: "flex",
        alignItems: "center",
        gap: 40,
      }}>
        <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 26, height: 26, borderRadius: 6,
            background: "#c8102e", display: "grid", placeItems: "center",
            color: "#fff", fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 13,
          }}>S</div>
          <span style={{
            fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 18,
            letterSpacing: "-0.01em", color: "#0a0a0a",
          }}>simkbo</span>
        </Link>

        <nav style={{ display: "flex", gap: 4, flex: 1 }}>
          {NAV_ITEMS.map(({ href, label }) => {
            const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link key={href} href={href} style={{
                textDecoration: "none",
                background: "transparent",
                padding: "8px 14px",
                fontSize: 14,
                fontFamily: "var(--font-sans)",
                fontWeight: 500,
                color: isActive ? "#0a0a0a" : "#4a5872",
                borderBottom: isActive ? "2px solid #c8102e" : "2px solid transparent",
                marginBottom: -1,
                display: "inline-block",
                transition: "color 0.15s",
              }}>{label}</Link>
            );
          })}
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#4a5872", fontFamily: "var(--font-mono)" }}>
          <span style={{ width: 6, height: 6, borderRadius: 3, background: "#1a7a3a", display: "inline-block" }} />
          모델 v1.0
        </div>
      </div>
    </header>
  );
}
