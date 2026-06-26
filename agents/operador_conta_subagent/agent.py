from google.adk import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.agent_tool import AgentTool

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

def consultar_assinatura(cliente_id: str):
    """Consulta a assinatura de um cliente pelo seu ID.
    Retorna o plano, status (ativa/cancelada) e a próxima renovação.
    """
    faturas_cliente = [
        fatura for fatura in FATURAS if fatura["cliente_id"] == cliente_id
    ]

    if not faturas_cliente:
        return {
            "sucesso": False,
            "mensagem": f"Nenhuma assinatura encontrada para o cliente {cliente_id}.",
        }

    assinatura = faturas_cliente[0]
    ativa = any(fatura["assinatura_ativa"] for fatura in faturas_cliente)
    proxima_renovacao = max(fatura["vencimento"] for fatura in faturas_cliente)

    return {
        "sucesso": True,
        "assinatura_id": assinatura["assinatura_id"],
        "plano": assinatura["plano"],
        "status": "ativa" if ativa else "cancelada",
        "proxima_renovacao": proxima_renovacao,
    }

consultor_assinatura_subagent = Agent(
    name="consultor_assinatura",
    instruction="""
        Você é um consultor de assinaturas
        Você é responsável por:
            - Informar o plano, status e renovação da assinatura de um cliente.
            - Cancelar a assinatura ativa de um cliente, se solicitado.
    """,
    mode="task",
    model="gemini-3.1-flash-lite",
    tools=[
        consultar_assinatura,
        cancelar_assinatura
    ],
    disallow_transfer_to_peers=True
)

consultor_fatura_subagent = Agent(
    name="consultor_faturas",
    description="Especialista em faturas, responsavel por listar as faturas de um cliente especifico",
    instruction="""
        Você é um consultor de faturas
        Você é responsável por:
            - Listar as faturas de um cliente específico.
    """,
    # mode="single_turn", # Transparente na sessão, retorna pro chamador
    mode="task", # Transparente na sessão
    model="gemini-3.1-flash-lite",
    tools=[
        listar_faturas
    ],
    disallow_transfer_to_peers=True
)

# agente coordenador
root_agent = Agent(
    name="operador_conta",
    description="Coordenador responsável por ajudar o cliente a gerenciar a conta, incluindo faturas e assinaturas",
    instruction="""
        Você é um atendente de conta da Acme
        Você é responsável por:
        O usuário precisa fornecer o ID do cleinte para que voce possa buscar as informações corretas.
        Seja cordial e direto.
    """,
    model="gemini-3.1-flash-lite",
    sub_agents=[
        consultor_fatura_subagent,
        consultor_assinatura_subagent
    ],
    # tools=[AgentTool(consultor_fatura_subagent)]
)
