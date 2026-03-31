import type { Metadata } from "next";
import { Noto_Sans_JP } from "next/font/google";
import "./globals.css";

const notoSansJP = Noto_Sans_JP({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "Nihongo Sensei",
  description: "AI Voice-Powered Japanese Language Tutor",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${notoSansJP.className} bg-slate-900 text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}
