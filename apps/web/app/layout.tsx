import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NovelOS · 小说大王",
  description: "面向个人作者的 AI 长篇小说创作工作台",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
