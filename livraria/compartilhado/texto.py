import unicodedata


def normalizar(texto):
    """Minúsculas e sem acentos, para comparar textos digitados pelo usuário."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto)).casefold() if not unicodedata.combining(c))


def reais(centavos):
    return f"R$ {centavos / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def nota_media(media):
    return "sem avaliações" if media is None else f"{media:.1f}".replace(".", ",")
