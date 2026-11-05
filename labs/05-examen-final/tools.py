
"""Tools: funciones del programa que el LLM puede pedir ejecutar.

Una tool tiene dos partes:
  - La DEFINICIÓN: nombre, descripción y JSON Schema de los argumentos.
  - La IMPLEMENTACIÓN: código normal que se ejecuta dentro del programa.

Las tools locales viven en este proceso. Las tools de un servidor MCP
y la búsqueda RAG se convierten en este mismo tipo Tool.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from llm_client import ToolDefinition


class ToolExecutionError(Exception):
    """Error previsto durante la ejecución de una herramienta."""


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    run: Callable[[dict[str, Any]], Awaitable[str]]
    read_only: bool
    origin: str

    def definition(self) -> ToolDefinition:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


def local_tool(
    function: Callable[..., Any],
    description: str,
    parameters: dict[str, Any],
    *,
    read_only: bool = True,
) -> Tool:
    """Convierte una función de Python en una herramienta del agente."""

    async def run(arguments: dict[str, Any]) -> str:
        return json.dumps(function(**arguments), ensure_ascii=False)

    return Tool(
        name=function.__name__,
        description=description,
        parameters=parameters,
        run=run,
        read_only=read_only,
        origin="local",
    )


# --- Implementaciones -------------------------------------------------------------------------

DIAS_SEMANA = [
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
]

PESOS = {
    "parcial_1": 0.20,
    "parcial_2": 0.20,
    "laboratorios": 0.35,
    "proyecto": 0.25,
}

NOTA_MINIMA = 3.0


def fecha_actual() -> dict[str, str]:
    today = date.today()
    return {
        "fecha": today.isoformat(),
        "dia_semana": DIAS_SEMANA[today.weekday()],
    }


def dias_hasta(fecha: str) -> dict[str, Any]:
    try:
        objetivo = date.fromisoformat(fecha)
    except ValueError as exc:
        raise ValueError(
            f"fecha debe tener el formato AAAA-MM-DD (recibido: {fecha!r})"
        ) from exc

    hoy = date.today()

    return {
        "hoy": hoy.isoformat(),
        "fecha": objetivo.isoformat(),
        "dias": (objetivo - hoy).days,
    }


def calcular_nota_final(
    parcial_1: float,
    parcial_2: float,
    laboratorios: float,
    proyecto: float,
) -> dict[str, Any]:

    notas = {
        "parcial_1": parcial_1,
        "parcial_2": parcial_2,
        "laboratorios": laboratorios,
        "proyecto": proyecto,
    }

    for nombre, nota in notas.items():
        if not 0.0 <= nota <= 5.0:
            raise ValueError(
                f"{nombre} debe estar entre 0.0 y 5.0 (recibido: {nota})"
            )

    final = sum(
        nota * PESOS[nombre]
        for nombre, nota in notas.items()
    )

    return {
        "nota_final": round(final, 2),
        "aprueba": final >= NOTA_MINIMA,
        "pesos": PESOS,
    }


def calcular_nota_necesaria(
    parcial_1: float,
    laboratorios: float,
    proyecto: float,
    nota_objetivo: float = NOTA_MINIMA,
) -> dict[str, Any]:
    """Calcula la nota necesaria en el segundo parcial para alcanzar un objetivo."""

    notas = {
        "parcial_1": parcial_1,
        "laboratorios": laboratorios,
        "proyecto": proyecto,
        "nota_objetivo": nota_objetivo,
    }

    for nombre, nota in notas.items():
        if not 0.0 <= nota <= 5.0:
            raise ValueError(
                f"{nombre} debe estar entre 0.0 y 5.0 (recibido: {nota})"
            )

    aporte_actual = (
        parcial_1 * PESOS["parcial_1"]
        + laboratorios * PESOS["laboratorios"]
        + proyecto * PESOS["proyecto"]
    )

    necesaria = (
        nota_objetivo - aporte_actual
    ) / PESOS["parcial_2"]

    if necesaria > 5.0:
        return {
            "posible": False,
            "mensaje": "No es posible alcanzar la nota objetivo con una nota máxima de 5.0 en el segundo parcial.",
            "nota_necesaria": round(necesaria, 2),
            "nota_maxima_segundo_parcial": 5.0,
        }

    if necesaria <= 0.0:
        return {
            "posible": True,
            "nota_necesaria": 0.0,
            "mensaje": "Ya alcanzas la nota objetivo incluso si obtienes 0.0 en el segundo parcial.",
        }

    return {
        "posible": True,
        "nota_necesaria": round(necesaria, 2),
        "mensaje": "Esta es la nota mínima necesaria en el segundo parcial.",
        "nota_objetivo": nota_objetivo,
    }


# --- Definiciones de herramientas -------------------------------------------------------------

LOCAL_TOOLS = [
    local_tool(
        fecha_actual,
        description="Devuelve la fecha de hoy y el día de la semana. Úsala cuando la respuesta dependa de la fecha actual.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),

    local_tool(
        dias_hasta,
        description="Calcula cuántos días faltan desde hoy hasta una fecha indicada.",
        parameters={
            "type": "object",
            "properties": {
                "fecha": {
                    "type": "string",
                    "description": "Fecha en formato AAAA-MM-DD",
                }
            },
            "required": ["fecha"],
        },
    ),

    local_tool(
        calcular_nota_final,
        description="Calcula la nota final del curso con los pesos oficiales. Requiere las notas de ambos parciales, laboratorios y proyecto.",
        parameters={
            "type": "object",
            "properties": {
                "parcial_1": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                },
                "parcial_2": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                },
                "laboratorios": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                },
                "proyecto": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                },
            },
            "required": [
                "parcial_1",
                "parcial_2",
                "laboratorios",
                "proyecto",
            ],
        },
    ),

    local_tool(
        calcular_nota_necesaria,
        description="Calcula la nota mínima necesaria en el segundo parcial para alcanzar una nota final objetivo. Requiere la nota del primer parcial, el promedio de laboratorios y la nota del proyecto. Si el estudiante no indica objetivo, utiliza 3.0.",
        parameters={
            "type": "object",
            "properties": {
                "parcial_1": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                },
                "laboratorios": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                },
                "proyecto": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                },
                "nota_objetivo": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                    "description": "Nota final que desea alcanzar. Por defecto es 3.0.",
                },
            },
            "required": [
                "parcial_1",
                "laboratorios",
                "proyecto",
            ],
        },
    ),
]


async def _demo() -> None:
    print("Definiciones que recibe el LLM:\n")

    print(
        json.dumps(
            [tool.definition() for tool in LOCAL_TOOLS],
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\nEjecución directa, sin LLM:")

    tools = {
        tool.name: tool
        for tool in LOCAL_TOOLS
    }

    print(
        "fecha_actual →",
        await tools["fecha_actual"].run({}),
    )

    print(
        "dias_hasta →",
        await tools["dias_hasta"].run({
            "fecha": "2026-12-03"
        }),
    )

    notas = {
        "parcial_1": 3.5,
        "parcial_2": 4.0,
        "laboratorios": 4.2,
        "proyecto": 3.8,
    }

    print(
        "calcular_nota_final →",
        await tools["calcular_nota_final"].run(notas),
    )

    datos_necesarios = {
        "parcial_1": 3.5,
        "laboratorios": 4.2,
        "proyecto": 3.8,
    }

    print(
        "calcular_nota_necesaria →",
        await tools["calcular_nota_necesaria"].run(datos_necesarios),
    )


if __name__ == "__main__":
    asyncio.run(_demo())
