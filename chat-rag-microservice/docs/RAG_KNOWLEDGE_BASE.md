# Base de conhecimento RAG — Protocolo de Manchester (Maringá)

## Fonte

Protocolo de Acolhimento e Classificação de Risco – Adulto, Maringá-PR, 2023 (`data/knowledge-base/protocolo-maringa-adulto.pdf`, 40 páginas). Baseado no Protocolo de Classificação de Riscos de Manchester, organiza os critérios clínicos em 24 fluxogramas (páginas 14-37), cada um com subseções por cor (VERMELHO/LARANJA/AMARELO/VERDE) e itens numerados, a maioria com um "Descritor:" explicativo.

## Registros

**415 registros** (`data/knowledge-base/regras_manchester_maringa.json`, gerado por `app/rag/extract_manchester_rules.py`), de 8 a 27 por fluxograma. Formato:

```json
{
  "fluxograma": "Dor Torácica",
  "cor": "VERMELHO",
  "tempo_alvo": "imediato",
  "criterio": "Dor precordial",
  "descritor": "Dor intensa em aperto ou peso no meio do peito, ..."
}
```

O selo de cor no PDF fica centralizado no bloco de itens que cobre, não alinhado ao topo, então a fronteira de cada bloco é detectada pela reinicialização da numeração dos itens (cada cor recomeça em "1"), não pela posição do selo.

## Chunking

**Um registro = um chunk.** Cada critério já é uma unidade semântica pequena e autocontida; o texto embedado por registro é `fluxograma + criterio + descritor`.

## Embeddings

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, local, via `chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction`. Modelo leve (~470MB), multilíngue, roda bem em CPU — evita dependência de API externa e de credenciais no pipeline de indexação e retrieval.

## ChromaDB em vez de FAISS

O Chroma guarda os metadados (`fluxograma`, `cor`, `tempo_alvo`, `criterio`, `descritor`) nativamente junto com cada vetor, dispensando um índice externo separado para mapear vetor → registro, como seria necessário com FAISS puro. Métrica de similaridade: cosseno (`metadata={"hnsw:space": "cosine"}`).

## Top-k

**5** (`settings.MANCHESTER_RAG_TOP_K`), separado do `RAG_TOP_K` (3) do mecanismo de retrieval genérico já existente (`_retrieve_context`, sobre `app/knowledge/triage_kb.md`) — os blocos `[RAG_CONTEXT]` e `[REGRAS DE TRIAGEM RECUPERADAS]` coexistem no prompt final.

## Acesso ao ChromaDB

`app/rag/storage/manchester_repository.py` centraliza todo acesso ao ChromaDB desta base: `ManchesterRulesRepository` (client + embedding function, `upsert`/`query`/`count`) e o `Protocol` `ManchesterRulesReader` (interface de leitura usada para injeção de dependência). `build_index.py` e `LangGraphRAGService` dependem deste repositório em vez de instanciar o ChromaDB cada um por conta própria.

## Integração

`app/graph/langgraph_rag_service.py`, classe `LangGraphRAGService`:

- Recebe um `ManchesterRulesReader` no construtor (`manchester_rules`), com um `ManchesterRulesRepository` real como padrão quando nenhum é injetado — permite testes substituírem por um fake sem tocar o ChromaDB.
- `_retrieve_manchester_rules(query)` — delega ao repositório injetado (top-5 registros mais similares à mensagem mais recente do paciente); falhas são logadas e tratadas sem interromper a conversa.
- `build_augmented_prompt(session_id, query)` — chama o retrieval a cada turno (não só no primeiro) e injeta o bloco `[REGRAS DE TRIAGEM RECUPERADAS]` no prompt final, antes da instrução de encerramento.

## Dívida técnica conhecida

`app/graph/nodes/` e `app/graph/workflow.py` não são usados por nenhum caminho de execução real — `build_chat_graph()` monta um grafo `START → END` sem nós, e nada no repositório o invoca. O caminho realmente ativo é `LangGraphRAGService` (mesmo diretório `graph/`, classe diferente). O retrieval desta base foi implementado ali, não no módulo morto.

Da mesma forma, `app/rag/{ingestion,indexing,retrieval,storage}/vector_store.py`/`embedder.py`/etc. contêm `Protocol`s e stubs genéricos sem uso real (trabalham com vetores pré-computados e strings simples, não com texto + metadados como o ChromaDB usa aqui). `manchester_repository.py` é uma implementação própria, não uma adaptação desses stubs.
