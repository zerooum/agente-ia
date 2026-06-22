from google.adk import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext

FATURAS = [
    {
        "fatura_id": "FAT-001",
        "cliente_id": "CLI-001",
        "assinatura_id": "ASS-001",
        "plano": "Pro",
        "descricao": "Assinatura Plano Pro - Junho/2026",
        "valor": 199.90,
        "vencimento": "2026-06-30",
        "status": "pendente",
        "assinatura_ativa": True,
    },
    {
        "fatura_id": "FAT-002",
        "cliente_id": "CLI-001",
        "assinatura_id": "ASS-001",
        "plano": "Pro",
        "descricao": "Assinatura Plano Pro - Maio/2026",
        "valor": 199.90,
        "vencimento": "2026-05-31",
        "status": "paga",
        "assinatura_ativa": True,
    },
    {
        "fatura_id": "FAT-003",
        "cliente_id": "CLI-002",
        "assinatura_id": "ASS-002",
        "plano": "Basic",
        "descricao": "Assinatura Plano Basic - Junho/2026",
        "valor": 79.90,
        "vencimento": "2026-06-15",
        "status": "atrasada",
        "assinatura_ativa": True,
    },
    {
        "fatura_id": "FAT-004",
        "cliente_id": "CLI-003",
        "assinatura_id": "ASS-003",
        "plano": "Enterprise",
        "descricao": "Assinatura Plano Enterprise - Junho/2026",
        "valor": 599.00,
        "vencimento": "2026-06-25",
        "status": "paga",
        "assinatura_ativa": True,
    },
    {
        "fatura_id": "FAT-005",
        "cliente_id": "CLI-002",
        "assinatura_id": "ASS-002",
        "plano": "Basic",
        "descricao": "Assinatura Plano Basic - Maio/2026",
        "valor": 79.90,
        "vencimento": "2026-05-15",
        "status": "paga",
        "assinatura_ativa": True,
    },
]

def listar_faturas(cliente_id: str):
    """Lista todas as faturas de um cliente pelo seu ID."""
    return {
        "faturas": [fatura for fatura in FATURAS if fatura["cliente_id"] == cliente_id]
    }
    # adk sempre converte para um dicionario {"result": [...]}
    # A boa pratica é sempre retornar um dicionario
    # docstring é importante para dar contexto

def cancelar_assinatura(cliente_id: str, tool_context: ToolContext):
    """Cancela a assinatura ativa de um cliente pelo seu ID.

    Marca a assinatura como inativa em todas as faturas relacionadas e
    informa qual assinatura foi cancelada.
    """

    if tool_context.tool_confirmation is None:
        tool_context.request_confirmation(
            hint="O valor da assinatura é alto. Tem certeza que deseja cancelar?"
        )
        return {"status": "aguardando confirmacao"}
   
    if not tool_context.tool_confirmation.confirmed:
        return {"status": "nao_cancelada", "mensagem": "Cancelamento não confirmado pelo usuário"}

    faturas_cliente = [
        fatura for fatura in FATURAS if fatura["cliente_id"] == cliente_id
    ]

    if not faturas_cliente:
        return {
            "sucesso": False,
            "mensagem": f"Nenhuma assinatura encontrada para o cliente {cliente_id}.",
        }

    ativas = [fatura for fatura in faturas_cliente if fatura["assinatura_ativa"]]
    if not ativas:
        return {
            "sucesso": False,
            "mensagem": f"A assinatura do cliente {cliente_id} já está cancelada.",
        }

    assinatura_id = ativas[0]["assinatura_id"]
    plano = ativas[0]["plano"]
    for fatura in ativas:
        fatura["assinatura_ativa"] = False

    return {
        "sucesso": True,
        "assinatura_id": assinatura_id,
        "plano": plano,
        "mensagem": (
            f"Assinatura {assinatura_id} (Plano {plano}) do cliente "
            f"{cliente_id} cancelada com sucesso."
        ),
    }

root_agent = Agent(
    name="operador_conta",
    instruction="""
        Você é um atendente de conta da Acme
        Você é responsável por:
            - Informar ao cliente sobre sua assinatura: o plano, status e renovação.
            - Tirar dúvidas sobre as faturas do cliente.
            - Cancelar a assinatura do cliente, se solicitado.
        O usuário precisa fornecer o ID do cleinte para que voce possa buscar as informações corretas.
        Seja cordial e direto.
    """,
    model="gemini-2.5-flash-lite",
    tools=[
        listar_faturas,
        cancelar_assinatura
        # FunctionTool(cancelar_assinatura, require_confirmation=True) 
        # o require_confirmation tb pode receber uma função que retorna um booleano
    ]
)
