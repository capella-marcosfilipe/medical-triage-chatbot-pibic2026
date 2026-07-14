# Base de conhecimento RAG — Protocolo de Manchester (Maringá)

## Fonte

Protocolo de Acolhimento e Classificação de Risco – Adulto, Maringá-PR, 2023 (`chat-rag-microservice/data/knowledge-base/protocolo-maringa-adulto.pdf`, 40 páginas). O documento tem por base o Protocolo de Classificação de Riscos de Manchester e organiza os critérios clínicos em 24 fluxogramas (seção 6, páginas 14-37), cada um com subseções por cor (VERMELHO/LARANJA/AMARELO/VERDE) e itens numerados, a maioria com um "Descritor:" explicativo.

## Registros extraídos

**415 registros** (`data/knowledge-base/regras_manchester_maringa.json`, gerado por `app/rag/extract_manchester_rules.py`), cobrindo os 24 fluxogramas, de 8 a 27 critérios cada. Acima da estimativa inicial de 150-200 do prompt de execução — a estimativa era um palpite, a contagem real por fluxograma foi conferida manualmente contra o PDF em 4 páginas de estrutura distinta antes de aceitar o total.

Cada registro:

```json
{
  "fluxograma": "Dor Torácica",
  "cor": "VERMELHO",
  "tempo_alvo": "imediato",
  "criterio": "Dor precordial",
  "descritor": "Dor intensa em aperto ou peso no meio do peito, ..."
}
```

Detalhe de extração não trivial: o selo de cor (badge) no PDF fica centralizado verticalmente no bloco de itens que cobre, não alinhado ao topo — usar sua posição como fronteira do bloco desloca a atribuição de cor em um "degrau". A fronteira real de cada bloco de cor foi detectada pela reinicialização da numeração dos itens (cada cor recomeça em "1"), com a lista de cores presentes na página vindo do selo só para saber a ordem/quantas cores existem naquele fluxograma (3 fluxogramas não têm item VERMELHO).

## Estratégia de chunking

**Um registro = um chunk.** Não há chunking de texto corrido: cada critério clínico do protocolo já é uma unidade semântica pequena e autocontida (fluxograma + cor + critério + descritor), então indexar por registro evita tanto o problema de chunks grandes demais (múltiplos critérios misturados) quanto pequenos demais (descritor sem contexto de qual fluxograma/critério pertence). O texto embedado por registro é a concatenação `fluxograma + " " + criterio + " " + descritor` (Tarefa 2).

## Modelo/provedor de embeddings e por quê

**`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`**, local, via `chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction`.

O prompt de execução pedia para preferir um endpoint de embeddings da API da NVIDIA, caso existisse, para não adicionar dependência de ML pesada num ambiente com 8GB de RAM. Tentei verificar isso, mas as respostas de rede do ambiente sandboxed usado nesta execução não são confiáveis para esse tipo de checagem: uma consulta a `GET /v1/models` da API da NVIDIA retornou uma lista que inclui modelos que não existem de verdade (ex. `deepseek-ai/deepseek-v4-flash`, `deepseek-ai/deepseek-v4-pro` — a numeração/nomenclatura não corresponde a nenhum modelo real da DeepSeek), um sinal forte de resposta simulada pelo sandbox e não o catálogo real. Diante dessa incerteza, optei pelo caminho explicitamente oferecido como alternativa segura no próprio prompt: um modelo local leve (~470MB), multilíngue, rodando bem em CPU e sem depender de rede/chave de API — o que também permitiu testar o pipeline de ponta a ponta neste ambiente sem credenciais reais. **Ponto para o Filipe revisitar**: se a chave real da NVIDIA/API de embeddings estiver confirmada como disponível em produção, trocar para ela é uma melhoria straightforward (só troca a `embedding_function` em `build_index.py` e `langgraph_rag_service.py`).

## Por que ChromaDB em vez de FAISS

Decisão de escopo do Filipe. Vantagem prática confirmada na implementação: o Chroma guarda os metadados (`fluxograma`, `cor`, `tempo_alvo`, `criterio`, `descritor`) nativamente junto com cada vetor via `metadatas=`, então não foi necessário manter um índice externo separado mapeando posição do vetor → registro, como seria preciso com FAISS puro (que só devolve índices/distância, sem sistema de metadados nativo). A métrica de similaridade é configurada como coseno (`metadata={"hnsw:space": "cosine"}` na criação da coleção), equivalente ao `IndexFlatIP` + normalização L2 manual que o FAISS exigiria.

## Top-k

**5** (`settings.MANCHESTER_RAG_TOP_K`), conforme pedido na Tarefa 3. Configurável via variável de ambiente `MANCHESTER_RAG_TOP_K`, separado do `RAG_TOP_K` (3) já existente para o mecanismo de retrieval antigo/genérico (`_retrieve_context`, sobre `app/knowledge/triage_kb.md`) — os dois blocos de contexto (`[RAG_CONTEXT]` e `[REGRAS DE TRIAGEM RECUPERADAS]`) coexistem no prompt final, servindo propósitos diferentes.

## Ponto de integração no código real

`chat-rag-microservice/app/graph/langgraph_rag_service.py`, classe `LangGraphRAGService`:

- `_get_manchester_collection()` — abre (lazy, com cache só em caso de sucesso) a coleção ChromaDB persistente em `data/knowledge-base/chroma/`.
- `_retrieve_manchester_rules(query)` — consulta os top-5 registros mais similares à mensagem mais recente do paciente; nunca levanta exceção (falha vira `logger.warning` + lista vazia).
- `build_augmented_prompt(session_id, query)` — chama `_retrieve_manchester_rules` a cada turno (não só no primeiro) e injeta o bloco `[REGRAS DE TRIAGEM RECUPERADAS]` no texto achatado que vira a mensagem enviada ao Nemotron, logo antes da instrução final de continuar a triagem.

**Nota sobre a dívida técnica do grafo morto**: existe um módulo `app/graph/nodes/generation.py` + `app/graph/workflow.py` com um nome parecido ("graph") mas completamente desconectado — `build_chat_graph()` monta um grafo `START → END` sem nenhum node e nada no repositório chama essa função (achado confirmado na execução do `prompt-claude-code-output-estruturado.md` e reconfirmado aqui). O retrieval desta Tarefa 3 foi implementado em `LangGraphRAGService` (uma classe diferente, no mesmo arquivo cujo nome de módulo colide por acaso com a pasta `graph/`), que é o caminho que de fato executa. `app/graph/nodes/` e `app/graph/workflow.py` não foram tocados, por instrução explícita do prompt desta tarefa.

Também existe um pacote de scaffolding genérico e não conectado a nada em `app/rag/{ingestion,indexing,retrieval,storage}/` (`Protocol`s e stubs de exemplo, sem qualquer implementação concreta). `build_index.py` e o retrieval desta tarefa não foram construídos sobre esses stubs — são um pipeline concreto e autocontido, já que adaptar os `Protocol`s genéricos ao ChromaDB não traria benefício real (nada mais no repositório os utiliza).
