from fpdf import FPDF
from datetime import datetime

class PDFReportGenerator(FPDF):
    def __init__(self, analyzer, cliente_data, sub_foco, row_foco):
        super().__init__()
        self.analyzer = analyzer
        self.cliente_data = cliente_data
        self.sub_foco = sub_foco
        self.row_foco = row_foco
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font("DejaVuSansCondensed", "", "DejaVuSansCondensed.ttf", uni=True)
        self.add_font("DejaVuSansCondensed", "B", "DejaVuSansCondensed-Bold.ttf", uni=True)
        self.set_font("DejaVuSansCondensed", size=12)

    def header(self):
        self.set_font("DejaVuSansCondensed", "B", 15)
        self.cell(0, 10, "Relatório Executivo de Inteligência de Mercado", 0, 1, "C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVuSansCondensed", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

    def chapter_title(self, title):
        self.set_font("DejaVuSansCondensed", "B", 14)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, "L", 1)
        self.ln(5)

    def chapter_body(self, body):
        self.set_font("DejaVuSansCondensed", "", 12)
        self.multi_cell(0, 8, body)
        self.ln()

    def add_summary(self):
        self.chapter_title("1. Sumário Executivo")
        self.chapter_body(f"Este relatório apresenta uma análise de inteligência de mercado para a empresa {self.cliente_data.get("empresa", "[Nome da Empresa]")}, focando na categoria {self.row_foco["Categoria Macro"]} e subcategoria {self.sub_foco}.\n\n")
        
        # Índice de Confiança
        confianca = self.analyzer.calcular_confianca(self.row_foco["Categoria Macro"], self.sub_foco)
        self.set_font("DejaVuSansCondensed", "B", 12)
        self.cell(0, 8, f"Índice de Confiança da Projeção: {confianca["score"]}% ({confianca["nivel"]})", 0, 1)
        self.set_font("DejaVuSansCondensed", "", 10)
        if confianca["motivos"]:
            for motivo in confianca["motivos"]:
                self.cell(0, 6, f"- {motivo}", 0, 1)
        self.ln(5)

    def add_market_opportunities(self):
        self.chapter_title("2. Matriz de Oportunidades")
        # Aqui você pode adicionar a lógica para listar as melhores categorias para investir
        # Por enquanto, um placeholder
        self.chapter_body("Detalhes das melhores categorias para investir serão incluídos aqui.")

    def add_growth_scenarios(self):
        self.chapter_title("3. Cenários de Crescimento")
        # Lógica para cenários de crescimento
        scenarios = self.analyzer.calcular_cenarios(self.row_foco["Categoria Macro"], self.sub_foco)
        
        self.set_font("DejaVuSansCondensed", "B", 12)
        self.cell(40, 10, "Cenário", 1)
        self.cell(40, 10, "Receita Projetada", 1)
        self.cell(40, 10, "Lucro Projetado", 1)
        self.cell(30, 10, "Crescimento", 1)
        self.ln()

        self.set_font("DejaVuSansCondensed", "", 10)
        for scenario in scenarios:
            self.cell(40, 8, scenario["Cenário"], 1)
            self.cell(40, 8, f"R$ {self.format_br(scenario["Receita Projetada 6M"])}", 1)
            self.cell(40, 8, f"R$ {self.format_br(scenario["Lucro Projetado 6M"])}", 1)
            self.cell(30, 8, f"{scenario["Crescimento (%)"]:.1f}%", 1)
            self.ln()
        self.ln(5)

    def add_demand_projection(self):
        self.chapter_title("4. Tendência e Projeção de Demanda")
        tendencia_res = self.analyzer.calcular_tendencia(self.row_foco["Categoria Macro"])
        
        self.set_font("DejaVuSansCondensed", "B", 12)
        self.cell(0, 8, f"Tendência Atual: {tendencia_res["tendencia"]} ({tendencia_res["crescimento_mensal"]:.1f}% mensal)", 0, 1)
        self.cell(0, 8, f"Projeção Total (3 Meses): R$ {self.format_br(tendencia_res["projecao_3m"])}", 0, 1)
        self.ln(2)

        self.set_font("DejaVuSansCondensed", "B", 12)
        self.cell(0, 8, "Projeção Mensal Detalhada:", 0, 1)
        self.set_font("DejaVuSansCondensed", "", 10)
        meses = ["Mês 1", "Mês 2", "Mês 3"]
        valores = tendencia_res.get("mensal", [0, 0, 0])
        
        # Calcular porcentagem de crescimento mensal
        faturamento_atual = self.analyzer.cliente_data.get("faturamento_3m", 0.0) / 3 # Faturamento mensal atual
        
        for i, val in enumerate(valores):
            if faturamento_atual > 0:
                crescimento_percentual = ((val - faturamento_atual) / faturamento_atual) * 100
            else:
                crescimento_percentual = 0.0 # Ou outro valor padrão se faturamento_atual for zero
            self.cell(0, 6, f"- {meses[i]}: R$ {self.format_br(val)} ({crescimento_percentual:.1f}%) ", 0, 1)
        self.ln(5)

    def add_action_plan(self):
        self.chapter_title("5. Plano de Ação Sugerido")
        # Lógica para o plano de ação
        plano_acao = self.analyzer.gerar_plano_acao(self.row_foco["Categoria Macro"], self.sub_foco)
        
        self.set_font("DejaVuSansCondensed", "B", 12)
        self.cell(0, 8, f"Prioridade: {plano_acao["prioridade"]} (Score: {plano_acao["score"]:.2f})", 0, 1)
        self.set_font("DejaVuSansCondensed", "", 10)
        self.multi_cell(0, 8, plano_acao["ajuste_estrategico"])
        self.ln(2)

        self.set_font("DejaVuSansCondensed", "B", 12)
        self.cell(0, 8, "Ações Detalhadas:", 0, 1)
        self.set_font("DejaVuSansCondensed", "", 10)
        for acao in plano_acao["acoes"]:
            self.multi_cell(0, 6, f"• {acao}")
        self.ln(5)

    def format_br(self, value):
        # Replicar a função format_br do app.py para o PDF
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M".replace(".", ",")
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K".replace(".", ",")
        else:
            return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def generate_report(self, filename="relatorio_executivo.pdf"):
        self.add_page()
        self.add_summary()
        self.add_market_opportunities()
        self.add_growth_scenarios()
        self.add_demand_projection()
        self.add_action_plan()
        self.output(filename)


# Para usar:
# from utils.pdf_generator import PDFReportGenerator
# pdf = PDFReportGenerator(analyzer, cliente_data, sub_foco, row_foco)
# pdf.generate_report("relatorio.pdf")
