import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

const description =
  "クロスワードのJSONプロジェクトを表示し、この端末へ自動保存するWebアプリ。";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host =
    requestHeaders.get("x-forwarded-host") ??
    requestHeaders.get("host") ??
    "localhost";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.includes("localhost") ? "http" : "https");
  const metadataBase = new URL(`${protocol}://${host}`);

  return {
    metadataBase,
    title: "CrossMaker Web",
    description,
    openGraph: {
      title: "CrossMaker Web",
      description,
      type: "website",
      images: [
        {
          url: "/og.png",
          width: 1731,
          height: 909,
          alt: "CrossMaker Web — クロスワードを、どこでも。",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: "CrossMaker Web",
      description,
      images: ["/og.png"],
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
