# Reis Cell Cash — Brief técnico para integração

## Objetivo e status

Este documento prepara o repasse do **Reis Cell Cash** ao técnico responsável pelo outro sistema. Descreve o que existe hoje, as regras de negócio que devem ser preservadas e os pontos que precisam ser definidos com o responsável pelo sistema de destino.

**Status:** o protótipo ainda não está integrado. O nome, a documentação e o acesso ao sistema de destino, sua API, ambiente de teste e responsável técnico ainda não foram informados. Portanto, endpoints e payloads sugeridos aqui são exemplos para alinhamento, não uma integração já implementada.

## Como o PDV funciona hoje

- Aplicação local de navegador: `index.html`, com HTML, CSS e JavaScript no mesmo arquivo.
- Os dados persistem no `localStorage` do navegador/perfil, com prefixo `vertice_`. Não existe servidor, banco remoto, API, sincronização entre computadores ou fila de sincronização.
- Chaves de armazenamento identificadas no código: `products`, `sales`, `sellers`, `cashOpen`, `cashShift`, `cashShifts`, `saleNo` e `managerUsers` (armazenadas com o prefixo `vertice_`).
- O app não deve ser tratado como fonte online compartilhada. Copiar o HTML para outro computador não compartilha os dados.
- O catálogo novo pode conter registros de demonstração (iPhone 15 · 128 GB e Vendedor 1). Eles devem ser revisados e removidos/substituídos antes do corte para produção.
- O relatório CSV existente é um relatório de vendas, não um backup completo nem um formato garantido de migração de todas as entidades.

## Funcionalidades e regras que a integração deve considerar

1. **Produtos e estoque:** busca por código, nome, marca e modelo; cadastro com SKU/código, marca, nome, modelo/cor, preço, custo, quantidade em estoque, estoque mínimo e IMEI opcional.
2. **Vendas:** vendedor obrigatório, observação opcional, garantia em dias ou meses, data/hora, itens e valores vendidos. O comprovante é não fiscal.
3. **Pagamentos divididos:** PIX, Dinheiro, Cartão de débito, Cartão de crédito, Ilug cell e Aparelho. A soma das partes deve corresponder exatamente ao total da venda.
4. **Recebíveis Ilug cell:** somente o valor alocado ao método Ilug cell participa da previsão; a previsão dobra esse valor e o divide em 12 parcelas mensais, com centavos ajustados para fechar o total. A primeira parcela começa no mês seguinte à venda; as demais vencem mensalmente. Vendas canceladas ficam fora da previsão.
5. **Cancelamento:** exige motivo e confirmação local da senha gerencial; mantém o histórico e repõe o estoque. No destino, o cancelamento deve ser uma mudança de estado auditável, e a reposição de estoque deve ocorrer uma única vez.
6. **Vendas retroativas:** podem ser registradas com data anterior e ficam fora da conferência do turno atual.
7. **Caixa:** exige fundo inicial, registra turno, valores contados por forma de pagamento, diferenças e observações. O relatório diário é um resumo operacional.
8. **Relatórios:** filtros por vendedor e período; exportação CSV. Estes relatórios não substituem os registros transacionais do sistema de destino.

## Modelo de dados observado no PDV

O armazenamento atual usa arrays/objetos JavaScript e valores monetários em reais, não uma API pública. Campos conhecidos:

| Entidade | Campos atuais/conhecidos |
|---|---|
| Produto | `id`, `code`, `brand`, `name`, `model`, `price`, `cost`, `stock`, `min`, `imei` |
| Item de venda | `code`, `name`, `brand`, `price`, `qty` — snapshot do produto no momento da venda |
| Venda | `id` local (formato sequencial `V0001`), `date`, `items`, `total`, `payment` (rótulo resumido), `payments` (lista de método/valor), `note`, `seller`, `sellerId`, `shiftId`, `historical`, dados de garantia, situação e campos ligados ao parcelamento Ilug cell |
| Vendedor | `id`, `name` e estado ativo/inativo conforme cadastro |
| Caixa | estado de abertura e turno atual; histórico de turnos/fechamentos no navegador |

A lista acima descreve o protótipo, não um contrato estável. O técnico deve conferir o arquivo e validar os campos antes de implementar importação. Campos que não forem mapeados devem ser preservados ou migrados explicitamente, não descartados silenciosamente.

## Diretriz de integração recomendada

- Usar uma API autenticada/documentada do sistema existente; não acessar diretamente o banco de dados do outro sistema e não colocar segredo de API dentro do HTML distribuído ao navegador.
- Definir com o responsável qual sistema é a fonte oficial de produtos, preços, estoque, usuários/vendedores, vendas, caixa e recebíveis. Cada dado deve ter uma fonte de verdade para evitar divergência e dupla baixa de estoque.
- Para valores financeiros na API, preferir centavos inteiros (por exemplo, `479990`) e converter explicitamente da representação atual em reais. Quantidades devem ser inteiras.
- Ao concluir uma venda, o servidor deve validar preço/estoque e gravar venda, itens e pagamentos atomicamente. Usar chave de idempotência para que repetição de envio/rede não crie uma venda nem dê baixa de estoque duas vezes.
- Usar ID canônico gerado pelo servidor e guardar o vínculo com o ID local `V...`; o contador local pode colidir entre navegadores.
- Registrar cancelamento como evento/estado com motivo, usuário e data/hora. Repor estoque uma única vez, mantendo os snapshots originais da venda.
- Definir timezone e padrão de data/hora (recomendação: ISO 8601 com offset/timezone explícito) e como tratar vendas retroativas.
- Se houver uso offline, projetar fila, retries, conflito de estoque, idempotência e resolução de divergências separadamente. O protótipo atual não possui fila de sincronização offline.
- A autenticação atual do Gerencial é local e provisória. Não importar `managerUsers`, hashes ou salts como identidade do sistema destino; usar o login/controle de acesso central do sistema existente.

