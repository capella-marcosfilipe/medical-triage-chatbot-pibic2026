# Base de conhecimento — Protocolo de Maringá

`regras_manchester_maringa.json`: 415 registros extraídos de `protocolo-maringa-adulto.pdf` (Protocolo de Acolhimento e Classificação de Risco – Adulto, Maringá-PR, 2023), cobrindo os 24 fluxogramas do documento (seção 6, páginas 14-37).

Cada registro tem o formato:

```json
{
  "fluxograma": "Dor Torácica",
  "cor": "VERMELHO",
  "tempo_alvo": "imediato",
  "criterio": "Dor precordial",
  "descritor": "Dor intensa em aperto ou peso no meio do peito, ..."
}
```

Gerado por `app/rag/extract_manchester_rules.py` (re-executável via `python -m app.rag.extract_manchester_rules` a partir de `chat-rag-microservice/`).

# TRAG: cada registro aqui já tem o formato critério→cor que uma regra if-then formal precisaria; falta validação médica formal de cada mapeamento e uma lógica de match estrito em vez de similaridade semântica.
