document.addEventListener('DOMContentLoaded', function() {
    // Elementos do formulário
    const produtoSelect = document.getElementById('produto_id');
    const quantidadeInput = document.getElementById('quantidade');
    const valorItemInput = document.getElementById('valor_item');
    const btnAdicionar = document.getElementById('btn-adicionar');
    const btnRegistrar = document.getElementById('btn-registrar');
    const itensContainer = document.getElementById('itens-fiado');
    const semItensMsg = document.getElementById('sem-itens');
    const totalGeralElement = document.getElementById('total-geral');
    const form = document.getElementById('form-fiado');
    const itensJsonInput = document.getElementById('itens_json');
    
    // Array para armazenar os itens do fiado
    let itensFiado = [];
    
    // Calcula valor do item quando muda produto ou quantidade
    function calcularValorItem() {
        if (produtoSelect.value && quantidadeInput.value) {
            const preco = parseFloat(produtoSelect.selectedOptions[0].dataset.preco);
            const quantidade = parseInt(quantidadeInput.value);
            const total = preco * quantidade;
            valorItemInput.value = total.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });
        } else {
            valorItemInput.value = 'R$ 0,00';
        }
    }
    
    // Adiciona um item ao fiado
    function adicionarItem() {
        if (!produtoSelect.value || !quantidadeInput.value || quantidadeInput.value <= 0) {
            alert('Selecione um produto e informe uma quantidade válida');
            return;
        }
        
        const produtoId = produtoSelect.value;
        const produtoNome = produtoSelect.selectedOptions[0].text.split(' - ')[0];
        const quantidade = parseInt(quantidadeInput.value);
        const precoUnitario = parseFloat(produtoSelect.selectedOptions[0].dataset.preco);
        const totalItem = precoUnitario * quantidade;
        
        // Verifica se o item já existe no fiado
        const itemExistente = itensFiado.find(item => item.produto_id == produtoId);
        
        if (itemExistente) {
            // Atualiza quantidade e total do item existente
            itemExistente.quantidade += quantidade;
            itemExistente.total += totalItem;
        } else {
            // Adiciona novo item
            itensFiado.push({
                produto_id: produtoId,
                produto_nome: produtoNome,
                quantidade: quantidade,
                preco_unitario: precoUnitario,
                total: totalItem
            });
        }
        
        // Atualiza a lista de itens na tela
        atualizarListaItens();
        
        // Limpa os campos para novo item
        produtoSelect.value = '';
        quantidadeInput.value = 1;
        valorItemInput.value = 'R$ 0,00';
        produtoSelect.focus();
    }
    
    // Remove um item do fiado
    function removerItem(produtoId) {
        itensFiado = itensFiado.filter(item => item.produto_id != produtoId);
        atualizarListaItens();
    }
    
    // Atualiza a lista de itens na tela
    function atualizarListaItens() {
        // Limpa a lista
        itensContainer.innerHTML = '';
        
        // Calcula total geral
        let totalGeral = 0;
        
        // Adiciona cada item na tabela
        itensFiado.forEach(item => {
            totalGeral += item.total;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.produto_nome}</td>
                <td>${item.quantidade}</td>
                <td>${item.preco_unitario.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}</td>
                <td>${item.total.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger btn-remover" data-produto-id="${item.produto_id}">
                        <i class="bi bi-trash"></i> Remover
                    </button>
                </td>
            `;
            itensContainer.appendChild(row);
        });
        
        // Atualiza total geral
        totalGeralElement.textContent = totalGeral.toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        });
        
        // Mostra/oculta mensagem de sem itens
        if (itensFiado.length > 0) {
            semItensMsg.style.display = 'none';
            btnRegistrar.disabled = false;
        } else {
            semItensMsg.style.display = 'block';
            btnRegistrar.disabled = true;
        }
        
        // Prepara os itens para envio no formulário
        itensJsonInput.value = JSON.stringify(itensFiado);
    }
    
    // Event listeners
    produtoSelect.addEventListener('change', calcularValorItem);
    quantidadeInput.addEventListener('input', calcularValorItem);
    btnAdicionar.addEventListener('click', adicionarItem);
    
    // Delegated event para os botões de remover (que são dinâmicos)
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('btn-remover')) {
            const produtoId = e.target.getAttribute('data-produto-id');
            removerItem(produtoId);
        }
    });
    
    // Validação do formulário
    form.addEventListener('submit', function(e) {
        if (itensFiado.length === 0 || !document.getElementById('cliente_id').value) {
            e.preventDefault();
            alert('Selecione um cliente e adicione pelo menos um item ao fiado');
        }
    });
});