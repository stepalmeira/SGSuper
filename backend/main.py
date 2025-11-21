# -*- coding: utf-8 -*-
from flask import Flask
# Importe todos os seus blueprints
from rotas.produto import produto_bp
from rotas.relatorios import relatorios_bp
# ... importe os outros (funcionario_bp, etc.)

# Inicializa a aplicação Flask
app = Flask(__name__)

# Registra os blueprints na aplicação principal
app.register_blueprint(produto_bp)
app.register_blueprint(relatorios_bp)

# Roda o servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)