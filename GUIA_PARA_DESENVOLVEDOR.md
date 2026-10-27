# Guia detalhado para o desenvolvedor — Reis Cell Cash

## 1. Para que serve este pacote

Este pacote reúne o protótipo local do Reis Cell Cash, as regras de negócio conhecidas e um conjunto de dados FAQ pronto para leitura/importação. O desenvolvedor pode estudar o fluxo atual e integrar/adaptar as partes necessárias ao sistema que já está em andamento.

**Importante:** esta é uma entrega para desenvolvimento/homologação. Não existe integração ativa com o sistema de destino, e o banco SQLite incluído é uma base de referência para as FAQs, não uma escolha do banco de produção do outro sistema.

## 2. Conteúdo do pacote

```text
.                                  # raiz do repositório
├── index.html                         # protótipo POS completo (HTML/CSS/JS)
├── README.md                          # funcionalidades atuais e limitações
├── INTEGRACAO_TECNICA.md              # resumo do modelo e requisitos POS
├── BRIEF_TECNICO_INTEGRACAO.docx      # resumo para leitura/compartilhamento
├── GUIA_PARA_DESENVOLVEDOR.md         # este guia, instruções detalhadas
└── database/
    ├── faq_source.txt                 # conteúdo original recebido (20 perguntas/respostas)
    ├── faq_ilug_rc_store.sqlite       # SQLite de referência, com 20 FAQs
    ├── faq_seed.json                 # exportação JSON do mesmo conteúdo
    ├── faq_schema_seed.sql            # schema e INSERTs de carga inicial SQLite
    └── build_faq_db.py                # reconstrói SQLite, JSON e SQL usando Python padrão
```

## 3. Banco incluído: dados FAQ atuais

A pasta `database` contém **20 perguntas e respostas** extraídas do texto fornecido pela loja. O texto das respostas, emojis, links e quebras de parágrafo foi mantido. Nenhuma resposta foi reescrita ou validada como afirmação jurídica/comercial.

### Schema SQLite

Tabela `faq_entries`:

| Campo | Tipo | Uso |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Identificador local inicial, igual ao número de origem (1–20) |
| `source_number` | INTEGER UNIQUE NOT NULL | Número original da FAQ; preservar ordem e rastreabilidade |
| `question` | TEXT NOT NULL | Pergunta original |
| `answer` | TEXT NOT NULL | Resposta integral original, incluindo quebras de linha e emojis |
| `locale` | TEXT | `pt-BR` |
| `review_status` | TEXT | `pending_business_review` até aprovação da loja |
| `source_file` | TEXT | Nome do arquivo de origem |

Tabela `dataset_metadata` documenta origem, versão do schema e necessidade de revisão.

### Inspecionar e consultar

Com o comando SQLite:

```sql
SELECT source_number, question, review_status
FROM faq_entries
ORDER BY source_number;

SELECT answer
FROM faq_entries
WHERE source_number = 10;
```

Ou com Python padrão:

```python
import sqlite3

with sqlite3.connect("database/faq_ilug_rc_store.sqlite") as db:
    for row in db.execute(
        "SELECT source_number, question, answer FROM faq_entries ORDER BY source_number"
    ):
        print(row)
```

### Reconstruir os arquivos derivados

Requer Python 3 e usa somente módulos padrão (`sqlite3`, `json`, `re`, `pathlib`):

```bash
python database/build_faq_db.py
```

O script lê `database/faq_source.txt`, verifica 20 registros numerados de 01 a 20 e gera novamente o SQLite, JSON e SQL seed. **Ele substitui o SQLite de referência existente**; faça cópia antes se alguém já tiver editado esse DB manualmente. O arquivo de origem é o material a preservar.

### Importar para o banco do sistema de destino

O outro desenvolvedor deve adaptar a tabela aos padrões do sistema em andamento e:

1. Confirmar qual banco/ORM e estratégia de migração o projeto já utiliza; não assumir que SQLite será o banco de produção.
2. Criar os registros usando migração/seed versionado e consultas parametrizadas.
3. Preservar `source_number` como chave de origem, a ordem e os textos completos. Gerar IDs próprios no sistema destino e guardar o mapeamento se o schema usar outra chave.
4. Definir se a FAQ será publicada no site/chatbot, usada apenas como base interna ou passará por revisão editorial antes de uso.
5. Não promover automaticamente `pending_business_review` para publicado. A loja deve validar especialmente condições de caução/reembolso, análise cadastral, atraso/bloqueio de aplicativos, disponibilidade, horários e instruções sobre CPF/contrato antes de mostrar ao consumidor.
6. Se atualizar uma resposta, registrar a alteração e a versão aprovada; não alterar o arquivo original recebido sem manter histórico.

## 4. Dados operacionais do POS: o que está e o que não está no ZIP

O código do protótipo está incluído. Os dados operacionais que podem existir no navegador — produtos cadastrados, estoque atual, vendas, vendedores, turnos/fechamentos e usuários locais — **não são parte deste ZIP**. Eles ficam no `localStorage` do navegador/perfil que abriu o `index.html`; o CSV dos relatórios não é um backup completo.

