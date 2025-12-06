'use client';

import { useEffect, useState } from 'react';
import api from '../../../lib/api';

interface MargemCanal {
  canal: string;
  receita_liquida: number;
  custo_total: number;
  margem_valor: number;
  margem_percentual: number;
}

export default function CanaisPage() {
  const [data, setData] = useState<MargemCanal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dataIni, setDataIni] = useState('');
  const [dataFim, setDataFim] = useState('');

  const fetchData = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (dataIni) params.append('data_ini', dataIni);
    if (dataFim) params.append('data_fim', dataFim);
    
    api
      .get(`/analytics/margem-por-canal?${params.toString()}`)
      .then((res) => {
        setData(res.data.itens || []);
        setError('');
      })
      .catch(() => setError('Erro ao carregar margem por canal'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Margem por Canal</h1>
      
      <div className="bg-white shadow-sm p-4 rounded space-y-4">
        <div className="flex gap-4">
          <div>
            <label className="block text-sm mb-1">Data Inicial</label>
            <input
              type="date"
              value={dataIni}
              onChange={(e) => setDataIni(e.target.value)}
              className="border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Data Final</label>
            <input
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="border rounded px-3 py-2"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={fetchData}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Filtrar
            </button>
          </div>
        </div>
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}
      {loading && <p className="text-slate-500 text-sm">Carregando...</p>}

      {!loading && data.length === 0 && (
        <p className="text-slate-500">Nenhum canal encontrado no período selecionado.</p>
      )}

      {!loading && data.length > 0 && (
        <div className="bg-white shadow-sm rounded overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Canal</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Receita Líquida</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Custo Total</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Margem (R$)</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Margem (%)</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((item, idx) => (
                <tr key={idx}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{item.canal}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">R$ {item.receita_liquida.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">R$ {item.custo_total.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">R$ {item.margem_valor.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">{item.margem_percentual.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
