'use client';

import { useEffect, useState } from 'react';
import api from '../../../lib/api';

interface PrecificacaoItem {
  sku: string;
  nome: string;
  custo_atual: number;
  preco_atual: number;
  preco_sugerido_20: number;
  preco_sugerido_30: number;
}

export default function PrecificacaoPage() {
  const [data, setData] = useState<PrecificacaoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    api
      .get('/analytics/precificacao-sugerida')
      .then((res) => {
        setData(res.data.itens || []);
        setError('');
      })
      .catch(() => setError('Erro ao carregar precificação sugerida'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Precificação Sugerida</h1>
      
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {loading && <p className="text-slate-500 text-sm">Carregando...</p>}

      {!loading && data.length === 0 && (
        <p className="text-slate-500">Nenhum produto encontrado.</p>
      )}

      {!loading && data.length > 0 && (
        <div className="bg-white shadow-sm rounded overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Custo Atual</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Preço Atual</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Sugerido 20%</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Sugerido 30%</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((item, idx) => {
                const abaixoSugerido = item.preco_atual < item.preco_sugerido_20;
                return (
                  <tr key={idx}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.sku}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.nome}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">R$ {item.custo_atual.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">R$ {item.preco_atual.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">R$ {item.preco_sugerido_20.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">R$ {item.preco_sugerido_30.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                      {abaixoSugerido ? (
                        <span className="px-2 py-1 rounded text-xs font-semibold bg-red-100 text-red-800">
                          ⚠️ Abaixo
                        </span>
                      ) : (
                        <span className="px-2 py-1 rounded text-xs font-semibold bg-green-100 text-green-800">
                          ✓ OK
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
