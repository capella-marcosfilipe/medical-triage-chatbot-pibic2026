"""One-off extraction of the Manchester-based triage criteria from the
Protocolo de Acolhimento e Classificação de Risco - Adulto (Maringá, 2023).

# TRAG: each record here already has the criterio->cor format that a formal
# if-then rule would need; what's missing is formal medical validation of
# each mapping and a strict-match lookup instead of semantic similarity
# search over the embeddings built in build_index.py.

Run as a script (from chat-rag-microservice/):

    python -m app.rag.extract_manchester_rules

Reads data/knowledge-base/protocolo-maringa-adulto.pdf and writes
data/knowledge-base/regras_manchester_maringa.json.

The PDF lays out each fluxograma on its own page (14-37): a color badge
("VERMELHO"/"LARANJA"/"AMARELO"/"VERDE" + a time annotation like
"(IMEDIATO)"/"(10 MINUTOS)") sits in a narrow left column, while the
numbered criteria and their "Descritor:" text sit in a wider column to the
right. pdfplumber's default `extract_text()` interleaves these two columns
in an unreliable reading order, so this script works from word bounding
boxes instead: words are split into a "badge" column (x0 < BADGE_COLUMN_MAX_X)
and a "content" column, lines are reconstructed by clustering words with a
close `top` coordinate, and each content line is assigned to whichever
color badge's vertical band it falls into.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

PDF_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge-base" / "protocolo-maringa-adulto.pdf"
OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge-base" / "regras_manchester_maringa.json"

# 0-indexed page range covering "6. Fluxograma e Descritores - Classificação
# de Risco Adulto" (one fluxograma per page, confirmed against the PDF's own
# sumário on page 4).
FIRST_FLUXOGRAMA_PAGE = 13
LAST_FLUXOGRAMA_PAGE = 36

# Canonical titles from the PDF's sumário (page 4), in page order. Read from
# the sumário instead of each page's own header text because a couple of
# section headers render with a broken leading drop-cap letter in
# extract_words() (e.g. "5. Diarreia e vômitos" loses its "5. D").
FLUXOGRAMA_TITULOS = [
    "Alterações cutâneas",
    "Alterações do nível de consciência, comportamento ou sensório",
    "Convulsões",
    "Desmaio, tontura, vertigem",
    "Diarreia e vômitos",
    "Dor abdominal ou queixas abdominais",
    "Dor cervical",
    "Dor de cabeça",
    "Dor de garganta",
    "Dor na coluna e em extremidades",
    "Dor torácica",
    "Exposição a agentes químicos",
    "Mordeduras e picadas de animais",
    "Mal-estar geral",
    "Palpitações",
    "Politraumas",
    "Queimaduras",
    "Queixas oculares",
    "Queixas otológicas",
    "Queixas respiratórias",
    "Queixas urinárias / Dor testicular",
    "Sangramentos",
    "Trauma torocoabdominal",
    "Traumas",
]

BADGE_COLUMN_MAX_X = 145.0
LINE_CLUSTER_TOLERANCE = 2.5
KNOWN_COLORS = ("VERMELHO", "LARANJA", "AMARELO", "VERDE")
TEMPO_ALVO_BY_COLOR = {
    "VERMELHO": "imediato",
    "LARANJA": "10 minutos",
    "AMARELO": "60 minutos",
    "VERDE": "120 minutos",
}
ITEM_START_PATTERN = re.compile(r"^\d+\s*[-–]\s*(.+)$")
DESCRITOR_PATTERN = re.compile(r"^Descritor:\s*(.*)$", re.IGNORECASE)


@dataclass
class Criterio:
    fluxograma: str
    cor: str
    tempo_alvo: str
    criterio: str
    descritor_parts: list[str] = field(default_factory=list)

    def to_record(self) -> dict:
        descritor = " ".join(part.strip() for part in self.descritor_parts if part.strip())
        return {
            "fluxograma": self.fluxograma,
            "cor": self.cor,
            "tempo_alvo": self.tempo_alvo,
            "criterio": self.criterio.strip(),
            # Per Tarefa 1: items without an explicit "Descritor:" line use
            # the criterion text itself as the descriptor.
            "descritor": descritor if descritor else self.criterio.strip(),
        }


def _cluster_lines(words: list[dict]) -> list[list[dict]]:
    """Group words into lines by proximity of their `top` coordinate."""
    lines: list[list[dict]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(lines[-1][0]["top"] - word["top"]) <= LINE_CLUSTER_TOLERANCE:
            lines[-1].append(word)
        else:
            lines.append([word])
    for line in lines:
        line.sort(key=lambda w: w["x0"])
    return lines


ITEM_NUMBER_PATTERN = re.compile(r"^(\d+)\s*[-–]")


def _colors_present(badge_words: list[dict]) -> list[str]:
    """Return the colors present on this page, in canonical order.

    The badge word's vertical position is NOT a reliable proxy for where its
    band starts: it renders roughly at the vertical *center* of the block of
    items it covers, not at the top edge, so using it as a top-boundary
    misattributes the first item(s) of every band to the previous color (or
    drops them if it's the page's very first band). We only use the badge
    words to know *which* colors exist on this page; the actual band
    boundaries are detected from item-numbering resets in
    `extract_fluxograma` instead.
    """
    found = {w["text"].upper() for w in badge_words}
    colors = [c for c in KNOWN_COLORS if c in found]
    return colors or list(KNOWN_COLORS)


def extract_fluxograma(page, titulo: str) -> list[Criterio]:
    # Drop the page-footer number: it sits isolated near the very bottom of
    # the page, well past the last real content line on every page checked.
    footer_cutoff = page.height * 0.85
    words = [w for w in page.extract_words() if w["top"] < footer_cutoff]
    badge_words = [w for w in words if w["x0"] < BADGE_COLUMN_MAX_X]
    content_words = [w for w in words if w["x0"] >= BADGE_COLUMN_MAX_X]

    colors = _colors_present(badge_words)
    content_lines = _cluster_lines(content_words)

    criterios: list[Criterio] = []
    current: Criterio | None = None
    band_index = 0
    seen_first_item = False

    for line_words in content_lines:
        text = " ".join(w["text"] for w in line_words)

        item_match = ITEM_START_PATTERN.match(text)
        descritor_match = DESCRITOR_PATTERN.match(text)

        if item_match:
            number_match = ITEM_NUMBER_PATTERN.match(text)
            item_number = int(number_match.group(1)) if number_match else None

            # Each color band restarts its item numbering at 1 (confirmed
            # across every fluxograma page read manually during development).
            # A "1" after we've already seen at least one item marks a new
            # band; the very first item on the page starts band 0 regardless
            # of its own number (some pages skip straight to a later color).
            if seen_first_item and item_number == 1 and band_index < len(colors) - 1:
                band_index += 1
            seen_first_item = True

            cor = colors[band_index]
            tempo_alvo = TEMPO_ALVO_BY_COLOR[cor]
            current = Criterio(fluxograma=titulo, cor=cor, tempo_alvo=tempo_alvo, criterio=item_match.group(1))
            criterios.append(current)
        elif descritor_match:
            if current is not None:
                current.descritor_parts.append(descritor_match.group(1))
        elif current is not None:
            # Continuation of either the criterion title (rare, long titles
            # wrap) or a multi-line "Descritor:" block.
            if current.descritor_parts:
                current.descritor_parts.append(text)
            else:
                current.criterio += " " + text

    return criterios


def main() -> None:
    if not PDF_PATH.exists():
        raise SystemExit(
            f"PDF não encontrado em {PDF_PATH}. Coloque o arquivo antes de rodar este script."
        )

    all_records: list[dict] = []
    with pdfplumber.open(PDF_PATH) as pdf:
        num_pages_expected = LAST_FLUXOGRAMA_PAGE - FIRST_FLUXOGRAMA_PAGE + 1
        if len(FLUXOGRAMA_TITULOS) != num_pages_expected:
            raise SystemExit(
                f"FLUXOGRAMA_TITULOS tem {len(FLUXOGRAMA_TITULOS)} itens, mas o intervalo de "
                f"páginas espera {num_pages_expected}. Ajuste antes de rodar."
            )

        for offset, titulo in enumerate(FLUXOGRAMA_TITULOS):
            page = pdf.pages[FIRST_FLUXOGRAMA_PAGE + offset]
            criterios = extract_fluxograma(page, titulo)
            all_records.extend(c.to_record() for c in criterios)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(all_records)} registros extraídos e salvos em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
