from fpdf import FPDF
from datetime import datetime
import pandas as pd

class PDFReportGenerator(FPDF):
    def __init__(self, analyzer, cliente_data, cat_foco, sub_foco, row_foco):
        super().__init__()
        self.analyzer = analyzer
        self.cliente_data = cliente_data
        self.cat_foco = cat_foco
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
        # Usar self.cat_foco e self.sub_foco que são passados no construtor
        categoria_display = self.cat_foco if self.cat_foco else "N/A"
        subcategoria_display = self.sub_foco if self.sub_foco else "N/A"
        
        self.chapter_body(f"Este relatorio apresenta uma analise de inteligencia de mercado para a empresa {empresa}, focando na categoria {categoria_display} e subcategoria {subcategoria_display}.\n\n")
        
        # Índice de Confiança
        confianca = self.analyzer.calcular_confianca(self.cat_foco, self.sub_foco)
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
        
        # Gerar ranking completo para ter todos os dados de subcategorias
        df_ranking = self.analyzer.gerar_ranking()
        
        if df_ranking.empty:
            self.chapter_body("Nenhuma oportunidade de mercado encontrada.")
            return

        # Filtrar para as subcategorias de FOCO ou OK
        df_oportunidades = df_ranking[df_ranking['Status'].isin(['FOCO', 'OK'])].head(5)

        if df_oportunidades.empty:
            self.chapter_body("Nenhuma oportunidade de mercado relevante encontrada para as subcategorias analisadas.")
            return

        self.set_font("Helvetica", "B", 11)
        self.cell(60, 10, "Subcategoria", 1)
        self.cell(40, 10, "Faturamento 6M", 1)
        self.cell(30, 10, "Score", 1)
        self.cell(40, 10, "Status", 1)
        self.ln()
        
        self.set_font("Helvetica", "", 10)
        for _, row in df_oportunidades.iterrows():
            self.cell(60, 8, str(row['Subcategoria'])[:30], 1)
            self.cell(40, 8, f"R$ {self.format_br(row['Mercado (R$)'])}", 1)
            self.cell(30, 8, f"{row['Score']:.2f}", 1)
            self.cell(40, 8, row['Status'], 1)
            self.ln()
        self.ln(5)

    def add_growth_scenarios(self):
        self.chapter_title("3. Cenarios de Crescimento")
        # Usar self.cat_foco e self.sub_foco que são passados no construtor
        res_simulacao = self.analyzer.simular_cenarios(self.cat_foco, self.sub_foco)
        scenarios_df = res_simulacao.get("cenarios", pd.DataFrame())

        # Garantir que o dataframe de cenários não está vazio e contém os dados esperados
        if scenarios_df.empty or not all(col in scenarios_df.columns for col in ['Cenário', 'Receita Projetada 6M', 'Lucro Projetado 6M', 'Crescimento (%)']):
            self.chapter_body("Nao foi possivel calcular cenarios para esta subcategoria ou os dados estao incompletos.")
            return

        # Adicionar informações de ticket e margem para contexto
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        margem_cliente = self.cliente_data.get('margem', 0) * 100
        self.chapter_body(f"Análise de cenários para a subcategoria **{self.sub_foco}** (Categoria: **{self.cat_foco}**). Seu ticket médio: R$ {self.format_br(ticket_cliente)}, Margem: {margem_cliente:.1f}%.")
        self.ln(2)
        
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
            # Garantir que o crescimento percentual é formatado corretamente
            crescimento_pct = scenario["Crescimento (%)"]
            if pd.isna(crescimento_pct): crescimento_pct = 0.0
            self.cell(40, 8, f"{crescimento_pct:.1f}%", 1)
            self.ln()
        self.ln(5)

    def add_demand_projection(self):
        self.chapter_title("4. Tendencia e Projecao de Demanda")
        tendencia_res = self.analyzer.calcular_tendencia(self.cat_foco)
        
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, f"Tendencia Atual: {tendencia_res['tendencia']} ({tendencia_res['crescimento_mensal']:.1f}% mensal)", 0, 1)
        self.cell(0, 8, f"Projecao Total (3 Meses): R$ {self.format_br(tendencia_res['projecao_3m'])}", 0, 1)
        self.ln(2)

        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, "Projecao Mensal Detalhada:", 0, 1)
        self.set_font("Helvetica", "", 10)
        meses = ["Mes 1", "Mes 2", "Mes 3"]
        valores = tendencia_res.get("mensal", [0, 0, 0])
        
        # O faturamento base para o cálculo do crescimento mensal deve ser o faturamento médio mensal do cliente
        faturamento_mensal_cliente_base = self.cliente_data.get("faturamento_3m", 0.0) / 3

        for i, val in enumerate(valores):
            # O crescimento percentual deve ser em relação ao mês anterior projetado, ou ao faturamento base para o primeiro mês
            if i == 0:
                # Primeiro mês, comparar com o faturamento mensal base do cliente
                crescimento_percentual = ((val - faturamento_mensal_cliente_base) / faturamento_mensal_cliente_base * 100) if faturamento_mensal_cliente_base > 0 else 0
            else:
                # Meses subsequentes, comparar com o valor projetado do mês anterior
                crescimento_percentual = ((val - valores[i-1]) / valores[i-1] * 100) if valores[i-1] > 0 else 0
            self.cell(0, 6, f"- {meses[i]}: R$ {self.format_br(val)} ({crescimento_percentual:+.1f}%)", 0, 1)
        self.ln(5)

    def clean_text(self, text):
        """Remove caracteres não-latinos e emojis que causam erro no PDF padrão"""
        if not text: return ""
        # Substituir caracteres comuns que causam erro e acentos problemáticos
        replacements = {
            '✅': '[OK]', '🚀': '>', '⚠️': '!', '💡': 'i', '💰': '$', '🎯': '>', '•': '*', '·': '*',
            '—': '-', '–': '-', '“': '"', '”': '"', '‘': "'", '’': "'"
        }
        for char, rep in replacements.items():
            text = text.replace(char, rep)
        
        # Normalizar para evitar problemas de codificação mantendo acentos básicos
        try:
            return text.encode('latin-1', 'replace').decode('latin-1').replace('?', ' ')
        except:
            return "".join([c if ord(c) < 256 else ' ' for c in text])

    def add_action_plan(self):
        self.chapter_title("5. Plano de Acao Sugerido")
        # Usar self.cat_foco e self.sub_foco que são passados no construtor
        lista_plano = self.analyzer.gerar_plano_acao(self.cat_foco)
        # Filtrar para a subcategoria de foco
        plano_foco = next((p for p in lista_plano if p["Subcategoria"] == self.sub_foco), None)
        
        if not plano_foco:
            self.chapter_body("Nao ha recomendacoes especificas para esta subcategoria no momento.")
            return

        self.set_font("Helvetica", "B", 12)
        prioridade = self.clean_text(plano_foco['Prioridade'])
        self.cell(0, 8, f"Prioridade: {prioridade} (Score: {plano_foco['Score']:.2f})", 0, 1)
        self.ln(2)

        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, "Acoes Detalhadas:", 0, 1)
        self.set_font("Helvetica", "", 10)
        for acao in plano_foco.get("Ações", []):
            # Remover markdown bold e limpar caracteres especiais
            acao_limpa = acao.replace("**", "")
            acao_limpa = self.clean_text(acao_limpa)
            # Usar largura fixa para evitar erro de espaço horizontal
            self.multi_cell(180, 6, f"* {acao_limpa}", border=0, align='L')
        self.ln(5)

    def format_br(self, value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M".replace(".", ",")
        elif value >= 1_000:
            return f"{value / 1_000:,.1f}K".replace(".", "X").replace(",", ".").replace("X", ",")
        else:
            return f"{value:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")

    def generate_report(self, filename="relatorio_executivo.pdf"):
        self.add_page()
        self.alias_nb_pages()
        self.add_summary()
        self.add_market_opportunities()
        self.add_growth_scenarios()
        self.add_demand_projection()
        self.add_action_plan()
        self.output(filename)
