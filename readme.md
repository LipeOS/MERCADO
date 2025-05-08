## Projeto Flask com MySQL - Biblioteca

Este é um projeto básico utilizando Flask com integração ao MySQL para gerenciar uma biblioteca de livros.

### Pré-requisitos

- Python: [Download Python](https://www.python.org/downloads/)
- Flask: Instale usando `pip install Flask`
- MySQL Server: Baixe e instale em [dev.mysql.com](https://dev.mysql.com/downloads/mysql/)
- Flask-MySQLdb: Instale usando `pip install Flask-MySQLdb`

### Configuração

1. Clone o repositório ou baixe o código-fonte.
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure o MySQL:
   - Crie um banco de dados chamado `biblioteca`.
   - Execute o script SQL para criar a tabela de livros dentro do banco de dados.
   

````sql

CREATE DATABASE IF NOT EXISTS mercadinho;
USE mercadinho;

-- Tabela de produtos (mantida igual)
CREATE TABLE produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(255),
    preco DECIMAL(10,2) NOT NULL CHECK (preco >= 0),
    preco_custo DECIMAL(10,2),
    quantidade INT NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    quantidade_minima INT DEFAULT 3,
    categoria VARCHAR(50) DEFAULT 'Outros',
    codigo_barras VARCHAR(20) UNIQUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE
);

-- Tabela de clientes (mantida igual)
CREATE TABLE clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    telefone VARCHAR(20),
    cpf VARCHAR(11) UNIQUE,
    endereco VARCHAR(255),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    limite_fiado DECIMAL(10,2) DEFAULT 200.00,
    ativo BOOLEAN DEFAULT TRUE
);

-- Nova estrutura para tabela fiado (modificada)
CREATE TABLE fiado (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    data_compra DATE NOT NULL,
    data_pagamento DATE,
    status ENUM('pendente', 'pago', 'cancelado') DEFAULT 'pendente',
    observacoes TEXT,
    valor_total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    INDEX idx_cliente_status (cliente_id, status),
    INDEX idx_data_compra (data_compra)
);

-- Nova tabela para itens do fiado
CREATE TABLE fiado_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fiado_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL CHECK (quantidade > 0),
    valor_unitario DECIMAL(10,2) NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (fiado_id) REFERENCES fiado(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE RESTRICT,
    INDEX idx_fiado (fiado_id),
    INDEX idx_produto (produto_id)
);


-- Tabela de usuários (mantida igual)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    nivel_acesso ENUM('admin', 'operador') DEFAULT 'operador',
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

4. Edite as configurações do MySQL no arquivo `app.py` conforme necessário.

### Executando o Projeto

1. No terminal, navegue até o diretório do projeto.
2. Execute o comando: `python app.py`
3. Abra seu navegador e vá para `http://localhost:5000/` para acessar a aplicação.

### Funcionalidades

- Adicionar livros
- Pesquisar livros por título ou autor
- Editar quantidade de livros
- Excluir livros da biblioteca

### Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para enviar pull requests ou reportar problemas.

### Autor

Felipe Oliveira Silva
