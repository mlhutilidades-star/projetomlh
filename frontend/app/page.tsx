import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Bem-vindo</h1>
      <p>Acesse o painel para continuar.</p>
      <Link href="/login" className="text-blue-600 underline">Ir para login</Link>
    </div>
  );
}
