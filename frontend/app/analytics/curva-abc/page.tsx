'use client';

import { useEffect, useState } from 'react';
import api from '../../../lib/api';

interface CurvaABCItem {
  sku: string;
  nome: string;
  receita: number;
  percentual_acumulado: number;
  classe: string;
}

export default function CurvaABCPage() {
  const [data, setData] = useState<CurvaABCItem[]>([]);
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
      .get(`/analytics/curva-abc?${params.toString()}`)
      .then((res) => {
        setData(res.data.itens || []);
        setError('');
      })
      .catch(() => setError('Erro ao carregar curva ABC'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getClasseColor = (classe: string) => {
    if (classe === 'A') return 'bg-green-100 text-green-800';
    if (classe === 'B') return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Curva ABC de Produtos</h1>
      
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
        <p className="text-slate-500">Nenhum produto encontrado no período selecionado.</p>
      )}

      {!loading && data.length > 0 && (
        <div className="bg-white shadow-sm rounded overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Receita</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">% Acumulado</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Classe</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((item, idx) => (
                <tr key={idx} className={item.classe === 'A' ? 'bg-green-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{item.sku}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{item.nome}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">R$ {item.receita.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">{item.percentual_acumulado.toFixed(2)}%</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getClasseColor(item.classe)}`}>
                      {item.classe}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