As chaves persistidas no app usam o prefixo `vertice_`, incluindo `products`, `sales`, `sellers`, `cashOpen`, `cashShift`, `cashShifts`, `saleNo` e `managerUsers`. Antes da migração real, localizar o perfil/navegador correto e gerar uma exportação controlada do `localStorage` com confirmação da loja. Não usar dados do navegador de teste.

**Não migrar** `managerUsers`, senhas, hashes ou salts como usuários de produção. A autenticação do protótipo é local e não é uma fronteira segura. Criar usuários/roles no sistema destino pelo mecanismo oficial dele.

Se os dados operacionais atuais também forem necessários, solicitar ao responsável da loja uma exportação JSON do perfil correto e verificar, antes da carga:

- quantidade de produtos, vendas, cancelamentos, vendedores e turnos;
- soma de totais e pagamentos por método;
- IDs duplicados ou venda local com mesmo ID (`V0001`, etc.) em perfis diferentes;
- produtos com IMEI/serial e notas que possam conter dados pessoais;
- reconciliação de estoque inicial/final e amostra de vendas canceladas;
- backup original mantido em local protegido e acesso restrito.

Não incluir essa exportação operacional em Drive público. Ela pode conter identificadores de aparelhos, observações e outros dados internos.

## 5. Mapa funcional do POS e invariantes

- Formas de pagamento: `PIX`, `Dinheiro`, `Cartão de débito`, `Cartão de crédito`, `Ilug cell`, `Aparelho`.
- Venda pode dividir o valor entre métodos; pagamentos devem somar exatamente o total.
- Recebíveis: considerar apenas a parte paga em `Ilug cell`, dobrar o valor conforme regra comercial atual e projetar em 12 parcelas mensais, começando no mês seguinte à venda. Distribuir centavos para que a soma feche; não gerar previsão de venda cancelada.
- Cada venda exige vendedor e guarda snapshots de itens/preços. O ID atual `V...` é local e sequencial; não é globalmente único.
- Cancelamento deve preservar registro e motivo e repor estoque exatamente uma vez.
- Venda retroativa deve permanecer fora da conferência do turno atual.
- Caixa tem abertura, fundo inicial, fechamento e conferência por método; manter valores esperados separados dos valores contados.
- Comprovante é não fiscal. O login gerencial é local e provisório.

Para a arquitetura de dados atualmente observada, mapeamento de campos e perguntas sobre API, consultar também `INTEGRACAO_TECNICA.md`.

## 6. Orientação para integração segura

- Obter nome/versão do sistema em andamento, documentação da API, ambiente de homologação e contato técnico antes de implementar chamadas.
- Determinar a fonte oficial de verdade para produto/preço/estoque/vendedor/venda/caixa/FAQ. Evitar manter o mesmo estoque como autoridade em dois sistemas.
- Integrar via API/backend autenticado. Não colocar segredo de API no HTML; não gravar diretamente no banco remoto a partir do navegador.
- Para venda, usar transação atômica no servidor (venda + linhas + pagamentos + baixa de estoque) e chave de idempotência para retries.
- Usar dinheiro em centavos inteiros na API e no banco do destino; converter os valores atuais em reais com regra explícita de arredondamento.
- Criar IDs canônicos do destino e uma tabela de correspondência para referência local, evitando colisão entre IDs locais sequenciais.
- Tratar cancelamento como transição auditável; exigir motivo/autorização e tornar restauração de estoque idempotente.
- Planejar exportação/importação, reconciliação, homologação e rollback antes de trocar a operação real. O protótipo não tem fila offline nem sincronização.

## 7. Testes mínimos para homologação

### FAQ

- Confirmar exatamente 20 linhas; `source_number` de 1 a 20 sem lacunas ou duplicações.
- Comparar pergunta/resposta e acentos/emoji com `faq_source.txt`; verificar preservação de parágrafos e link `https://ilugcell.com.br/`.
- Confirmar status inicial de revisão e que itens não aprovados não são publicados.
- Reexecutar o gerador em cópia de trabalho e validar contagem/ordem após rebuild.

### POS / integração futura

- Venda simples, pagamento dividido, pagamento Ilug, venda retroativa, falta de estoque, retry de rede e cancelamento repetido.
- Conferir total em centavos, baixa/restauração do estoque uma única vez e ausência de registros duplicados.
- Confirmar exclusão de canceladas dos recebíveis e relatórios, preservando histórico.
- Testar migração numa cópia dos dados e comparar contagens/totais antes de qualquer corte de produção.

## 8. Limites e pendências

Este pacote inclui o protótipo e as FAQs fornecidas, mas não conecta ao sistema em andamento e não contém os dados do `localStorage` da loja. Para fechar a integração, o desenvolvedor precisa receber a documentação/API do sistema alvo; para migrar vendas/estoque reais, também é necessária uma exportação aprovada do perfil correto do PDV. As respostas FAQ são conteúdo fornecido pela loja e continuam pendentes de aprovação para publicação.
