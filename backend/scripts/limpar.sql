-- Limpar dados simulados - Deixar banco pronto para dados REAIS
DELETE FROM payout WHERE order_id IN (SELECT id FROM "order" WHERE tenant_id = 4);
DELETE FROM receivable WHERE tenant_id = 4;
DELETE FROM payable WHERE tenant_id = 4;
DELETE FROM "order" WHERE tenant_id = 4;
DELETE FROM product WHERE tenant_id = 4;

SELECT 'Limpeza concluída' as status;
