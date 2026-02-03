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
        # Usando fontes padrão do sistema para evitar erros de arquivo ausente
        self.set_font("Helvetica", size=12)

    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 10, "Relatorio Executivo de Inteligencia de Mercado", 0, 1, "C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", 0, 0, "C")

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, "L", 1)
        self.ln(5)

    def chapter_body(self, body):
        self.set_font("Helvetica", "", 12)
        self.multi_cell(0, 8, body)
        self.ln()

    def add_summary(self):
        self.chapter_title("1. Sumario Executivo")
        empresa = self.cliente_data.get("empresa", "[Nome da Empresa]")
        categoria = self.row_foco.get("Categoria Macro", "N/A")
        subcategoria = self.sub_foco if self.sub_foco else "N/A"
        
        self.chapter_body(f"Este relatorio apresenta uma analise de inteligencia de mercado para a empresa {empresa}, focando na categoria {categoria} e subcategoria {subcategoria}.\n\n")
        
        # Índice de Confiança
        confianca = self.analyzer.calcular_confianca(categoria, subcategoria)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, f"Indice de Confianca da Projecao: {confianca['score']}% ({confianca['nivel']})", 0, 1)
        self.set_font("Helvetica", "", 10)
        if confianca["motivos"]:
            for motivo in confianca["motivos"]:
                self.cell(0, 6, f"- {motivo}", 0, 1)
        self.ln(5)

    def add_market_opportunities(self):
        self.chapter_title("2. Matriz de Oportunidades")
        self.chapter_body("Analise das melhores categorias para investimento baseada no potencial de mercado e competitividade de preco.")
        
        # Listar top categorias
        if hasattr(self.analyzer, 'mercado_categoria') and self.analyzer.mercado_categoria:
            self.set_font("Helvetica", "B", 11)
            self.cell(80, 10, "Categoria", 1)
            self.cell(50, 10, "Faturamento 6M", 1)
            self.cell(40, 10, "Oportunidade", 1)
            self.ln()
            
            self.set_font("Helvetica", "", 10)
            
            # Lógica segura para extrair dados de categoria (pode ser dict ou list de dicts)
            cats_data = []
            if isinstance(self.analyzer.mercado_categoria, dict):
                for cat, data in self.analyzer.mercado_categoria.items():
                    faturamento = data.get('faturamento', 0) if isinstance(data, dict) else 0
                    cats_data.append({'nome': cat, 'faturamento': faturamento})
            elif isinstance(self.analyzer.mercado_categoria, list):
                for item in self.analyzer.mercado_categoria:
                    if isinstance(item, dict):
                        nome = item.get('categoria', 'N/A')
                        faturamento = item.get('faturamento', 0)
                        cats_data.append({'nome': nome, 'faturamento': faturamento})

            # Ordenar e exibir top 5
            sorted_cats = sorted(cats_data, key=lambda x: x['faturamento'], reverse=True)[:5]
            for item in sorted_cats:
                self.cell(80, 8, str(item['nome'])[:40], 1)
                self.cell(50, 8, f"R$ {self.format_br(item['faturamento'])}", 1)
                self.cell(40, 8, "Alta" if item['faturamento'] > 1000000 else "Media", 1)
                self.ln()
        self.ln(5)

    def add_growth_scenarios(self):
        self.chapter_title("3. Cenarios de Crescimento")
        categoria = self.row_foco.get("Categoria Macro", "")
        subcategoria = self.sub_foco if self.sub_foco else ""
        
        # O método correto no MarketAnalyzer é simular_cenarios
        res_simulacao = self.analyzer.simular_cenarios(categoria, subcategoria)
        scenarios_df = res_simulacao.get('cenarios', pd.DataFrame())
        
        if scenarios_df.empty:
            self.chapter_body("Nao foi possivel calcular cenarios para esta subcategoria.")
            return

        self.set_font("Helvetica", "B", 11)
        self.cell(40, 10, "Cenario", 1)
        self.cell(50, 10, "Receita Projetada", 1)
        self.cell(50, 10, "Lucro Projetado", 1)
        self.cell(40, 10, "Crescimento", 1)
        self.ln()

        self.set_font("Helvetica", "", 10)
        for _, scenario in scenarios_df.iterrows():
            self.cell(40, 8, str(scenario["Cenário"]), 1)
            self.cell(50, 8, f"R$ {self.format_br(scenario['Receita Projetada 6M'])}", 1)
            self.cell(50, 8, f"R$ {self.format_br(scenario['Lucro Projetado 6M'])}", 1)
            self.cell(40, 8, f"{scenario['Crescimento (%)']:.1f}%", 1)
            self.ln()
        self.ln(5)

    def add_demand_projection(self):
        self.chapter_title("4. Tendencia e Projecao de Demanda")
        categoria = self.row_foco.get("Categoria Macro", "")
        tendencia_res = self.analyzer.calcular_tendencia(categoria)
        
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, f"Tendencia Atual: {tendencia_res['tendencia']} ({tendencia_res['crescimento_mensal']:.1f}% mensal)", 0, 1)
        self.cell(0, 8, f"Projecao Total (3 Meses): R$ {self.format_br(tendencia_res['projecao_3m'])}", 0, 1)
        self.ln(2)

        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, "Projecao Mensal Detalhada:", 0, 1)
        self.set_font("Helvetica", "", 10)
        meses = ["Mes 1", "Mes 2", "Mes 3"]
        valores = tendencia_res.get("mensal", [0, 0, 0])
        
        faturamento_atual = self.analyzer.cliente_data.get("faturamento_3m", 0.0) / 3
        
        for i, val in enumerate(valores):
            crescimento_percentual = ((val - faturamento_atual) / faturamento_atual * 100) if faturamento_atual > 0 else 0
            self.cell(0, 6, f"- {meses[i]}: R$ {self.format_br(val)} ({crescimento_percentual:+.1f}%)", 0, 1)
        self.ln(5)

    def add_action_plan(self):
        self.chapter_title("5. Plano de Acao Sugerido")
        categoria = self.row_foco.get("Categoria Macro", "")
        subcategoria = self.sub_foco if self.sub_foco else ""
        
        lista_plano = self.analyzer.gerar_plano_acao(categoria)
        # Filtrar para a subcategoria de foco
        plano_foco = next((p for p in lista_plano if p['Subcategoria'] == subcategoria), None)
        
        if not plano_foco:
            self.chapter_body("Nao ha recomendacoes especificas para esta subcategoria no momento.")
            return

        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, f"Prioridade: {plano_foco['Prioridade']} (Score: {plano_foco['Score']:.2f})", 0, 1)
        self.ln(2)

        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, "Acoes Detalhadas:", 0, 1)
        self.set_font("Helvetica", "", 10)
        for acao in plano_foco.get("Ações", []):
            # Remover markdown bold para o PDF
            acao_limpa = acao.replace("**", "")
            self.multi_cell(0, 6, f"* {acao_limpa}")
        self.ln(5)

    def format_br(self, value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M".replace(".", ",")
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K".replace(".", ",")
        else:
            return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def generate_report(self, filename="relatorio_executivo.pdf"):
        self.add_page()
        self.alias_nb_pages()
        self.add_summary()
        self.add_market_opportunities()
        self.add_growth_scenarios()
        self.add_demand_projection()
        self.add_action_plan()
        self.output(filename)
