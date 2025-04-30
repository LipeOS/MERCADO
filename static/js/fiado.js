document.addEventListener('DOMContentLoaded', function() {
    // Calcula valor total quando muda produto ou quantidade
    const produtoSelect = document.getElementById('produto_id');
    const quantidadeInput = document.getElementById('quantidade');
    const valorTotalInput = document.getElementById('valor_total');

    function calcularTotal() {
        if (produtoSelect.value && quantidadeInput.value) {
            const preco = parseFloat(produtoSelect.selectedOptions[0].dataset.preco);
            const quantidade = parseInt(quantidadeInput.value);
            const total = preco * quantidade;
            valorTotalInput.value = total.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });
        } else {
            valorTotalInput.value = 'R$ 0,00';
        }
    }

    produtoSelect.addEventListener('change', calcularTotal);
    quantidadeInput.addEventListener('input', calcularTotal);

    // Validação do formulário
    const form = document.getElementById('form-fiado');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Validações adicionais podem ser adicionadas aqui
            if (!produtoSelect.value || !quantidadeInput.value || quantidadeInput.value <= 0) {
                e.preventDefault();
                alert('Preencha todos os campos obrigatórios corretamente');
            }
        });
    }
});