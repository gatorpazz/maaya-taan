# Data sources and licenses

| File | Source | License | Use |
|---|---|---|---|
| raw/YUA_ES_communicative_contexts_corpus_v1.tsv, raw/contexts.tsv | https://github.com/alemol/yua-es-ccc (Molina-Villegas et al.) | CC-BY-4.0 | Attested phrases for lessons |
| raw/kaikki-yua.jsonl | https://kaikki.org/dictionary/Yucatec%20Maya/ (Wiktionary extract) | CC-BY-SA 3.0 | Lemma glosses |
| raw/inali_norma_maya.pdf | INALI 2014, *U nu'ukbesajil u ts'íibta'al maayat'aan* | INALI | Orthography reference |
| model facebook/mms-tts-yua | https://huggingface.co/facebook/mms-tts-yua | CC-BY-NC 4.0 | Maya voice (personal, non-commercial) |
| model facebook/mms-1b-all | https://huggingface.co/facebook/mms-1b-all | CC-BY-NC 4.0 | Maya ASR for checks |
| model hexgrad/Kokoro-82M | https://huggingface.co/hexgrad/Kokoro-82M | Apache-2.0 | English narrator |

## Standard phrases (`data/standard_phrases.tsv`)

Hand-curated greetings and courtesy formulas from published teaching materials that the YUA-ES-CCC corpus lacks.
`maya attest` reports them as level `standard`; lesson YAML cites them by `STDnnnn` id. Keep the spelling INALI 2014
even when the source uses the 1984 alphabet or a loose press spelling, and record the source's spelling in `note`.

| Key | Source | Kind |
|---|---|---|
| MAYMAY2010 | Ismael May May, *Kan maaya yéetel mejen tsikbalo'ob / Aprenda maya con breves diálogos*, 2nd ed., CEPHCIS-UNAM, Mérida 2010 (reprint 2013), ISBN 978-607-02-1548-3. https://www.cephcis.unam.mx/wp-content/uploads/2020/04/aprenda-maya.pdf | Native-speaker textbook (1984 alphabet) |
| NAATIK | Na'atik Language & Culture Institute (Felipe Carrillo Puerto), "Yucatec Maya Phrases". https://naatikmexico.org/blog/yucatec-maya-phrases | Language school phrase list; loose spelling |
| YUCTODAY2025 | Violeta H. Cantarell, "Say It in Maya", *Yucatán Today*, 2025-02-19. https://yucatantoday.com/en/say-it-in-maya | Magazine column; notes the time-of-day greetings are calques |
| PORESTO2023A | Redacción Por Esto!, "¿Cómo se dice hola en Yucatán?", 2023-07-27. https://www.poresto.com/yucatan/2023/7/27/como-se-dice-hola-en-yucatan.html | Press, uncredited |
| PORESTO2023B | Redacción Por Esto!, "¿Cómo se dice por favor y gracias en maya?", 2023-08-17. https://www.poresto.com/yucatan/2023/8/17/como-se-dice-por-favor-gracias-en-maya.html | Press, uncredited |
| UNOTV2022 | UnoTV, "Descubre frases básicas para aprender a hablar maya", 2022-02-25. https://www.unotv.com/estados/yucatan/lengua-maya-frases-basicas-para-hablarla/ | Press; encoding-damaged spellings |
| YUCATART2018 | yucat.art.blog, "10 palabras y frases en maya que debes conocer", 2018-11-19. https://yucat.art.blog/2018/11/19/primera-entrada-del-blog/ | Blog |
| LESSON02 | Author's choice for lesson 2 (2026-10-18), built on the corpus collocation *u chíinil k'iin* | Course decision |

Reliability, best first: MAYMAY2010 (native speaker, academic press), then NAATIK and YUCTODAY2025, then the press
pieces. Press sources agree with each other on the three standard greetings but none cites a linguist, and the
native-speaker textbook does not use them at all: its dialogues open with *Bix a beel* and close with *xi'ik tech utsil*
or *ka'akate'*. Treat the time-of-day greetings as the modern school register, not as village speech.
