# Reis Cell Cash — PDV de celulares

Protótipo local de ponto de venda para uma loja de celulares. Abra `index.html` no navegador; não precisa instalar dependências nem iniciar servidor.

## Demo online

https://newtaum.github.io/reis-cash-pdv/

Acesso ao menu Gerencial (dados de demonstração):

- usuário: `Allan`
- senha: `demo-rcstore-2026`

Essa senha demo existe apenas para navegar no protótipo público. Ao usar o sistema com dados reais, cadastre um usuário novo em Gerencial → “Adicionar / ver usuários” e trate o acesso local como provisório (ver limitações abaixo).

## O que já funciona

- Frente de caixa: busca por código, nome, marca ou modelo; carrinho com quantidades e cálculo automático.
- Cadastro, edição, exclusão e consulta de celulares, com SKU, marca, modelo/cor, custo, preço, estoque, mínimo e IMEI opcional.
- Finalização da venda com dois ou mais meios de pagamento (PIX, dinheiro, cartões, Ilug cell e Aparelho), informando o valor destinado a cada um; o total distribuído precisa corresponder exatamente ao total da venda. Para recebíveis, o sistema dobra somente o valor alocado a Ilug cell.
- Botão “Editar valor” no item do carrinho para alterar o preço apenas na venda atual, sem mudar o preço cadastrado do produto.
- Relatórios com filtros por vendedor e período diário, mensal ou anual; indicadores, totais por pagamento, vendas recentes e exportação CSV acompanham os filtros. Um resumo separado mostra a quantidade total de vendas no histórico, o faturamento das concluídas e a quantidade cancelada.
- Recebíveis Ilug cell: só os valores alocados a essa forma de pagamento entram na previsão; o total é dobrado e dividido em 12 parcelas mensais, com centavos ajustados para fechar o valor exato. Em novas vendas, o primeiro vencimento é automático no mês seguinte à venda. Na atualização desta regra, as vendas Ilug cell já registradas são reprojetadas uma única vez com 12 parcelas a partir do mês seguinte ao mês atual; vendas canceladas ficam fora da previsão. A data da 12ª parcela é calculada automaticamente. A contagem em cada mês é a quantidade de parcelas que vencem naquele mês, somando todas as vendas Ilug cell; não é o total restante de uma venda individual.
- Abertura do caixa exige informar o fundo inicial para troco; fechamento pede o valor contado em cada uma das seis formas de pagamento, incluindo Aparelho, compara com o esperado e salva observações e diferenças.
- No fechamento do caixa, abre um relatório diário em texto com total de vendas, resumo por forma de pagamento e lista de produtos/quantidades; pode copiar o texto ou baixar como `.txt`.
- O menu Gerencial pede login. O usuário inicial é Allan; dentro do Gerencial, “Adicionar / ver usuários” permite cadastrar outros logins com senha de pelo menos 10 caracteres. As senhas são guardadas como hashes no navegador; esse bloqueio local é provisório e não equivale à autenticação segura em servidor.
- Cada venda exige vendedor responsável. Em Gerencial também é possível cadastrar/editar/desativar vendedores, consultar cada venda individualmente (itens, pagamentos, vendedor e observações), reabrir comprovante e solicitar cancelamento com motivo e confirmação da senha usada no login; o cancelamento mantém o histórico e devolve o estoque. Também é possível consultar conferências de caixa e registrar venda com data anterior; vendas retroativas ficam fora da conferência do turno atual.
- Ao finalizar a venda, informe o prazo de garantia em dias ou meses (use 0 se não houver prazo para registrar); o prazo e a data final aparecem no comprovante salvo na venda.
- O comprovante de compra não fiscal é exibido após a venda e pode ser reaberto em Gerencial. Use “Imprimir / salvar em PDF” e escolha “Salvar como PDF” na janela de impressão do navegador; o app não emite documento fiscal.
- Atalhos F1 (busca), F2 (nova venda), F4 (finalizar). Layout adaptável inspirado na referência enviada.

## Dados e observações

Os dados ficam no `localStorage` do navegador e deste perfil de usuário. Não há sincronização entre computadores, backup automático, integração com adquirente/cartão ou emissão fiscal/NFC-e. O login do Gerencial é local e provisório: quem tem acesso ao arquivo e ao navegador pode contorná-lo; antes de usar proteção real, migre para autenticação em servidor e troque a senha inicial. Faça exportações/backup antes de limpar os dados do navegador. Na primeira abertura, o catálogo traz um celular de demonstração (iPhone 15 · 128 GB) e um vendedor de exemplo (“Vendedor 1”); edite ou exclua/arquive os registros de demonstração e cadastre os dados reais da loja.

## Preparação para integração

O projeto está preparado para análise do técnico responsável pelo outro sistema, mas ainda não possui API nem sincronização. Consulte `INTEGRACAO_TECNICA.md` e `GUIA_PARA_DESENVOLVEDOR.md` (instruções detalhadas), além de `BRIEF_TECNICO_INTEGRACAO.docx`. A pasta `database/` contém uma base SQLite de referência com as 20 FAQs fornecidas, JSON, SQL seed, texto-fonte e script reprodutível. Os registros operacionais do POS (`localStorage` do navegador: vendas, estoque, vendedores e caixa) não estão incluídos e precisam de exportação separada do perfil correto antes da migração.

Este projeto é uma primeira versão local para demonstração/validação, não substitui um PDV fiscal homologado.

## Dados de operação (repositório privado)

Os registros reais da loja — catálogo, custo, preço e estoque — **não** ficam neste repositório. A exportação de produção de 2026-10-27 (19 SKUs, chave `vertice_products`) está no repositório **privado** `reis-cash-dados`, junto com o contrato de dados (`GUIA_EXPORTACAO_PRODUTOS.md`), a conferência de integridade e a mensagem de importação para o dev.

Nenhum dado real de operação entra neste repositório público, nem no histórico de commits.

## Licença

MIT — veja [LICENSE](LICENSE).
