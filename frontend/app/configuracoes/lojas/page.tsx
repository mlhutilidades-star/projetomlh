'use client';

import { useEffect, useState } from 'react';
import api from '../../../lib/api';

interface Store {
  id: number;
  name: string;
  tipo_canal: string;
  ativo: boolean;
}

export default function LojasPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [form, setForm] = useState({ name: '', tipo_canal: 'shopee' });

  const load = () => {
    api.get('/stores').then((res) => setStores(res.data)).catch(() => setStores([]));
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post('/stores', { ...form, credenciais: {}, ativo: true });
    setForm({ name: '', tipo_canal: 'shopee' });
    load();
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Lojas</h1>
      <div className="bg-white p-4 shadow rounded">
        <h2 className="font-semibold mb-2">Nova loja</h2>
        <form className="grid grid-cols-1 md:grid-cols-3 gap-3" onSubmit={submit}>
          <input className="border rounded px-3 py-2" placeholder="Nome" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <select className="border rounded px-3 py-2" value={form.tipo_canal} onChange={(e) => setForm({ ...form, tipo_canal: e.target.value })}>
            <option value="shopee">Shopee</option>
            <option value="tiny">Tiny</option>
            <option value="outro">Outro</option>
          </select>
          <button type="submit" className="bg-blue-600 text-white rounded px-4">Salvar</button>
        </form>
      </div>
      <div className="bg-white shadow rounded overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-2">Nome</th>
              <th className="text-left p-2">Canal</th>
              <th className="text-left p-2">Ativo</th>
            </tr>
          </thead>
          <tbody>
            {stores.map((s) => (
              <tr key={s.id} className="border-t">
                <td className="p-2">{s.name}</td>
                <td className="p-2">{s.tipo_canal}</td>
                <td className="p-2">{s.ativo ? 'Sim' : 'Não'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
