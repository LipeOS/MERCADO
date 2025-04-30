from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysql_connector import MySQL
from datetime import datetime
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
    if request.method == 'POST':
        try:
            cliente_id = int(request.form['cliente_id'])
            produto_id = int(request.form['produto_id'])
            quantidade = int(request.form['quantidade'])
            observacoes = request.form.get('observacoes', '')

            if quantidade <= 0:
                flash('Quantidade deve ser maior que zero', 'danger')
                return redirect(url_for('gerenciar_fiado'))

            cursor = mysql.connection.cursor(dictionary=True)
            
            cursor.execute('SELECT id, limite_fiado FROM clientes WHERE id = %s AND ativo = TRUE', (cliente_id,))
            cliente = cursor.fetchone()
            if not cliente:
                flash('Cliente não encontrado ou inativo', 'danger')
                return redirect(url_for('gerenciar_fiado'))

            cursor.execute('SELECT id, nome, preco, quantidade FROM produtos WHERE id = %s AND ativo = TRUE', (produto_id,))
            produto = cursor.fetchone()
            if not produto:
                flash('Produto não encontrado ou inativo', 'danger')
                return redirect(url_for('gerenciar_fiado'))

            if produto['quantidade'] < quantidade:
                flash('Quantidade em estoque insuficiente', 'danger')
                return redirect(url_for('gerenciar_fiado'))

            valor_total = produto['preco'] * quantidade

            cursor.execute('''
                SELECT COALESCE(SUM(valor_total), 0) as total_fiado 
                FROM fiado 
                WHERE cliente_id = %s AND status = "pendente"
            ''', (cliente_id,))
            total_fiado = cursor.fetchone()['total_fiado']

            if (total_fiado + valor_total) > cliente['limite_fiado']:
                flash(f'Limite de fiado excedido (Limite: R$ {cliente["limite_fiado"]:.2f})', 'danger')
                return redirect(url_for('gerenciar_fiado'))

            cursor.execute('''
                INSERT INTO fiado 
                (cliente_id, produto_id, quantidade, valor_unitario, valor_total, data_compra, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (cliente_id, produto_id, quantidade, produto['preco'], valor_total, datetime.now().date(), observacoes))

            cursor.execute('''
                UPDATE produtos 
                SET quantidade = quantidade - %s 
                WHERE id = %s
            ''', (quantidade, produto_id))

            mysql.connection.commit()
            return redirect(url_for('gerenciar_fiado'))

        except ValueError:
            flash('Dados inválidos fornecidos', 'danger')
        except Exception as e:
            flash(f'Erro ao registrar venda fiada: {str(e)}', 'danger')
        finally:
            cursor.close()

    cursor = mysql.connection.cursor(dictionary=True)
    
    cursor.execute('''
        SELECT f.id, c.nome_completo as cliente, p.nome as produto, 
               f.quantidade, f.valor_unitario, f.valor_total, 
               DATE_FORMAT(f.data_compra, '%%d/%%m/%%Y') as data_compra, 
               f.observacoes
        FROM fiado f
        JOIN clientes c ON f.cliente_id = c.id
        JOIN produtos p ON f.produto_id = p.id
        WHERE f.status = 'pendente'
        ORDER BY f.data_compra DESC
    ''')
    fiados_pendentes = cursor.fetchall()
    
    cursor.execute('SELECT id, nome_completo FROM clientes WHERE ativo = TRUE ORDER BY nome_completo')
    clientes = cursor.fetchall()
    
    cursor.execute('SELECT id, nome, preco FROM produtos WHERE ativo = TRUE AND quantidade > 0 ORDER BY nome')
    produtos = cursor.fetchall()
    
    cursor.close()
    
    return render_template('fiado/lista.html',
                         fiados_pendentes=fiados_pendentes,
                         clientes=clientes,
                         produtos=produtos,
                         now=datetime.now())

@app.route('/fiado/quitar/<int:id>')
@login_required
def quitar_fiado(id):
    cursor = mysql.connection.cursor(dictionary=True)
    
    try:
        cursor.execute('SELECT * FROM fiado WHERE id = %s AND status = "pendente"', (id,))
        fiado = cursor.fetchone()
        
        if not fiado:
            flash('Registro de fiado não encontrado ou já quitado', 'danger')
            return redirect(url_for('gerenciar_fiado'))
        
        cursor.execute('''
            UPDATE fiado 
            SET status = 'pago', data_pagamento = %s 
            WHERE id = %s
        ''', (datetime.now().date(), id))
        
        mysql.connection.commit()
        
        
    except Exception as e:
        flash(f'Erro ao quitar fiado: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('gerenciar_fiado'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')