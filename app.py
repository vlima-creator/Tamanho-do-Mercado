#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Streamlit - Análise de Mercado Marketplace
Dashboard interativo para análise estratégica de categorias e subcategorias em marketplaces
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Adicionar pasta utils ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.market_analyzer import MarketAnalyzer
from utils.visualizations import (
    criar_grafico_evolucao_categoria,
    criar_grafico_ticket_medio,
    criar_grafico_ranking_subcategorias,
    criar_grafico_mercado_subcategorias,
    criar_grafico_cenarios,
    criar_grafico_crescimento,
    criar_gauge_score,
    criar_comparacao_tickets
)

# Configuração da página
st.set_page_config(
    page_title="Análise de Mercado Marketplace",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2ca02c;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .status-foco {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        font-weight: bold;
        text-align: center;
    }
    .status-ok {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        font-weight: bold;
        text-align: center;
    }
    .status-evitar {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        font-weight: bold;
        text-align: center;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MarketAnalyzer()
if 'dados_salvos' not in st.session_state:
    st.session_state.dados_salvos = False
if 'step' not in st.session_state:
    st.session_state.step = 1

# Função para avançar steps
def avancar_step():
    st.session_state.step += 1

def voltar_step():
    st.session_state.step = max(1, st.session_state.step - 1)

# Header
st.markdown('<div class="main-header">📊 Análise de Mercado Marketplace</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Navegação
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=Marketplace+Analytics", use_container_width=True)
    st.markdown("### 🧭 Navegação")
    
    menu = st.radio(
        "Escolha a seção:",
        ["🏠 Início", "👤 Dados do Cliente", "📈 Mercado Categoria", "🎯 Mercado Subcategorias", 
         "📊 Dashboard Executivo", "ℹ️ Sobre"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 📋 Status")
    
    if st.session_state.analyzer.cliente_data:
        st.success("✅ Dados do Cliente")
    else:
        st.warning("⏳ Dados do Cliente")
    
    if st.session_state.analyzer.mercado_categoria:
        st.success(f"✅ Mercado Categoria ({len(st.session_state.analyzer.mercado_categoria)} períodos)")
    else:
        st.warning("⏳ Mercado Categoria")
    
    if st.session_state.analyzer.mercado_subcategorias:
        st.success(f"✅ Subcategorias ({len(st.session_state.analyzer.mercado_subcategorias)})")
    else:
        st.warning("⏳ Subcategorias")
    
    st.markdown("---")
    
    if st.button("🗑️ Limpar Todos os Dados", use_container_width=True):
        st.session_state.analyzer.clear_data()
        st.session_state.dados_salvos = False
        st.rerun()

# ====================
# SEÇÃO: INÍCIO
# ====================
if menu == "🏠 Início":
    st.markdown("## 🎯 Bem-vindo à Ferramenta de Análise Estratégica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📖 O que é esta ferramenta?
        
        Esta aplicação ajuda você a tomar decisões estratégicas sobre **em qual categoria/subcategoria focar**
        em marketplaces, baseado em:
        
        - ✅ **Tamanho de mercado** (volume de faturamento)
        - ✅ **Fit de ticket** (alinhamento de preço cliente vs mercado)
        - ✅ **Potencial de crescimento** (simulação de cenários)
        - ✅ **Análise de lucratividade** (projeção de lucro)
        
        ### 🚀 Como usar?
        
        1. **👤 Preencha os dados do cliente** (empresa, ticket, margem, faturamento)
        2. **📈 Adicione dados de mercado da categoria** (evolução temporal - opcional)
        3. **🎯 Informe subcategorias** (faturamento e unidades dos últimos 6 meses)
        4. **📊 Visualize o dashboard** com ranking automático e cenários
        """)
    
    with col2:
        st.info("""
        ### 💡 Exemplo Prático
        
        **Cliente:** Tamoyo (Ferramentas)  
        **Ticket médio:** R$ 204,34  
        **Margem:** 15%
        
        **Análise identificou:**
        - 🎯 **Ferramentas Elétricas** - Mercado R$ 3,7 bi - **FOCO**
        - ⚠️ Ferramentas Manuais - Ticket muito baixo - **EVITAR**
        - ⚠️ Acessórios - Ticket muito baixo - **EVITAR**
        
        **Cenário Provável (0,5% share):**
        - Receita 6M: **R$ 18,6 milhões**
        - Crescimento: **278x** vs atual
        - Lucro adicional: **R$ 27.975**
        """)
        
        st.success("""
        ### ✨ Diferenciais
        
        - 🤖 **Cálculos automáticos** de score e ranking
        - 📊 **Visualizações interativas** com Plotly
        - 🎯 **Recomendações claras** (FOCO/OK/EVITAR)
        - 💰 **Simulação de 3 cenários** (conservador, provável, otimista)
        - 📈 **Dashboard executivo** pronto para apresentação
        """)
    
    st.markdown("---")
    st.markdown("### 🎬 Comece agora!")
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("▶️ Iniciar Análise", use_container_width=True, type="primary"):
            st.session_state.step = 2
            st.rerun()

# ====================
# SEÇÃO: DADOS DO CLIENTE
# ====================
elif menu == "👤 Dados do Cliente":
    st.markdown("## 👤 Dados do Cliente")
    st.markdown("Preencha as informações básicas do cliente. Os campos marcados com * são obrigatórios.")
    
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        
        with col1:
            empresa = st.text_input("* Nome da Empresa", value=st.session_state.analyzer.cliente_data.get('empresa', ''))
            categoria = st.text_input("* Categoria Macro", value=st.session_state.analyzer.cliente_data.get('categoria', ''))
            ticket_medio = st.number_input("Ticket Médio do Cliente (R$)", min_value=0.0, 
                                          value=float(st.session_state.analyzer.cliente_data.get('ticket_medio', 0.0)),
                                          help="Deixe em 0 para calcular automaticamente baseado em faturamento/unidades")
            margem = st.number_input("* Margem Atual (%)", min_value=0.0, max_value=100.0, 
                                    value=float(st.session_state.analyzer.cliente_data.get('margem', 0.0) * 100),
                                    step=0.1)
        
        with col2:
            faturamento_3m = st.number_input("* Faturamento Médio (últimos 3 meses) (R$)", min_value=0.0,
                                            value=float(st.session_state.analyzer.cliente_data.get('faturamento_3m', 0.0)))
            unidades_3m = st.number_input("* Unidades Médias (últimos 3 meses)", min_value=0,
                                         value=int(st.session_state.analyzer.cliente_data.get('unidades_3m', 0)))
            range_permitido = st.number_input("Range Permitido vs Ticket Mercado (±%)", min_value=0.0, max_value=100.0,
                                             value=float(st.session_state.analyzer.cliente_data.get('range_permitido', 0.20) * 100),
                                             step=1.0,
                                             help="Define a tolerância de variação aceitável do ticket")
            ticket_custom = st.number_input("Ticket Custom (R$) - Opcional", min_value=0.0,
                                           value=float(st.session_state.analyzer.cliente_data.get('ticket_custom', 0.0) or 0.0),
                                           help="Use para testar um ticket diferente do atual")
        
        submitted = st.form_submit_button("💾 Salvar Dados do Cliente", use_container_width=True, type="primary")
        
        if submitted:
            if not empresa or not categoria or margem == 0 or faturamento_3m == 0 or unidades_3m == 0:
                st.error("❌ Por favor, preencha todos os campos obrigatórios (marcados com *)")
            else:
                st.session_state.analyzer.set_cliente_data(
                    empresa=empresa,
                    categoria=categoria,
                    ticket_medio=ticket_medio,
                    margem=margem,
                    faturamento_3m=faturamento_3m,
                    unidades_3m=unidades_3m,
                    range_permitido=range_permitido,
                    ticket_custom=ticket_custom if ticket_custom > 0 else None
                )
                st.success("✅ Dados do cliente salvos com sucesso!")
                st.balloons()
    
    # Mostrar resumo dos dados salvos
    if st.session_state.analyzer.cliente_data:
        st.markdown("---")
        st.markdown("### 📋 Resumo dos Dados Salvos")
        
        dados = st.session_state.analyzer.cliente_data
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Empresa", dados['empresa'])
        with col2:
            st.metric("Categoria", dados['categoria'])
        with col3:
            st.metric("Ticket Médio", f"R$ {dados['ticket_medio']:,.2f}")
        with col4:
            st.metric("Margem", f"{dados['margem']*100:.1f}%")
        
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("Faturamento 3M", f"R$ {dados['faturamento_3m']:,.2f}")
        with col6:
            st.metric("Unidades 3M", f"{dados['unidades_3m']:,}")
        with col7:
            st.metric("Range", f"±{dados['range_permitido']*100:.0f}%")
        with col8:
            if dados.get('ticket_custom'):
                st.metric("Ticket Custom", f"R$ {dados['ticket_custom']:,.2f}")

# ====================
# SEÇÃO: MERCADO CATEGORIA
# ====================
elif menu == "📈 Mercado Categoria":
    st.markdown("## 📈 Mercado da Categoria (Macro)")
    st.markdown("Adicione dados históricos da categoria para contextualizar a análise. **Esta seção é opcional.**")
    
    if not st.session_state.analyzer.cliente_data:
        st.warning("⚠️ Por favor, preencha os dados do cliente primeiro.")
    else:
        st.info("💡 **Dica:** Cole dados mensais de faturamento e unidades da categoria. Isso ajuda a identificar tendências e sazonalidade.")
        
        with st.form("form_mercado_categoria"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                periodo = st.date_input("Período (Mês/Ano)", value=datetime.now())
            with col2:
                faturamento = st.number_input("Faturamento (R$)", min_value=0.0, value=0.0, step=1000.0)
            with col3:
                unidades = st.number_input("Unidades", min_value=0, value=0, step=100)
            
            submitted = st.form_submit_button("➕ Adicionar Período", use_container_width=True)
            
            if submitted:
                if faturamento > 0 and unidades > 0:
                    st.session_state.analyzer.add_mercado_categoria(
                        periodo=periodo.strftime("%Y-%m-%d"),
                        faturamento=faturamento,
                        unidades=unidades
                    )
                    st.success(f"✅ Período {periodo.strftime('%m/%Y')} adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Faturamento e unidades devem ser maiores que zero")
        
        # Mostrar dados salvos
        if st.session_state.analyzer.mercado_categoria:
            st.markdown("---")
            st.markdown("### 📊 Dados de Mercado da Categoria")
            
            df = st.session_state.analyzer.get_mercado_categoria_df()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(
                    df.style.format({
                        'faturamento': 'R$ {:,.2f}',
                        'unidades': '{:,.0f}',
                        'ticket_medio': 'R$ {:,.2f}'
                    }),
                    use_container_width=True
                )
            
            with col2:
                st.metric("Total de Períodos", len(df))
                if len(df) > 0:
                    st.metric("Faturamento Médio", f"R$ {df['faturamento'].mean():,.2f}")
                    st.metric("Ticket Médio", f"R$ {df['ticket_medio'].mean():,.2f}")
            
            # Gráficos
            st.markdown("### 📈 Visualizações")
            
            tab1, tab2 = st.tabs(["Evolução da Categoria", "Ticket Médio"])
            
            with tab1:
                fig1 = criar_grafico_evolucao_categoria(df)
                st.plotly_chart(fig1, use_container_width=True)
            
            with tab2:
                fig2 = criar_grafico_ticket_medio(df)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Botão para limpar
            if st.button("🗑️ Limpar Dados de Mercado Categoria"):
                st.session_state.analyzer.mercado_categoria = []
                st.rerun()

# ====================
# SEÇÃO: MERCADO SUBCATEGORIAS
# ====================
elif menu == "🎯 Mercado Subcategorias":
    st.markdown("## 🎯 Mercado por Subcategoria")
    st.markdown("Adicione pelo menos **3 subcategorias** com dados de mercado dos últimos 6 meses.")
    
    if not st.session_state.analyzer.cliente_data:
        st.warning("⚠️ Por favor, preencha os dados do cliente primeiro.")
    else:
        st.info("💡 **Importante:** Informe faturamento e unidades dos últimos 6 meses. O ticket médio será calculado automaticamente.")
        
        with st.form("form_subcategoria"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                subcategoria = st.text_input("Nome da Subcategoria")
            with col2:
                faturamento_6m = st.number_input("Faturamento 6M (R$)", min_value=0.0, value=0.0, step=1000.0)
            with col3:
                unidades_6m = st.number_input("Unidades 6M", min_value=0, value=0, step=100)
            
            submitted = st.form_submit_button("➕ Adicionar Subcategoria", use_container_width=True)
            
            if submitted:
                if subcategoria and faturamento_6m > 0 and unidades_6m > 0:
                    st.session_state.analyzer.add_mercado_subcategoria(
                        subcategoria=subcategoria,
                        faturamento_6m=faturamento_6m,
                        unidades_6m=unidades_6m
                    )
                    st.success(f"✅ Subcategoria '{subcategoria}' adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos com valores válidos")
        
        # Mostrar ranking de subcategorias
        if st.session_state.analyzer.mercado_subcategorias:
            st.markdown("---")
            st.markdown("### 🏆 Ranking de Subcategorias")
            
            df_ranking = st.session_state.analyzer.gerar_ranking()
            
            # Aplicar estilo condicional
            def colorir_status(val):
                if val == 'FOCO':
                    return 'background-color: #d4edda; color: #155724; font-weight: bold'
                elif val == 'OK':
                    return 'background-color: #fff3cd; color: #856404; font-weight: bold'
                elif val == 'EVITAR':
                    return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                return ''
            
            styled_df = df_ranking.style.format({
                'Mercado (R$)': 'R$ {:,.2f}',
                'Unidades 6M': '{:,.0f}',
                'Ticket Mercado': 'R$ {:,.2f}',
                'Ticket Cliente': 'R$ {:,.2f}',
                'Score': '{:.3f}'
            }).applymap(colorir_status, subset=['Status'])
            
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Métricas resumo
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Subcategorias", len(df_ranking))
            with col2:
                foco_count = len(df_ranking[df_ranking['Status'] == 'FOCO'])
                st.metric("FOCO", foco_count, delta="Prioridade Alta")
            with col3:
                ok_count = len(df_ranking[df_ranking['Status'] == 'OK'])
                st.metric("OK", ok_count, delta="Prioridade Média")
            with col4:
                evitar_count = len(df_ranking[df_ranking['Status'] == 'EVITAR'])
                st.metric("EVITAR", evitar_count, delta="Não Recomendado")
            
            # Visualizações
            st.markdown("### 📊 Visualizações")
            
            tab1, tab2 = st.tabs(["Ranking por Score", "Tamanho de Mercado"])
            
            with tab1:
                fig1 = criar_grafico_ranking_subcategorias(df_ranking)
                st.plotly_chart(fig1, use_container_width=True)
            
            with tab2:
                fig2 = criar_grafico_mercado_subcategorias(df_ranking)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Botão para limpar
            if st.button("🗑️ Limpar Subcategorias"):
                st.session_state.analyzer.mercado_subcategorias = []
                st.rerun()

# ====================
# SEÇÃO: DASHBOARD EXECUTIVO
# ====================
elif menu == "📊 Dashboard Executivo":
    st.markdown("## 📊 Dashboard Executivo")
    
    if not st.session_state.analyzer.cliente_data:
        st.warning("⚠️ Por favor, preencha os dados do cliente primeiro.")
    elif not st.session_state.analyzer.mercado_subcategorias:
        st.warning("⚠️ Por favor, adicione pelo menos 3 subcategorias.")
    else:
        # Gerar ranking
        df_ranking = st.session_state.analyzer.gerar_ranking()
        
        # Seletor de subcategoria
        st.markdown("### 🎯 Selecione a Subcategoria para Análise Detalhada")
        
        subcategoria_selecionada = st.selectbox(
            "Subcategoria:",
            options=df_ranking['Subcategoria'].tolist(),
            index=0
        )
        
        if subcategoria_selecionada:
            # Obter dados da subcategoria
            subcat_info = df_ranking[df_ranking['Subcategoria'] == subcategoria_selecionada].iloc[0]
            
            st.markdown("---")
            
            # KPIs principais
            st.markdown("### 📈 Indicadores Principais")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "Mercado 6M",
                    f"R$ {subcat_info['Mercado (R$)']:,.0f}",
                    help="Volume total do mercado nos últimos 6 meses"
                )
            
            with col2:
                st.metric(
                    "Ticket Mercado",
                    f"R$ {subcat_info['Ticket Mercado']:,.2f}",
                    help="Ticket médio do mercado"
                )
            
            with col3:
                st.metric(
                    "Ticket Cliente",
                    f"R$ {subcat_info['Ticket Cliente']:,.2f}",
                    help="Ticket médio do cliente"
                )
            
            with col4:
                # Calcular share atual
                share_atual = st.session_state.analyzer.calcular_share_atual(subcat_info['Mercado (R$)'])
                st.metric(
                    "Share Atual",
                    f"{share_atual:.4f}%",
                    help="Participação estimada do cliente no mercado"
                )
            
            with col5:
                margem = st.session_state.analyzer.cliente_data.get('margem', 0) * 100
                st.metric(
                    "Margem",
                    f"{margem:.1f}%",
                    help="Margem de lucro do cliente"
                )
            
            # Gauge de Score e Status
            col_gauge1, col_gauge2 = st.columns(2)
            
            with col_gauge1:
                fig_gauge = criar_gauge_score(subcat_info['Score'], subcat_info['Status'])
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            with col_gauge2:
                # Comparação de tickets
                limite_inf, limite_sup = st.session_state.analyzer.calcular_limites_ticket(subcat_info['Ticket Mercado'])
                fig_tickets = criar_comparacao_tickets(
                    subcat_info['Ticket Mercado'],
                    subcat_info['Ticket Cliente'],
                    limite_inf,
                    limite_sup
                )
                st.plotly_chart(fig_tickets, use_container_width=True)
            
            # Interpretação do Status
            st.markdown("### 🎯 Interpretação")
            
            if subcat_info['Status'] == 'FOCO':
                st.success(f"""
                ✅ **RECOMENDAÇÃO: FOCO**
                
                Esta subcategoria é a **melhor oportunidade identificada**:
                - ✅ Mercado grande (R$ {subcat_info['Mercado (R$)']:,.0f})
                - ✅ Ticket do cliente alinhado com o mercado
                - ✅ Score alto ({subcat_info['Score']:.2f})
                - 📌 Leitura: {subcat_info['Leitura']}
                
                **Ação recomendada:** Priorizar investimentos e esforços nesta subcategoria.
                """)
            elif subcat_info['Status'] == 'OK':
                st.info(f"""
                💡 **RECOMENDAÇÃO: OK (Secundária)**
                
                Esta subcategoria tem potencial moderado:
                - ⚠️ Score médio ({subcat_info['Score']:.2f})
                - 📌 Leitura: {subcat_info['Leitura']}
                
                **Ação recomendada:** Considerar como oportunidade secundária após focar na prioridade principal.
                """)
            else:
                st.error(f"""
                ⛔ **RECOMENDAÇÃO: EVITAR**
                
                Esta subcategoria **não é recomendada**:
                - ❌ Score baixo ({subcat_info['Score']:.2f})
                - ❌ Ticket desalinhado ou mercado pequeno
                - 📌 Leitura: {subcat_info['Leitura']}
                
                **Ação recomendada:** Evitar investimentos. Focar em subcategorias com status FOCO.
                """)
            
            # Simulação de Cenários
            st.markdown("---")
            st.markdown("### 💰 Simulação de Cenários")
            
            resultado_cenarios = st.session_state.analyzer.simular_cenarios(subcategoria_selecionada)
            
            if resultado_cenarios:
                df_cenarios = resultado_cenarios['cenarios']
                
                st.info(f"""
                **Como ler os cenários:**
                - **Conservador (0,2%):** Meta conservadora de participação no mercado
                - **Provável (0,5%):** Meta realista baseada em crescimento típico
                - **Otimista (1,0%):** Meta agressiva com investimento alto
                
                **Share atual estimado:** {resultado_cenarios['share_atual']:.4f}%
                """)
                
                # Tabela de cenários
                st.dataframe(
                    df_cenarios.style.format({
                        'Ticket Usado': 'R$ {:,.2f}',
                        'Receita Projetada 6M': 'R$ {:,.0f}',
                        'Lucro Projetado 6M': 'R$ {:,.0f}',
                        'Delta vs Atual': 'R$ {:,.0f}',
                        'Crescimento (%)': '{:,.1f}%'
                    }),
                    use_container_width=True
                )
                
                # Gráficos de cenários
                tab1, tab2 = st.tabs(["Receita e Lucro", "Crescimento Percentual"])
                
                with tab1:
                    fig_cenarios = criar_grafico_cenarios(df_cenarios)
                    st.plotly_chart(fig_cenarios, use_container_width=True)
                
                with tab2:
                    fig_crescimento = criar_grafico_crescimento(df_cenarios)
                    st.plotly_chart(fig_crescimento, use_container_width=True)
                
                # Insights dos cenários
                st.markdown("### 💡 Insights dos Cenários")
                
                col_c1, col_c2, col_c3 = st.columns(3)
                
                cenario_conservador = df_cenarios.iloc[0]
                cenario_provavel = df_cenarios.iloc[1]
                cenario_otimista = df_cenarios.iloc[2]
                
                with col_c1:
                    st.markdown(f"""
                    **🟢 Cenário Conservador**
                    - Receita: R$ {cenario_conservador['Receita Projetada 6M']:,.0f}
                    - Lucro: R$ {cenario_conservador['Lucro Projetado 6M']:,.0f}
                    - Crescimento: {cenario_conservador['Crescimento (%)']:,.0f}%
                    """)
                
                with col_c2:
                    st.markdown(f"""
                    **🟡 Cenário Provável**
                    - Receita: R$ {cenario_provavel['Receita Projetada 6M']:,.0f}
                    - Lucro: R$ {cenario_provavel['Lucro Projetado 6M']:,.0f}
                    - Crescimento: {cenario_provavel['Crescimento (%)']:,.0f}%
                    """)
                
                with col_c3:
                    st.markdown(f"""
                    **🔴 Cenário Otimista**
                    - Receita: R$ {cenario_otimista['Receita Projetada 6M']:,.0f}
                    - Lucro: R$ {cenario_otimista['Lucro Projetado 6M']:,.0f}
                    - Crescimento: {cenario_otimista['Crescimento (%)']:,.0f}%
                    """)

# ====================
# SEÇÃO: SOBRE
# ====================
elif menu == "ℹ️ Sobre":
    st.markdown("## ℹ️ Sobre a Ferramenta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📖 Descrição
        
        Esta ferramenta foi desenvolvida para ajudar **consultores, gestores de marketplace e sellers** a tomar
        decisões estratégicas baseadas em dados sobre **em qual categoria/subcategoria focar**.
        
        ### 🎯 Metodologia
        
        A análise combina dois fatores principais:
        
        1. **Tamanho de Mercado (70%)**
           - Volume de faturamento da subcategoria
           - Quanto maior, maior o potencial
        
        2. **Fit de Ticket (30%)**
           - Alinhamento entre ticket do cliente e ticket do mercado
           - Considera range de tolerância configurável
        
        ### 📊 Outputs
        
        - **Score de 0 a 1:** Priorização quantitativa
        - **Status (FOCO/OK/EVITAR):** Recomendação clara
        - **Cenários Automáticos:** Projeções de receita e lucro
        - **Visualizações Interativas:** Gráficos com Plotly
        """)
    
    with col2:
        st.markdown("""
        ### 🚀 Tecnologias
        
        - **Streamlit:** Framework web interativo
        - **Pandas:** Manipulação de dados
        - **Plotly:** Visualizações interativas
        - **Python 3.x:** Backend
        
        ### 📝 Versão
        
        **v1.0.0** - Janeiro 2026
        
        ### 👨‍💻 Desenvolvimento
        
        Desenvolvido por **GenSpark AI Developer**
        
        Baseado no template Excel "Análise de Mercado Marketplace v8"
        
        ### 📄 Licença
        
        MIT License - Uso livre com atribuição
        
        ### 🔗 Links
        
        - [GitHub Repository](#)
        - [Documentação](#)
        - [Suporte](#)
        """)
    
    st.markdown("---")
    st.markdown("""
    ### 🙏 Agradecimentos
    
    Esta ferramenta é baseada no template Excel de análise de mercado, adaptado e expandido para formato web interativo.
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>📊 <strong>Análise de Mercado Marketplace</strong> v1.0.0</p>
    <p>Desenvolvido com ❤️ usando Streamlit</p>
</div>
""", unsafe_allow_html=True)
