# 📊 Padrão de Planilha para o App

Para que o sistema leia seus dados corretamente mês a mês, sua planilha deve seguir exatamente esta estrutura:

## 1. Aba: `Cliente`
Esta aba deve conter as informações básicas do seu negócio.
- **Linha 5:** Empresa | [Nome da sua Empresa]
- **Linha 6:** Categoria macro (texto) | [Ex: ferramentas]
- **Linha 7:** Ticket médio do cliente (R$) | [Valor]
- **Linha 8:** Margem atual (%) | [Valor]
- **Linha 9:** Faturamento médio | [Valor]
- **Linha 10:** Unidades médias | [Valor]
- **Linha 11:** Range permitido | [Valor, ex: 20]

## 2. Aba: `Mercado_Categoria`
Contém o histórico macro da categoria.
- **Linha 3 (Cabeçalho):** Categoria | Periodo | Faturamento | Unidades
- O sistema lerá todas as linhas a partir da linha 4.

## 3. Abas de Subcategorias (Uma para cada Categoria Macro)
Crie uma aba com o **mesmo nome** da categoria macro (ex: `Ferramentas`, `Casa, Móveis e Decoração`).
- **Linha 16 (Cabeçalho):** Subcategoria | Janeiro - Faturamento | Janeiro - Unidades | Fevereiro - Faturamento | Fevereiro - Unidades ...
- Você pode adicionar quantos meses quiser seguindo o padrão `Nome do Mês - Tipo`.

### 💡 Dicas Importantes:
1. **Nomes das Abas:** Devem ser idênticos aos nomes usados na coluna "Categoria".
2. **Datas:** O sistema aceita datas no formato `DD/MM/YYYY` ou apenas o nome do mês.
3. **Números:** Pode usar `R$`, pontos e vírgulas normalmente.