### Exemplo conceitual de venda enviada

Exemplo apenas para discussão do contrato; não é payload implementado nem endpoint existente. Usar o identificador de produto aceito pelo sistema de destino e adaptar nomes/códigos conforme a documentação oficial.

```json
{
  "client_reference": "V0001",
  "occurred_at": "2026-10-24T14:30:00-03:00",
  "seller_reference": "ID_DO_VENDEDOR",
  "historical": false,
  "items": [
    {
      "sku": "APL-IP15-128",
      "name_snapshot": "iPhone 15 · 128 GB",
      "quantity": 1,
      "unit_price_cents": 479990
    }
  ],
  "payments": [
    {"method": "PIX", "amount_cents": 10000},
    {"method": "Ilug cell", "amount_cents": 469990}
  ],
  "warranty": {"amount": 90, "unit": "days"},
  "note": ""
}
```

O servidor deve validar que os pagamentos somam o total calculado, resolver os IDs de produto/vendedor, registrar o ator/autorização e retornar o ID definitivo e o estado final da venda. Se o sistema de destino já fornece uma estrutura própria, ela prevalece após validação conjunta.

## Endpoints a discutir (não implementados)

Ajustar aos serviços reais do destino. Esta lista serve como checklist de capacidades, não como exigência de nomes/rotas:

- Consultar produtos e disponibilidade de estoque; definir se o PDV recebe alterações ou apenas consulta.
- Consultar vendedores/usuários ativos.
- Criar venda com itens e múltiplos pagamentos, com validação e idempotência.
- Consultar venda por ID/referência local.
- Cancelar venda com motivo, autorização e reposição de estoque idempotente.
- Abrir/fechar turno de caixa e enviar conferência por forma de pagamento, se o outro sistema possuir esse módulo.
- Consultar/exportar histórico e recebíveis Ilug cell, caso o destino seja responsável por essa regra.

## Informações necessárias do técnico do sistema de destino

1. Nome e versão do sistema; ambiente de homologação/teste e documentação oficial da API.
2. Autenticação, permissões, CORS/rede, limites e requisitos de segurança.
3. Sentido do fluxo: quais dados o PDV envia, recebe ou sincroniza em ambos os sentidos.
4. Fonte oficial de verdade para produtos, preço, estoque, vendedores, vendas, cancelamentos, caixa e previsão Ilug cell.
5. Chaves de correspondência: SKU/código de barras, ID do produto, IMEI, ID do vendedor, loja/filial e caixa/terminal.
6. Regras do destino para venda dividida, arredondamento, estorno, data retroativa e fechamento por método de pagamento.
7. Se é necessário importar vendas antigas e desde qual data; formato, IDs e processo de conferência antes do corte.
8. Responsável por homologação, plano de rollback, backup e critérios de aceite.

## Critérios mínimos de aceite

- Produto/vendedor desconhecido ou inativo é tratado sem criar venda parcialmente válida.
- Total dos pagamentos coincide com o total da venda, em centavos.
- Reenvio da mesma operação não duplica venda, recebíveis nem baixa de estoque.
- Cancelamento exige motivo e autorização; registra auditoria e restitui estoque uma única vez.
- Recebíveis Ilug seguem a regra de 12 parcelas, somente sobre a parte Ilug e com início no mês seguinte; canceladas são excluídas.
- Vendas retroativas não alteram a conferência de um turno atual indevidamente.
- Nenhuma senha, hash, salt ou segredo de API é exposto no navegador, em logs ou neste pacote.
- Homologação cobre venda simples, pagamento dividido, Ilug cell, falta de estoque, erro/retry de rede, cancelamento repetido e reconciliação de caixa.

## FAQ fornecida e base de referência

A pasta `database/` inclui 20 FAQs fornecidas pela loja em `faq_source.txt`, um banco SQLite de referência (`faq_ilug_rc_store.sqlite`), seed JSON, SQL de criação/carga e `build_faq_db.py` para reconstrução. O schema incluído é demonstrativo e não define o banco de produção do sistema em andamento. Os registros começam como `pending_business_review`; validar informações comerciais/contratuais antes de publicar.

Para instruções de leitura, importação, migração POS e homologação, consultar `GUIA_PARA_DESENVOLVEDOR.md`. O conteúdo da base FAQ é separado das vendas/produtos/turnos do POS, que continuam no `localStorage` do perfil de navegador e não foram exportados neste pacote.

## Limites do pacote

Este brief não cria conexão, credenciais, endpoint nem sincronização. Para implementar a integração, o técnico precisa fornecer a documentação/contato do sistema de destino e decidir os pontos pendentes acima. O projeto atual permanece local até essa etapa.
