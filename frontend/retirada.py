"""Dados de retirada dos itens achados.

Para trocar os dados provisórios pelos reais, edite apenas o dicionário RETIRADA.
O link do Google Maps é gerado automaticamente a partir do endereço.
"""
from urllib.parse import quote_plus

RETIRADA = {
    "empresa": "Empresa Exemplo Ltda.",
    "setor": "Recepção, térreo - Sala 01",
    "endereco": "Av. Exemplo, 1000, Centro, Teresina - PI",
    "horario": "Segunda a sexta, das 8h às 17h",
    "orientacoes": "Leve um documento com foto. O CPF deve ser o mesmo do seu cadastro.",
}


def dados_da_retirada():
    """Devolve os dados de retirada já com o link do mapa."""
    dados = dict(RETIRADA)
    dados["mapa"] = (
        "https://www.google.com/maps/search/?api=1&query="
        + quote_plus(RETIRADA["endereco"])
    )
    return dados