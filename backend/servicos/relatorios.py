from database.conector import DatabaseManager

class RelatoriosDatabase:

    def __init__(self, db_provider: DatabaseManager | None = None) -> None:
        # Avoid creating a DB connection at import time by lazy-initializing
        self.db = db_provider or DatabaseManager()

    def get_resumo_mensal_por_produto(self, ano: int, mes: int):
        """
        Calcula a soma total de entradas (Lote) e saídas (Venda) para CADA produto em um mês específico.
        """
        query = """
            WITH Movimentacao AS (
                -- ENTRADAS (Lote)
                SELECT 
                    l.cod_produto AS cod_barras,
                    p.nome AS nome_produto,
                    l.quantidade AS entrada,
                    0 AS saida
                FROM 
                    Lote l
                JOIN 
                    Produto p ON l.cod_produto = p.cod_barras
                WHERE 
                    EXTRACT(YEAR FROM data_recebimento) = %s AND EXTRACT(MONTH FROM data_recebimento) = %s
                
                UNION ALL
                
                -- SAÍDAS (Venda)
                SELECT 
                    vcp.cod_barras,
                    p.nome AS nome_produto,
                    0 AS entrada,
                    vcp.quantidade AS saida
                FROM 
                    Venda_Contem_Produto vcp
                JOIN 
                    Venda v ON vcp.cod_venda = v.cod_venda
                JOIN 
                    Produto p ON vcp.cod_barras = p.cod_barras
                WHERE 
                    EXTRACT(YEAR FROM v.data_venda) = %s AND EXTRACT(MONTH FROM v.data_venda) = %s
            )
            -- Agrupa as movimentações por produto e soma
            SELECT
                cod_barras,
                nome_produto,
                SUM(entrada) AS total_entradas,
                SUM(saida) AS total_saidas
            FROM
                Movimentacao
            GROUP BY
                cod_barras, nome_produto
            ORDER BY
                nome_produto ASC;
        """
        # Repetimos os parâmetros (ano, mes) para as duas consultas WHERE
        params = (ano, mes, ano, mes)
        
        # Usamos execute_select_all porque retorna várias linhas (uma por produto)
        return self.db.execute_select_all(query, params)

    def get_relatorio_movimentacao(self, cod_barras=None):
        """
        Gera um relatório unificado de entrada e saída.
        Se cod_barras for None, retorna a movimentação de TODOS os produtos.
        """
        # Se for um relatório geral, não precisamos do UNION ALL, 
        # mas sim de uma cláusula WHERE dinâmica.
        
        # A complexidade de ter um UNION ALL e um LEFT JOIN para nome do produto
        # torna mais simples manter a query com UNION ALL e usar a cláusula WHERE.
        
        # 1. Monta a condição WHERE
        where_clause = "WHERE l.cod_produto = %s" if cod_barras else ""
        where_clause_venda = "WHERE vcp.cod_barras = %s" if cod_barras else ""
        
        # 2. Monta os parâmetros
        params = (cod_barras, cod_barras) if cod_barras else ()

        query = f"""
            -- ENTRADAS (Lote)
            SELECT 
                'ENTRADA' AS tipo_movimento,
                l.data_recebimento AS data_movimento,
                l.quantidade,
                CAST(l.cod_lote AS VARCHAR) AS referencia,
                l.cod_produto,
                p.nome AS nome_produto    -- Adicionado o nome do produto
            FROM 
                Lote l
            JOIN
                Produto p ON l.cod_produto = p.cod_barras
            {where_clause}
            
            UNION ALL
            
            -- SAÍDAS (Venda)
            SELECT 
                'SAÍDA' AS tipo_movimento,
                v.data_venda AS data_movimento,
                (vcp.quantidade * -1) AS quantidade,
                CAST(vcp.cod_venda AS VARCHAR) AS referencia,
                vcp.cod_barras AS cod_produto,
                p.nome AS nome_produto    -- Adicionado o nome do produto
            FROM 
                Venda_Contem_Produto vcp
            JOIN 
                Venda v ON vcp.cod_venda = v.cod_venda
            JOIN
                Produto p ON vcp.cod_barras = p.cod_barras
            {where_clause_venda}
            
            ORDER BY 
                data_movimento DESC;
        """
        # Usamos self.db.execute_select_all para consultas dinâmicas (f-string) e injetamos os parâmetros separadamente
        return self.db.execute_select_all(query, params)