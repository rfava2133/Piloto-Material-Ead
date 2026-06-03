# Etapa 1 — Extração de Material · UNIGRAN EAD

Piloto funcional da primeira etapa da esteira: recebe Word/PDF, extrai texto
(Markdown) e imagens, cria a estrutura de pastas.

## Instalação (uma vez)

```bash
# Dependências do sistema
brew install pandoc python

# Bibliotecas Python
pip install flask pyyaml pymupdf --break-system-packages
```

## Configuração

Edite `scripts/config.yml`:
- `raiz`: caminho da pasta do projeto no Google Drive
- `sheets.sheet_id`: deixe vazio por enquanto (modo piloto)

## Como usar — Interface visual (recomendado)

```bash
cd unigran-ead-esteira
python3 servidor.py
```

Abra http://127.0.0.1:5000 no navegador.

1. Preencha código (ex: ADM), nome da disciplina e número da aula
2. Arraste o Word e/ou PDF
3. Clique "Processar material"
4. Veja o resultado: Markdown gerado, imagens extraídas, pasta criada

## Como usar — Linha de comando (alternativa)

```bash
python3 scripts/01-processar-entrada.py \
    --codigo ADM \
    --disciplina "Fundamentos de Administração" \
    --aula 1 \
    --word /caminho/aula.docx \
    --pdf /caminho/aula.pdf
```

## O que acontece

```
Material (Word + PDF)
      ↓
Cria estrutura de pastas da aula (7 subpastas)
      ↓
Copia originais para 01_source/
      ↓
Pandoc: Word → 02_markdown/{ID}.md + imagens do Word → 04_imagens/antigas/
      ↓
PyMuPDF: imagens do PDF → 04_imagens/antigas/
      ↓
Registra _log.json
```

## Estrutura gerada

```
disciplinas/ADM-fundamentos-de-administracao/aula-01/
├── 01_source/          ADM-01.docx · ADM-01-original.pdf
├── 02_markdown/        ADM-01.md
├── 03_reformulado/     (vazio — próximas etapas)
├── 04_imagens/
│   ├── antigas/        word-*.png · pdf-*.png (extraídas)
│   └── prontas/        (vazio — etapa 4)
├── 05_output/          (vazio — etapa 5)
├── 06_revisao/         (vazio)
├── 07_incubadora/      (vazio)
└── _log.json           registro do processamento
```

## Arquivos do projeto

```
unigran-ead-esteira/
├── CLAUDE.md                      Instrução-mãe (Claude Code lê)
├── servidor.py                    Servidor local da interface
├── interface/
│   └── index.html                 Interface drag & drop
├── scripts/
│   ├── config.yml                 Configuração
│   ├── 01-processar-entrada.py    Orquestrador
│   └── lib/
│       ├── pastas.py              Criação de pastas + nomenclatura
│       ├── extrair_word.py        Pandoc wrapper
│       ├── extrair_pdf.py         PyMuPDF
│       └── logger.py              Log por aula
└── docs/
    ├── PROMPT_MESTRE.md           Contexto portátil para chats filhos
    └── INSTRUCOES_CHAT.md         Como organizar os chats
```

## Notas

- **Slug com "de":** a pasta fica `ADM-fundamentos-de-administracao`. Mantém
  literal e previsível. Se preferir sem stopwords, ajuste `lib/pastas.py`.
- **Filtro de imagens pequenas:** ícones < 100px são descartados (configurável
  em `config.yml`).
- **Versão final:** quando a planilha de cursos chegar, os campos viram combo
  com filtro. A lógica de pastas e extração não muda.
