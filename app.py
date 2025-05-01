from decimal import Decimal
import json
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_mysql_connector import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
import functools


app = Flask(__name__, static_url_path='/static')
app.secret_key = 'sua_chave_secreta_aqui'


# Configurações do MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DATABASE'] = 'mercadinho'
app.config['MYSQL_AUTOCOMMIT'] = True

mysql = MySQL(app)

# Decorator para rotas que requerem login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'adm' and password == 'adm':
            session['logged_in'] = True
            session['username'] = 'adm'
            return redirect(url_for('home'))
        else:
            flash('Usuário ou senha incorretos', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi deslogado com sucesso', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) as total FROM produtos WHERE ativo = TRUE')
    total_produtos = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as total FROM produtos WHERE quantidade < quantidade_minima AND ativo = TRUE')
    estoque_baixo = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as total FROM fiado WHERE status = "pendente"')
    fiados_pendentes = cursor.fetchone()['total']
    cursor.close()
    
    return render_template('home.html', 
                         total_produtos=total_produtos,
                         estoque_baixo=estoque_baixo,
                         fiados_pendentes=fiados_pendentes,
                         now=datetime.now())

@app.route('/produtos')
@login_required
def produtos():  # Mudei de 'listar_produtos' de volta para 'produtos'
    busca = request.args.get('busca', '')
    categoria = request.args.get('categoria', '')
    
    query = 'SELECT * FROM produtos WHERE ativo = TRUE'
    params = []
    
    if busca:
        query += ' AND nome LIKE %s'
        params.append(f'%{busca}%')
    
    if categoria:
        query += ' AND categoria = %s'
        params.append(categoria)
    
    query += ' ORDER BY nome'
    
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute(query, params)
    produtos = cursor.fetchall()
    cursor.execute('SELECT DISTINCT categoria FROM produtos WHERE ativo = TRUE ORDER BY categoria')
    categorias = [cat['categoria'] for cat in cursor.fetchall()]
    cursor.close()
    
    return render_template('produtos/lista.html', 
                         produtos=produtos,
                         categorias=categorias,
                         busca=busca,
                         categoria_selecionada=categoria,
                         now=datetime.now())
@app.route('/produtos/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'POST':
        try:
            dados = {
                'nome': request.form['nome'],
                'descricao': request.form.get('descricao', ''),
                'preco': float(request.form['preco']),
                'preco_custo': float(request.form.get('preco_custo', 0)),
                'quantidade': int(request.form['quantidade']),
                'quantidade_minima': int(request.form.get('quantidade_minima', 5)),
                'categoria': request.form.get('categoria', 'Outros'),
                'codigo_barras': request.form.get('codigo_barras', None)
            }
            
            cursor = mysql.connection.cursor()
            cursor.execute('''
                INSERT INTO produtos 
                (nome, descricao, preco, preco_custo, quantidade, quantidade_minima, categoria, codigo_barras)
                VALUES (%(nome)s, %(descricao)s, %(preco)s, %(preco_custo)s, %(quantidade)s, %(quantidade_minima)s, %(categoria)s, %(codigo_barras)s)
            ''', dados)
            mysql.connection.commit()
            
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_produtos'))
            
        except Exception as e:
            flash(f'Erro ao cadastrar produto: {str(e)}', 'danger')
    
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute('SELECT DISTINCT categoria FROM produtos ORDER BY categoria')
    categorias = [cat['categoria'] for cat in cursor.fetchall()]
    cursor.close()
    
    return render_template('produtos/formulario.html', 
                         categorias=categorias,
                         produto=None,
                         now=datetime.now())

@app.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM produtos WHERE id = %s', (id,))
    produto = cursor.fetchone()
    
    if request.method == 'POST':
        try:
            dados = {
                'id': id,
                'nome': request.form['nome'],
                'descricao': request.form.get('descricao', ''),
                'preco': float(request.form['preco']),
                'preco_custo': float(request.form.get('preco_custo', 0)),
                'quantidade': int(request.form['quantidade']),
                'quantidade_minima': int(request.form.get('quantidade_minima', 5)),
                'categoria': request.form.get('categoria', 'Outros'),
                'codigo_barras': request.form.get('codigo_barras', None)
            }
            
            cursor.execute('''
                UPDATE produtos SET
                nome = %(nome)s,
                descricao = %(descricao)s,
                preco = %(preco)s,
                preco_custo = %(preco_custo)s,
                quantidade = %(quantidade)s,
                quantidade_minima = %(quantidade_minima)s,
                categoria = %(categoria)s,
                codigo_barras = %(codigo_barras)s
                WHERE id = %(id)s
            ''', dados)
            mysql.connection.commit()
            
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('listar_produtos'))
            
        except Exception as e:
            flash(f'Erro ao atualizar produto: {str(e)}', 'danger')
    
    cursor.execute('SELECT DISTINCT categoria FROM produtos ORDER BY categoria')
    categorias = [cat['categoria'] for cat in cursor.fetchall()]
    cursor.close()
    
    if not produto:
        flash('Produto não encontrado', 'danger')
        return redirect(url_for('listar_produtos'))
    
    return render_template('produtos/formulario.html', 
                         categorias=categorias,
                         produto=produto,
                         now=datetime.now())

