// Função para confirmar exclusão
function confirmarExclusao(url) {
    if (confirm('Tem certeza que deseja excluir este cliente?')) {
        window.location.href = url;
    }
}

// Máscaras e validações
document.addEventListener('DOMContentLoaded', function() {
    // Máscara para telefone
    const telefoneInput = document.getElementById('telefone');
    if (telefoneInput) {
        telefoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 0) {
                value = value.replace(/^(\d{2})(\d)/g, '($1) $2');
                if (value.length > 10) {
                    value = value.replace(/(\d)(\d{4})$/, '$1-$2');
                }
            }
            e.target.value = value;
        });
    }

    // Máscara para CPF
    const cpfInput = document.getElementById('cpf');
    if (cpfInput) {
        cpfInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 0) {
                value = value.replace(/^(\d{3})(\d)/g, '$1.$2');
                value = value.replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3');
                value = value.replace(/\.(\d{3})(\d)/, '.$1-$2');
                value = value.substring(0, 14);
            }
            e.target.value = value;
        });
    }

    // Validação do formulário
    const form = document.getElementById('form-cliente');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Limpa CPF antes de enviar (remove pontos e traço)
            const cpfInput = document.getElementById('cpf');
            if (cpfInput && cpfInput.value) {
                cpfInput.value = cpfInput.value.replace(/\D/g, '');
            }
            
            // Limpa telefone antes de enviar (remove parênteses, espaços e traço)
            const telInput = document.getElementById('telefone');
            if (telInput && telInput.value) {
                telInput.value = telInput.value.replace(/\D/g, '');
            }
        });
    }
});