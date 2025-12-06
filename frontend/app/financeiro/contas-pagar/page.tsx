'use client';

import { useEffect, useState } from 'react';
import api from '../../../lib/api';

interface Payable {
  id: number;
  fornecedor: string;
  categoria?: string;
  vencimento: string;
  valor_previsto: number;
  status: string;
}

export default function ContasPagarPage() {
  const [data, setData] = useState<Payable[]>([]);
  const [form, setForm] = useState({ fornecedor: '', categoria: '', vencimento: '', valor_previsto: 0 });
  const [error, setError] = useState('');

  const load = () => {
    api
      .get('/finance/payables')
      .then((res) => setData(res.data))
      .catch(() => setError('Erro ao carregar. Faça login novamente.'));
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/finance/payables', form);
      setForm({ fornecedor: '', categoria: '', vencimento: '', valor_previsto: 0 });
      load();
    } catch (err) {
      setError('Erro ao criar');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Contas a pagar</h1>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <div className="bg-white shadow p-4 rounded">
        <h2 className="font-semibold mb-2">Nova conta</h2>
        <form className="grid grid-cols-1 md:grid-cols-4 gap-3" onSubmit={submit}>
          <input className="border rounded px-3 py-2" placeholder="Fornecedor" value={form.fornecedor} onChange={(e) => setForm({ ...form, fornecedor: e.target.value })} required />
          <input className="border rounded px-3 py-2" placeholder="Categoria" value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })} />
          <input className="border rounded px-3 py-2" type="date" value={form.vencimento} onChange={(e) => setForm({ ...form, vencimento: e.target.value })} required />
          <input className="border rounded px-3 py-2" type="number" step="0.01" value={form.valor_previsto} onChange={(e) => setForm({ ...form, valor_previsto: parseFloat(e.target.value) })} required />
          <button type="submit" className="md:col-span-4 bg-blue-600 text-white py-2 rounded">Salvar</button>
        </form>
      </div>

      <div className="bg-white shadow rounded overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-2">Fornecedor</th>
              <th className="text-left p-2">Categoria</th>
              <th className="text-left p-2">Vencimento</th>
              <th className="text-left p-2">Valor</th>
              <th className="text-left p-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="p-2">{p.fornecedor}</td>
                <td className="p-2">{p.categoria}</td>
                <td className="p-2">{p.vencimento}</td>
                <td className="p-2">R$ {p.valor_previsto?.toFixed(2)}</td>
                <td className="p-2">{p.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white shadow p-4 rounded">
        <h2 className="font-semibold mb-2">Upload de boleto (mock)</h2>
        <input type="file" className="block" />
        <p className="text-xs text-slate-500 mt-1">Integração já preparada para chamar /finance/upload-boleto.</p>
      </div>
    </div>
  );
}
