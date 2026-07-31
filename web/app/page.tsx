import type { Metadata } from "next";
import { CrosswordApp } from "./CrosswordApp";

export const metadata: Metadata = {
  title: "CrossMaker Web",
  description:
    "クロスワードのプロジェクトをブラウザで開き、前回の作業を自動復元できるWeb版CrossMaker。",
};

export default function Home() {
  return <CrosswordApp />;
}
