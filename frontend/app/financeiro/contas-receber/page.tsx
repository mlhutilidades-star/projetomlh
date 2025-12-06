'use client';

import { useEffect, useState } from 'react';
import api from '../../../lib/api';

interface Receivable {
  id: number;
  referencia: string;
  previsao?: string;
  valor_previsto: number;
  status: string;
}

export default function ContasReceberPage() {
  const [data, setData] = useState<Receivable[]>([]);
  const [form, setForm] = useState({ referencia: '', previsao: '', valor_previsto: 0 });

  const load = () => {
    api.get('/finance/receivables').then((res) => setData(res.data)).catch(() => setData([]));
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post('/finance/receivables', { ...form, origem: 'manual', status: 'pendente' });
    setForm({ referencia: '', previsao: '', valor_previsto: 0 });
    load();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Contas a receber</h1>
      <div className="bg-white p-4 shadow rounded">
        <h2 className="font-semibold mb-2">Novo título</h2>
        <form className="grid grid-cols-1 md:grid-cols-4 gap-3" onSubmit={submit}>
          <input className="border rounded px-3 py-2" placeholder="Referência" value={form.referencia} onChange={(e) => setForm({ ...form, referencia: e.target.value })} required />
          <input className="border rounded px-3 py-2" type="date" value={form.previsao} onChange={(e) => setForm({ ...form, previsao: e.target.value })} />
          <input className="border rounded px-3 py-2" type="number" step="0.01" value={form.valor_previsto} onChange={(e) => setForm({ ...form, valor_previsto: parseFloat(e.target.value) })} required />
          <button type="submit" className="bg-blue-600 text-white rounded px-4">Salvar</button>
        </form>
      </div>

      <div className="bg-white shadow rounded overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-2">Referência</th>
              <th className="text-left p-2">Previsão</th>
              <th className="text-left p-2">Valor</th>
              <th className="text-left p-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="p-2">{r.referencia}</td>
                <td className="p-2">{r.previsao}</td>
                <td className="p-2">R$ {r.valor_previsto?.toFixed(2)}</td>
                <td className="p-2">{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
