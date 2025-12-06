'use client';

import { useEffect, useState } from 'react';
import api from '../../lib/api';

interface Payout {
  id: number;
  referencia_periodo: string;
  liquido?: number;
  valor_bruto?: number;
}

export default function RepassesPage() {
  const [payouts, setPayouts] = useState<Payout[]>([]);

  useEffect(() => {
    api.get('/payouts').then((res) => setPayouts(res.data)).catch(() => setPayouts([]));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Repasses</h1>
      <div className="bg-white shadow rounded overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-2">Período</th>
              <th className="text-left p-2">Bruto</th>
              <th className="text-left p-2">Líquido</th>
            </tr>
          </thead>
          <tbody>
            {payouts.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="p-2">{p.referencia_periodo}</td>
                <td className="p-2">R$ {p.valor_bruto?.toFixed(2)}</td>
                <td className="p-2">R$ {p.liquido?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
