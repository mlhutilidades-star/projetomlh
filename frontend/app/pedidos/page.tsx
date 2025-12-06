'use client';

import { useEffect, useState } from 'react';
import api from '../../lib/api';

interface Order {
  id: number;
  codigo_externo: string;
  canal?: string;
  status?: string;
  total_bruto?: number;
}

export default function PedidosPage() {
  const [orders, setOrders] = useState<Order[]>([]);

  useEffect(() => {
    api.get('/orders').then((res) => setOrders(res.data)).catch(() => setOrders([]));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Pedidos</h1>
      <div className="bg-white shadow rounded overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-2">Código</th>
              <th className="text-left p-2">Canal</th>
              <th className="text-left p-2">Status</th>
              <th className="text-left p-2">Total</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} className="border-t">
                <td className="p-2">{o.codigo_externo}</td>
                <td className="p-2">{o.canal}</td>
                <td className="p-2">{o.status}</td>
                <td className="p-2">R$ {o.total_bruto?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
