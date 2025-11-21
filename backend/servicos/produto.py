from database.conector import DatabaseManager

class ProdutoDatabase:

    def __init__(self, db_provider: DatabaseManager | None = None) -> None:
        # Avoid creating a DB connection at import time by lazy-initializing
        self.db = db_provider or DatabaseManager()

    def get_produto_by_cod_barras(self, cod_barras):

        query = "SELECT nome, preco_venda, tipo_produto, estoque_minimo FROM produto WHERE cod_barras = %s;"
        result = self.db.execute_select_one(query, (cod_barras,))
        return result
    
    def get_produtos_proxima_validade(self, dias=30):
        """
        Lista produtos que vencerão nos próximos 'dias'.
        Retorna: lista de dicionários.
        """
        query = """
            SELECT 
                p.nome AS produto_nome, 
                l.cod_lote, 
                l.data_validade
            FROM 
                Lote l
            JOIN 
                Produto p ON l.cod_produto = p.cod_barras
            WHERE 
                l.data_validade BETWEEN current_date AND current_date + interval '%s days'
            ORDER BY 
                l.data_validade ASC;
        """
        # Passamos a variável 'dias' como tupla de parâmetros
        return self.db.execute_select_all(query, (dias,))
    
    def get_produtos_em_falta(self):
        """
        Calcula o estoque atual (Entradas - Saídas) e lista produtos 
        cujo estoque atual é menor que o estoque_minimo.
        """
        query = """
            SELECT
                p.nome, 
                p.cod_barras,
                p.estoque_minimo,
                -- COALESCE garante que, se não houver registros (entrada ou saída), o valor seja 0
                (COALESCE(SUM(l.quantidade), 0) - COALESCE(SUM(vcp.quantidade), 0)) AS estoque_atual
            FROM 
                Produto p
            LEFT JOIN 
                Lote l ON p.cod_barras = l.cod_produto        -- Entradas
            LEFT JOIN 
                Venda_Contem_Produto vcp ON p.cod_barras = vcp.cod_barras -- Saídas
            GROUP BY 
                p.cod_barras, p.nome, p.estoque_minimo
            HAVING 
                (COALESCE(SUM(l.quantidade), 0) - COALESCE(SUM(vcp.quantidade), 0)) < p.estoque_minimo
            ORDER BY 
                estoque_atual ASC;
        """
        # Esta consulta não tem parâmetros dinâmicos, então passamos uma tupla vazia.
        return self.db.execute_select_all(query, ())