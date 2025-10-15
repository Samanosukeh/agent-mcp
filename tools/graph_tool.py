import matplotlib.pyplot as plt
from typing import Dict, Any
import os
import uuid


class GraphTool:
    name = "graph"
    description = (
        "Gera gráficos (pizza, linear, barra) dados os dados, labels e eixos. "
        "Retorna caminho da imagem PNG armazenada temporariamente."
    )

    def _normalize_tipo(self, tipo):
        if not isinstance(tipo, str):
            return "pizza"
        tipo = tipo.strip().lower()
        if tipo in ["pizza", "pie", "setores"]:
            return "pizza"
        if tipo in ["barra", "bar", "coluna"]:
            return "barra"
        if tipo in ["linear", "linha", "linhas", "line"]:
            return "linear"
        return tipo

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        tipo_raw = input.get("tipo", input.get("type", "pizza"))
        tipo = self._normalize_tipo(tipo_raw)
        dados = (
            input.get("dados")
            or input.get("data")
            or input.get("valores")
        )
        if not dados or not isinstance(dados, list) or not all(isinstance(v, (int, float)) for v in dados):
            return {
                "error": (
                    "Por favor, forneça uma lista de valores numéricos em 'dados', 'data' ou 'valores'\n"
                    "para gerar o gráfico."
                )
            }
        labels = (
            input.get("labels")
            or input.get("label")
            or input.get("rótulos")
            or input.get("rotulos")
            or [str(i) for i in range(len(dados))]
        )
        eixo_x = input.get("eixo_x", input.get("xlabel", "Eixo X"))
        eixo_y = input.get("eixo_y", input.get("ylabel", "Eixo Y"))
        titulo = input.get("titulo", input.get("title", "Gráfico Gerado"))

        if len(labels) < len(dados):
            labels = list(labels) + [f"Item {i+1}" for i in range(len(labels), len(dados))]
        elif len(labels) > len(dados):
            labels = labels[:len(dados)]

        try:
            # Garante diretório temporário próprio, nunca apaga
            base_tmp = os.path.join(os.getcwd(), "tmp_graphs")
            os.makedirs(base_tmp, exist_ok=True)
            unique_id = str(uuid.uuid4())[:8]
            img_path = os.path.join(base_tmp, f"graph_{unique_id}.png")
            fig, ax = plt.subplots()
            if tipo == "pizza":
                ax.pie(dados, labels=labels, autopct="%1.1f%%")
                ax.set_title(titulo)
            elif tipo == "barra":
                ax.bar(labels, dados)
                ax.set_xlabel(eixo_x)
                ax.set_ylabel(eixo_y)
                ax.set_title(titulo)
            elif tipo == "linear":
                ax.plot(labels, dados, marker='o')
                ax.set_xlabel(eixo_x)
                ax.set_ylabel(eixo_y)
                ax.set_title(titulo)
            else:
                plt.close(fig)
                return {
                    "error": (
                        f"Tipo de gráfico '{tipo_raw}' não suportado. "
                        "Use pizza, barra ou linear."
                    )
                }
            plt.tight_layout()
            fig.savefig(img_path)
            plt.close(fig)
            return {
                "figure_path": img_path,
                "mensagem": f"Gráfico gerado em {img_path}"
            }
        except Exception as e:
            return {
                "error": f"Ocorreu um problema ao gerar o gráfico: {str(e)}"
            }