@app.route('/produtos/excluir/<int:id>')
@login_required
def excluir_produto(id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('UPDATE produtos SET ativo = FALSE WHERE id = %s', (id,))
        mysql.connection.commit()
        flash('Produto excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir produto: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('listar_produtos'))

@app.route('/clientes')
@login_required
def listar_clientes():
    busca = request.args.get('busca', '')
    
    query = 'SELECT * FROM clientes WHERE ativo = TRUE'
    params = []
    
    if busca:
        query += ' AND nome_completo LIKE %s'
        params.append(f'%{busca}%')
    
    query += ' ORDER BY nome_completo'
    
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute(query, params)
    clientes = cursor.fetchall()
    cursor.close()
    
    return render_template('clientes/lista.html', 
                         clientes=clientes,
                         busca=busca,
                         now=datetime.now())

@app.route('/clientes/novo', methods=['GET', 'POST'])
@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def gerenciar_cliente(id=None):
    if request.method == 'POST':
        nome_completo = request.form['nome_completo']
        telefone = request.form['telefone']
        cpf = request.form.get('cpf', '')
        
        # Validações
        erros = []
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        if len(telefone_limpo) < 10:
            erros.append('Telefone deve ter pelo menos 10 dígitos')
        
        if cpf:
            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            if len(cpf_limpo) != 11:
                erros.append('CPF deve ter 11 dígitos')
            else:
                cpf = cpf_limpo
        
        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('clientes/formulario.html',
                                 cliente={'nome_completo': nome_completo,
                                         'telefone': telefone,
                                         'cpf': cpf} if not id else None,
                                 now=datetime.now())
        
        cursor = mysql.connection.cursor()
        try:
            if id:
                cursor.execute('''
                    UPDATE clientes 
                    SET nome_completo = %s, telefone = %s, cpf = %s 
                    WHERE id = %s
                ''', (nome_completo, telefone_limpo, cpf or None, id))
                flash('Cliente atualizado com sucesso!', 'success')
            else:
                cursor.execute('''
                    INSERT INTO clientes (nome_completo, telefone, cpf)
                    VALUES (%s, %s, %s)
                ''', (nome_completo, telefone_limpo, cpf or None))
                flash('Cliente cadastrado com sucesso!', 'success')
            
            mysql.connection.commit()
            return redirect(url_for('listar_clientes'))
            
        except Exception as e:
            flash(f'Erro ao salvar cliente: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    cliente = None
    if id:
        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM clientes WHERE id = %s', (id,))
        cliente = cursor.fetchone()
        cursor.close()
        if not cliente:
            flash('Cliente não encontrado', 'danger')
            return redirect(url_for('listar_clientes'))
    
    return render_template('clientes/formulario.html', 
                         cliente=cliente,
                         now=datetime.now())

@app.route('/clientes/excluir/<int:id>')
@login_required
def excluir_cliente(id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('UPDATE clientes SET ativo = FALSE WHERE id = %s', (id,))
        mysql.connection.commit()
        flash('Cliente marcado como inativo!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir cliente: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('listar_clientes'))

@app.route('/fiado', methods=['GET', 'POST'])
@login_required
def gerenciar_fiado():
    cursor = None
    try:
        if request.method == 'POST':
            # Verificação dos campos obrigatórios
            required_fields = ['cliente_id', 'itens_json']
            if not all(field in request.form for field in required_fields):
                flash('Dados incompletos no formulário', 'danger')
                return redirect(url_for('gerenciar_fiado'))

            try:
                # Processamento dos dados do formulário
                cliente_id = int(request.form['cliente_id'])
                itens_json = request.form['itens_json']
                observacoes = request.form.get('observacoes', '')
                
                # Parse e validação dos itens
                try:
                    itens = json.loads(itens_json)
                    # Conversão para Decimal
                    for item in itens:
                        item['produto_id'] = int(item['produto_id'])
                        item['quantidade'] = int(item['quantidade'])
                        item['preco_unitario'] = Decimal(str(item['preco_unitario']))
                        item['total'] = Decimal(str(item['total']))
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    flash('Formato inválido dos itens do fiado', 'danger')
                    return redirect(url_for('gerenciar_fiado'))
                
                if not itens:
                    flash('Adicione pelo menos um produto ao fiado', 'danger')
                    return redirect(url_for('gerenciar_fiado'))
                
                cursor = mysql.connection.cursor(dictionary=True)
                
                # Validação do cliente
                cursor.execute('SELECT id, limite_fiado FROM clientes WHERE id = %s AND ativo = TRUE', (cliente_id,))
                cliente = cursor.fetchone()
                if not cliente:
                    flash('Cliente não encontrado ou inativo', 'danger')
                    return redirect(url_for('gerenciar_fiado'))
                
                # Cálculo do fiado existente
                cursor.execute('''
                    SELECT COALESCE(SUM(valor_total), 0) as total_fiado 
                    FROM fiado 
                    WHERE cliente_id = %s AND status = "pendente"
                ''', (cliente_id,))
                total_fiado = Decimal(str(cursor.fetchone()['total_fiado']))
                limite_cliente = Decimal(str(cliente['limite_fiado']))
                valor_total_novo = sum(item['total'] for item in itens)
                
                # Validação de limite
                if (total_fiado + valor_total_novo) > limite_cliente:
                    flash(f'Limite de fiado excedido (Limite: R$ {limite_cliente:.2f})', 'danger')
                    return redirect(url_for('gerenciar_fiado'))
                
                # Validação de estoque
                for item in itens:
                    cursor.execute('''
                        SELECT id, nome, preco, quantidade 
                        FROM produtos 
                        WHERE id = %s AND ativo = TRUE
                        FOR UPDATE
                    ''', (item['produto_id'],))
                    produto = cursor.fetchone()
                    
                    if not produto:
                        flash(f'Produto ID {item["produto_id"]} não encontrado ou inativo', 'danger')
                        return redirect(url_for('gerenciar_fiado'))
                    
                    if int(produto['quantidade']) < item['quantidade']:
                        flash(f'Estoque insuficiente para {produto["nome"]} (Disponível: {produto["quantidade"]})', 'danger')
                        return redirect(url_for('gerenciar_fiado'))
                
                # Inserção do fiado
                cursor.execute('''
                    INSERT INTO fiado 
                    (cliente_id, data_compra, observacoes, valor_total, status)
                    VALUES (%s, %s, %s, %s, 'pendente')
                ''', (cliente_id, datetime.now().date(), observacoes, valor_total_novo))
                fiado_id = cursor.lastrowid
                
                # Inserção dos itens e atualização de estoque
                for item in itens:
                    cursor.execute('''
                        INSERT INTO fiado_itens
                        (fiado_id, produto_id, quantidade, valor_unitario, valor_total)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (fiado_id, item['produto_id'], item['quantidade'], item['preco_unitario'], item['total']))
                    
                    cursor.execute('''
                        UPDATE produtos 
                        SET quantidade = quantidade - %s 
                        WHERE id = %s
                    ''', (item['quantidade'], item['produto_id']))
                
                mysql.connection.commit()
                flash('Fiado registrado com sucesso!', 'success')
                return redirect(url_for('gerenciar_fiado'))

            except ValueError as e:
                flash(f'Dados inválidos fornecidos: {str(e)}', 'danger')
                return redirect(url_for('gerenciar_fiado'))
            except Exception as e:
                mysql.connection.rollback()
                flash(f'Erro durante o processamento: {str(e)}', 'danger')
                return redirect(url_for('gerenciar_fiado'))

        # GET Request - Exibição da página
        cursor = mysql.connection.cursor(dictionary=True)
        
        # Consulta fiados pendentes
        cursor.execute('''
            SELECT f.id, c.nome_completo as cliente, 
                   DATE_FORMAT(f.data_compra, '%%d/%%m/%%Y') as data_compra,
                   f.observacoes, f.valor_total
            FROM fiado f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.status = 'pendente'
            ORDER BY f.data_compra DESC
        ''')
        fiados_pendentes = cursor.fetchall()
        
        # Consulta itens para cada fiado
        for fiado in fiados_pendentes:
            cursor.execute('''
                SELECT fi.id, p.nome as produto, fi.quantidade,
                       fi.valor_unitario, fi.valor_total
                FROM fiado_itens fi
                JOIN produtos p ON fi.produto_id = p.id
                WHERE fi.fiado_id = %s
            ''', (fiado['id'],))
            fiado['itens'] = cursor.fetchall()
        
        # Consulta clientes e produtos ativos
        cursor.execute('SELECT id, nome_completo FROM clientes WHERE ativo = TRUE ORDER BY nome_completo')
        clientes = cursor.fetchall()
        
        cursor.execute('SELECT id, nome, preco FROM produtos WHERE ativo = TRUE AND quantidade > 0 ORDER BY nome')
        produtos = cursor.fetchall()
        
        return render_template('fiado/lista.html',
                            fiados_pendentes=fiados_pendentes,
                            clientes=clientes,
                            produtos=produtos,
                            now=datetime.now())

    except Exception as e:
        if 'cursor' in locals() and cursor:
            mysql.connection.rollback()
        flash(f'Erro no sistema: {str(e)}', 'danger')
        return redirect(url_for('gerenciar_fiado'))
    finally:
        if cursor:
            cursor.close()
@app.route('/fiado/quitar/<int:id>')
@login_required
def quitar_fiado(id):
    cursor = mysql.connection.cursor(dictionary=True)
    
    try:
        # Verifica se o fiado existe e está pendente
        cursor.execute('SELECT * FROM fiado WHERE id = %s AND status = "pendente"', (id,))
        fiado = cursor.fetchone()
        
        if not fiado:
            flash('Registro de fiado não encontrado ou já quitado', 'danger')
            return redirect(url_for('gerenciar_fiado'))
        
        # Atualiza o status para pago
        cursor.execute('''
            UPDATE fiado 
            SET status = 'pago', data_pagamento = %s 
            WHERE id = %s
        ''', (datetime.now().date(), id))
        
        mysql.connection.commit()
        flash('Fiado quitado com sucesso!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Erro ao quitar fiado: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('gerenciar_fiado'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')