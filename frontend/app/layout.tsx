import "./globals.css";
import Link from "next/link";
import { ReactNode } from "react";

export const metadata = {
  title: "AP Gestor Seller",
  description: "Painel de gestão para e-commerce",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen">
        <div className="min-h-screen">
          <header className="bg-white shadow-sm">
            <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
              <div className="font-semibold text-lg">AP Gestor Seller</div>
              <nav className="space-x-4 text-sm text-slate-600">
                <Link href="/dashboard">Dashboard</Link>
                <Link href="/analytics/margem">Margens</Link>
                <Link href="/analytics/canais">Canais</Link>
                <Link href="/analytics/curva-abc">Curva ABC</Link>
                <Link href="/analytics/precificacao">Precificação</Link>
                <Link href="/financeiro/contas-pagar">Contas a pagar</Link>
                <Link href="/financeiro/contas-receber">Contas a receber</Link>
                <Link href="/pedidos">Pedidos</Link>
                <Link href="/repasses">Repasses</Link>
                <Link href="/configuracoes/lojas">Lojas</Link>
              </nav>
            </div>
          </header>
          <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
