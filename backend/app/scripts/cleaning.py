"""Regras de limpeza dos CSVs, aplicadas pelo seed.

São funções puras (texto entra, texto sai) para ficarem fáceis de testar.
"""

import re

# ---------------------------------------------------------------------------
# Aspas duplicadas
# ---------------------------------------------------------------------------


def _has_lone_quote(text: str) -> bool:
    """Há alguma aspa que não faz parte de um par ``""``?"""

    return '"' in text.replace('""', "")


def unwrap_double_quoted(value: str | None) -> str | None:
    """Desfaz a dupla serialização CSV de títulos e sinopses.

    ``"Um filme ""cult"" dos anos 80"`` -> ``Um filme "cult" dos anos 80``.
    Nos textos truncados a aspa final some: ``"Dos criadores de ""Fulano""``.
    Só desfaz quando todas as aspas restantes estão em pares, para não
    estragar citações legítimas como ``"Plus Ultra" is the motto of...``.
    """

    if not value or not value.startswith('"'):
        return value
    body = value[1:]
    if body.endswith('"') and not _has_lone_quote(body[:-1]):
        body = body[:-1]
    if _has_lone_quote(body):
        return value
    return body.replace('""', '"')


# ---------------------------------------------------------------------------
# Numerais romanos
# ---------------------------------------------------------------------------

# "Vi" e "Xi" ficam de fora: são palavras/nomes reais ("Vi" = "nós" em norueguês).
_ROMAN_TITLE_CASE = re.compile(r"\b(Ii|Iii|Iv|Vii|Viii|Ix|Xii|Xiii|Xiv)\b")


def fix_roman_numerals(title: str) -> str:
    """``Frozen Ii`` -> ``Frozen II``."""

    return _ROMAN_TITLE_CASE.sub(lambda match: match.group(1).upper(), title)


# ---------------------------------------------------------------------------
# "Pessoas" que não são pessoas
# ---------------------------------------------------------------------------


def _terms(text: str) -> set[str]:
    return {term.strip() for term in text.split(",") if term.strip()}


# As colunas de equipe dos CSVs vieram com outros campos do TMDB misturados.
GENRES = _terms("""
    action, adventure, animation, biography, comedy, crime, documentary, drama, family,
    fantasy, history, horror, music, musical, mystery, romance, science fiction, sci-fi,
    sport, thriller, tv movie, war, western
""")

KEYWORDS = _terms("""
    short film, stand-up comedy, lgbt, woman director, concert, anime, based on novel or book,
    based on true story, duringcreditsstinger, aftercreditsstinger, live action, remake,
    sequel, sports, superhero, christmas, mockumentary, based on manga, based on comic,
    based on play or musical, love, holiday, anthology
""")

LANGUAGES = _terms("""
    afrikaans, albanian, amharic, arabic, armenian, azerbaijani, basque, belarusian, bengali,
    bosnian, bulgarian, burmese, cantonese, catalan, chinese, croatian, czech, danish, dutch,
    english, esperanto, estonian, filipino, finnish, french, galician, georgian, german, greek,
    gujarati, hebrew, hindi, hungarian, icelandic, indonesian, irish, italian, japanese,
    kannada, kazakh, khmer, korean, kurdish, lao, latin, latvian, lithuanian, macedonian,
    malay, malayalam, maltese, mandarin, marathi, mongolian, nepali, no language, norwegian,
    pashto, persian, polish, portuguese, punjabi, romanian, russian, serbian, sinhalese,
    slovak, slovenian, somali, spanish, swahili, swedish, tagalog, tamil, telugu, thai,
    tibetan, turkish, ukrainian, urdu, uzbek, vietnamese, welsh, yiddish, zulu
""")

COUNTRIES = _terms("""
    afghanistan, albania, algeria, argentina, armenia, australia, austria, azerbaijan,
    bangladesh, belarus, belgium, bolivia, bosnia and herzegovina, brazil, bulgaria, cambodia,
    cameroon, canada, chile, china, colombia, costa rica, croatia, cuba, cyprus,
    czech republic, czechia, denmark, dominican republic, ecuador, egypt, estonia, ethiopia,
    finland, france, germany, ghana, greece, guatemala, hong kong, hungary, iceland, india,
    indonesia, iran, iraq, ireland, israel, italy, jamaica, japan, jordan, kazakhstan, kenya,
    kosovo, kuwait, latvia, lebanon, lithuania, luxembourg, malaysia, malta, mexico, moldova,
    mongolia, montenegro, morocco, nepal, netherlands, new zealand, nigeria, north macedonia,
    norway, pakistan, palestinian territory, panama, paraguay, peru, philippines, poland,
    portugal, puerto rico, qatar, romania, russia, saudi arabia, senegal, serbia, singapore,
    slovakia, slovenia, south africa, south korea, spain, sri lanka, sweden, switzerland,
    syria, taiwan, thailand, tunisia, turkey, ukraine, united arab emirates, united kingdom,
    united states of america, uruguay, venezuela, vietnam
""")

NOT_PEOPLE = GENRES | KEYWORDS | LANGUAGES | COUNTRIES

_ONLY_NUMBERS = re.compile(r"[\d\s.,:%+-]+")


def is_not_a_person(name: str) -> bool:
    """O "nome" é, na verdade, idioma, país, gênero, palavra-chave ou número?

    A lista é explícita de propósito: diretores com nome único (ex.: Sukumar)
    são pessoas reais e não podem ser removidos por heurística.
    """

    cleaned = name.strip()
    if not cleaned or _ONLY_NUMBERS.fullmatch(cleaned):
        return True
    return cleaned.casefold() in NOT_PEOPLE


# ---------------------------------------------------------------------------
# Limpeza por tabela
# ---------------------------------------------------------------------------


def clean_movie(row: dict[str, str | None]) -> dict[str, str | None]:
    titulo = unwrap_double_quoted(row["titulo"])
    return {
        **row,
        "titulo": fix_roman_numerals(titulo) if titulo else titulo,
        "sinopse": unwrap_double_quoted(row["sinopse"]),
        # Duração 0 significa "desconhecida" nos CSVs.
        "duracao_minutos": None if row["duracao_minutos"] == "0" else row["duracao_minutos"],
    }
