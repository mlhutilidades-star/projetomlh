'use client';

import { useEffect, useState } from 'react';
import api from '../../lib/api';

interface Resumo {
  faturamento_30d: number;
  lucro_estimado_30d: number;
  contas_pagar_abertas: number;
  contas_receber_abertas: number;
  saldo_repasses_30d: number;
  ticket_medio_30d: number;
}

export default function DashboardPage() {
  const [data, setData] = useState<Resumo | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get('/analytics/resumo-financeiro')
      .then((res) => {
        setData(res.data);
        setError('');
      })
      .catch(() => setError('Erro ao carregar resumo. Faça login novamente.'))
      .finally(() => setLoading(false));
  }, []);

  const cards = [
    { label: 'Faturamento 30d', value: data?.faturamento_30d ?? 0 },
    { label: 'Lucro estimado 30d', value: data?.lucro_estimado_30d ?? 0 },
    { label: 'Contas a pagar abertas', value: data?.contas_pagar_abertas ?? 0 },
    { label: 'Contas a receber abertas', value: data?.contas_receber_abertas ?? 0 },
    { label: 'Saldo de repasses 30d', value: data?.saldo_repasses_30d ?? 0 },
    { label: 'Ticket médio 30d', value: data?.ticket_medio_30d ?? 0 },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {loading && <p className="text-slate-500 text-sm">Carregando...</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((c) => (
          <div key={c.label} className="bg-white shadow-sm p-4 rounded">
            <div className="text-sm text-slate-500">{c.label}</div>
            <div className="text-2xl font-semibold">R$ {c.value.toFixed(2)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
