"""
Script de Database Optimization - Phase 11.
Cria índices e otimiza queries para melhor performance.
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseOptimization:
    """Gerencia otimizações de banco de dados."""
    
    def __init__(self, db_url: str = "sqlite:///./data/mlh_test.db"):
        """
        Inicializa otimizador de database.
        
        Args:
            db_url: URL de conexão do banco de dados.
        """
        # Extrai caminho do arquivo SQLite
        if "sqlite:///" in db_url:
            self.db_path = db_url.replace("sqlite:///", "")
        else:
            self.db_path = db_url
    
    def create_indexes(self):
        """Cria índices recomendados para melhor performance."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indexes = [
            # Índices para tabela payables
            (
                "idx_payables_shop_status",
                "CREATE INDEX IF NOT EXISTS idx_payables_shop_status ON payables(shop_id, status);"
            ),
            (
                "idx_payables_due_date",
                "CREATE INDEX IF NOT EXISTS idx_payables_due_date ON payables(due_date) WHERE status='pending';"
            ),
            (
                "idx_payables_created",
                "CREATE INDEX IF NOT EXISTS idx_payables_created ON payables(created_at DESC);"
            ),
            
            # Índices para tabela orders
            (
                "idx_orders_shop_date",
                "CREATE INDEX IF NOT EXISTS idx_orders_shop_date ON orders(shop_id, order_date DESC);"
            ),
            (
                "idx_orders_status",
                "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);"
            ),
            
            # Índices para tabela products
            (
                "idx_products_category",
                "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);"
            ),
            (
                "idx_products_status",
                "CREATE INDEX IF NOT EXISTS idx_products_status ON products(status) WHERE status='active';"
            ),
            
            # Índices para tabela syncs
            (
                "idx_syncs_api_date",
                "CREATE INDEX IF NOT EXISTS idx_syncs_api_date ON syncs(api, last_sync DESC);"
            ),
        ]
        
        created_count = 0
        for idx_name, query in indexes:
            try:
                cursor.execute(query)
                logger.info(f"✅ Índice criado: {idx_name}")
                created_count += 1
            except sqlite3.Error as e:
                logger.warning(f"⚠️  Erro ao criar índice {idx_name}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Total de índices criados: {created_count}")
        return created_count
    
    def analyze_query_plans(self):
        """Analisa planos de execução de queries frequentes."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        queries = [
            ("Payables por Status", 
             "SELECT status, COUNT(*) as count FROM payables GROUP BY status;"),
            
            ("Receita Total por Shop",
             "SELECT shop_id, SUM(amount) as total FROM orders WHERE status='completed' GROUP BY shop_id;"),
            
            ("Produtos com Estoque Baixo",
             "SELECT product_id, quantity FROM products WHERE quantity < 10 AND status='active';"),
            
            ("Últimos Pedidos",
             "SELECT * FROM orders WHERE shop_id=? ORDER BY order_date DESC LIMIT 100;"),
        ]
        
        print("\n📈 ANÁLISE DE QUERY PLANS:\n")
        for query_name, query in queries:
            print(f"Query: {query_name}")
            print(f"SQL: {query}")
            
            try:
                cursor.execute(f"EXPLAIN QUERY PLAN {query}")
                plan = cursor.fetchall()
                for row in plan:
                    print(f"  {row}")
            except Exception as e:
                print(f"  Erro: {e}")
            
            print()
        
        conn.close()
    
    def get_statistics(self):
        """Retorna estatísticas do banco de dados."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tamanho do arquivo
        db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB
        
        # Contagem de registros por tabela
        tables = [
            "payables", "orders", "products", "order_items", 
            "syncs", "logs", "audit_logs"
        ]
        
        stats = {
            "file_size_mb": round(db_size, 2),
            "tables": {}
        }
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                stats["tables"][table] = count
            except:
                pass
        
        conn.close()
        return stats
    
    def vacuum_database(self):
        """Otimiza espaço do banco de dados removendo fragmentação."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("VACUUM;")
            conn.commit()
            logger.info("✅ Database vacuumed - espaço otimizado")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ Erro ao fazer VACUUM: {e}")
            return False
        finally:
            conn.close()
    
    def analyze_database(self):
        """Executa ANALYZE para atualizar estatísticas."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("ANALYZE;")
            conn.commit()
            logger.info("✅ Database analyzed - estatísticas atualizadas")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ Erro ao fazer ANALYZE: {e}")
            return False
        finally:
            conn.close()


def run_database_optimization():
    """Executa todas as otimizações de database."""
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        DATABASE OPTIMIZATION - PHASE 11                       ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    optimizer = DatabaseOptimization()
    
    # 1. Criar índices
    print("\n1️⃣  Criando índices para melhor performance...")
    optimizer.create_indexes()
    
    # 2. Analisar queries
    print("\n2️⃣  Analisando planos de execução de queries...")
    optimizer.analyze_query_plans()
    
    # 3. Estatísticas
    print("\n3️⃣  Estatísticas do banco de dados:")
    stats = optimizer.get_statistics()
    print(f"   📊 Tamanho: {stats['file_size_mb']} MB")
    print("   📈 Contagem de registros por tabela:")
    for table, count in stats['tables'].items():
        print(f"      - {table}: {count:,} registros")
    
    # 4. VACUUM
    print("\n4️⃣  Otimizando espaço do database...")
    optimizer.vacuum_database()
    
    # 5. ANALYZE
    print("\n5️⃣  Atualizando estatísticas para query optimizer...")
    optimizer.analyze_database()
    
    print("\n✅ Otimizações de database concluídas!")
    print("\n💡 Próximos passos:")
    print("   - Monitorar performance com as métricas (Phase 10)")
    print("   - Executar testes de carga")
    print("   - Considerar particionamento de tabelas grandes")
    print("   - Backup automático configurado")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_database_optimization()
