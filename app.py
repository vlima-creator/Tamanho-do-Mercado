#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Streamlit - Tamanho do Mercado
Dashboard interativo para análise estratégica de múltiplas categorias macro
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import json
import re
import io

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
    page_title="Tamanho do Mercado",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNÇÕES UTILITÁRIAS ---

def format_br(valor):
    """Formata números para o padrão brasileiro (1.234,56)"""
    if valor is None: return "0,00"
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def parse_large_number(text):
    """Converte strings como '1.5M' ou '500k' em números reais"""
    if isinstance(text, (int, float)):
        return float(text)
    
    text = str(text).strip().upper()
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    
    multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}
    match = re.match(r"([\d.]+)([KMB]?)", text)
    if match:
        value, unit = match.groups()
        try:
            num = float(value)
            if unit in multipliers:
                num *= multipliers[unit]
            return num
        except ValueError:
            return 0.0
    return 0.0

def safe_float(val):
    try:
        if pd.isna(val): return 0.0
        return float(val)
    except:
        return 0.0

def calcular_limites_ticket_local(ticket_mercado, range_permitido=0.20):
    """Calcula limites inferior e superior baseado no ticket do mercado"""
    if not ticket_mercado: return 0.0, 0.0
    inf = ticket_mercado * (1 - range_permitido)
    sup = ticket_mercado * (1 + range_permitido)
    return inf, sup

# --- INICIALIZAÇÃO ---

# Garantir que o analyzer esteja sempre na sessão
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MarketAnalyzer()

# --- LÓGICA DE IMPORTAÇÃO EXCEL ---

def processar_excel(file):
    try:
        # Criar novo analyzer temporário
        temp_analyzer = MarketAnalyzer()
        
        # 1. Cliente
        df_cliente = pd.read_excel(file, sheet_name="Cliente", header=None)
        empresa = str(df_cliente.iloc[4, 1])
        cat_macro_cliente = str(df_cliente.iloc[5, 1])
        ticket_medio = safe_float(df_cliente.iloc[6, 1])
        margem = safe_float(df_cliente.iloc[7, 1])
        fat_3m = safe_float(df_cliente.iloc[8, 1])
        uni_3m = int(safe_float(df_cliente.iloc[9, 1]))
        range_p = safe_float(df_cliente.iloc[10, 1])
        ticket_c = df_cliente.iloc[11, 1]
        ticket_custom = safe_float(ticket_c) if pd.notna(ticket_c) and str(ticket_c).strip() != "" else None
        
        temp_analyzer.set_cliente_data(
            empresa=empresa, categoria=cat_macro_cliente, ticket_medio=ticket_medio,
            margem=margem, faturamento_3m=fat_3m, unidades_3m=uni_3m,
            range_permitido=range_p, ticket_custom=ticket_custom
        )
        
        # 2. Mercado Categoria
        df_cat = pd.read_excel(file, sheet_name="Mercado_Categoria", skiprows=2)
        count_cat = 0
        for _, row in df_cat.iterrows():
            if pd.notna(row['Categoria']) and pd.notna(row['Periodo (texto)']):
                temp_analyzer.add_mercado_categoria(
                    str(row['Categoria']), str(row['Periodo (texto)']), 
                    safe_float(row['Faturamento (R$)']), int(safe_float(row['Unidades']))
                )
                count_cat += 1
                
        # 3. Mercado Subcategoria
        df_sub = pd.read_excel(file, sheet_name="Mercado_Subcategoria", skiprows=2)
        count_sub = 0
        for _, row in df_sub.iterrows():
            if pd.notna(row['Categoria']) and pd.notna(row['Subcategoria']):
                temp_analyzer.add_mercado_subcategoria(
                    str(row['Categoria']), str(row['Subcategoria']), 
                    safe_float(row['Faturamento 6M (R$)']), int(safe_float(row['Unidades 6M']))
                )
                count_sub += 1
        
        # ATUALIZAÇÃO CRÍTICA: Substituir o objeto na sessão
        st.session_state.analyzer = temp_analyzer
        st.session_state['data_version'] = datetime.now().timestamp()
        st.session_state['last_upload_info'] = f"Empresa: {empresa} | Macros: {count_cat} | Subs: {count_sub}"
        return True
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return False

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: bold; color: #FFFFFF; background-color: #1E1E1E;
        text-align: center; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 2rem; border-bottom: 4px solid #3498db;
    }
    .metric-card {
        background-color: #262730; padding: 1.2rem; border-radius: 0.5rem; border-top: 3px solid #3498db; text-align: center;
    }
    .metric-label { font-size: 0.85rem; color: #A0A0A0; margin-bottom: 0.3rem; }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: #FFFFFF; }
    .insight-card {
        background-color: #1E1E1E; padding: 1.5rem; border-radius: 0.5rem; border-left: 5px solid #3498db; margin-bottom: 1rem;
    }
    .insight-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🧭 Navegação")
    menu = st.radio("Escolha a seção:", ["🏠 Início", "👤 Dados do Cliente", "📈 Gestão de Categorias", "🎯 Mercado Subcategorias", "📊 Dashboard Executivo"])
    
    st.markdown("---")
    st.markdown("### 📤 Importar Dados")
    
    uploaded_file = st.file_uploader("Suba sua planilha Excel", type=["xlsx"], key="excel_uploader_v5")
    if uploaded_file is not None:
        if st.button("🚀 Processar Planilha", use_container_width=True):
            if processar_excel(uploaded_file):
                st.success("Dados carregados!")
                st.rerun()
    
    if 'last_upload_info' in st.session_state:
        st.info(st.session_state.last_upload_info)
    
    st.markdown("---")
    if st.button("🗑️ Limpar Tudo (Zerar)", use_container_width=True, type="secondary"):
        st.session_state.analyzer = MarketAnalyzer()
        if 'last_upload_info' in st.session_state: del st.session_state['last_upload_info']
        st.rerun()

# Header
st.markdown('<div class="main-header">📊 Tamanho do Mercado</div>', unsafe_allow_html=True)

# Referência curta para o analyzer da sessão
analyzer = st.session_state.analyzer

# ====================
# SEÇÃO: INÍCIO
# ====================
if menu == "🏠 Início":
    st.markdown("## 🎯 Bem-vindo")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🚀 Como usar?
        1. **Importe seu Excel**: Use o campo na barra lateral para subir sua planilha preenchida.
        2. **Ajuste Manual**: Se precisar, altere os dados nas abas de Cliente, Categorias ou Subcategorias.
        3. **Analise**: Vá para o Dashboard Executivo para ver o ranking e os cenários.
        """)
    with col2:
        st.info("💡 **Dica**: O sistema agora aceita o modelo de planilha que você já utiliza, facilitando a migração dos dados!")
        
    if not analyzer.cliente_data:
        st.warning("⚠️ Nenhum dado carregado. Suba uma planilha na barra lateral para começar.")
    else:
        st.success(f"✅ Dados carregados para: **{analyzer.cliente_data.get('empresa', 'Empresa')}**")

# ====================
# SEÇÃO: DADOS DO CLIENTE
# ====================
elif menu == "👤 Dados do Cliente":
    st.markdown("## 👤 Dados do Cliente")
    ver = st.session_state.get('data_version', 0)
    
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Nome da Empresa", value=analyzer.cliente_data.get('empresa', ''), key=f"emp_{ver}")
            ticket_medio = st.number_input("Ticket Médio Geral (R$)", min_value=0.0, value=float(analyzer.cliente_data.get('ticket_medio', 0.0)), format="%.2f", key=f"tm_{ver}")
            margem = st.number_input("Margem Atual (%)", min_value=0.0, max_value=100.0, value=float(analyzer.cliente_data.get('margem', 0.0) * 100), step=0.1, key=f"mg_{ver}")
        with col2:
            fat_val = analyzer.cliente_data.get('faturamento_3m', 0.0)
            fat_input = st.text_input("Faturamento Médio 3M (R$)", value=str(fat_val) if fat_val > 0 else "", key=f"fat_{ver}")
            uni_val = analyzer.cliente_data.get('unidades_3m', 0)
            uni_input = st.text_input("Unidades Médias 3M", value=str(uni_val) if uni_val > 0 else "", key=f"uni_{ver}")
            range_permitido = st.number_input("Range Permitido (±%)", min_value=0.0, max_value=100.0, value=float(analyzer.cliente_data.get('range_permitido', 0.20) * 100), key=f"rp_{ver}")
        
        if st.form_submit_button("💾 Salvar Dados"):
            analyzer.set_cliente_data(
                empresa=empresa, categoria="Geral", ticket_medio=ticket_medio,
                margem=margem, faturamento_3m=parse_large_number(fat_input), 
                unidades_3m=int(parse_large_number(uni_input)), range_permitido=range_permitido
            )
            st.toast("✅ Dados salvos!", icon="💾")
            st.rerun()

# ====================
# SEÇÃO: GESTÃO DE CATEGORIAS
# ====================
elif menu == "📈 Gestão de Categorias":
    st.markdown("## 📈 Categorias Macro")
    with st.expander("➕ Adicionar Nova Categoria Macro"):
        with st.form("nova_cat"):
            nova_cat = st.text_input("Nome da Categoria")
            col1, col2, col3 = st.columns(3)
            periodo = col1.text_input("Período (ex: Jan/24)")
            fat_cat = col2.text_input("Faturamento Mercado (R$)")
            uni_cat = col3.text_input("Unidades Mercado")
            if st.form_submit_button("Adicionar"):
                if nova_cat:
                    analyzer.add_mercado_categoria(nova_cat, periodo, parse_large_number(fat_cat), int(parse_large_number(uni_cat)))
                    st.rerun()

    if analyzer.mercado_categoria:
        for cat in list(analyzer.mercado_categoria.keys()):
            df_cat = analyzer.get_mercado_categoria_df(cat).copy()
            if not df_cat.empty:
                col_title, col_actions = st.columns([4, 1])
                col_title.markdown(f"### 📂 {cat}")
                
                with col_actions:
                    if st.button(f"🗑️ Excluir Categoria", key=f"del_cat_{cat}"):
                        analyzer.remover_mercado_categoria(cat)
                        st.rerun()
                
                # Edição de Períodos
                with st.expander(f"📝 Editar Dados de {cat}"):
                    for i, row in df_cat.iterrows():
                        with st.form(f"edit_cat_{cat}_{i}"):
                            st.markdown(f"**Período: {row['periodo']}**")
                            c1, c2, c3 = st.columns(3)
                            new_name = c1.text_input("Nome Categoria", value=cat)
                            new_fat = c2.text_input("Faturamento (R$)", value=str(row['faturamento']))
                            new_uni = c3.text_input("Unidades", value=str(row['unidades']))
                            if st.form_submit_button("Salvar Alterações"):
                                analyzer.editar_mercado_categoria(cat, new_name, row['periodo'], parse_large_number(new_fat), int(parse_large_number(new_uni)))
                                st.rerun()

                # Métricas da Categoria
                m_col1, m_col2 = st.columns(2)
                fat_medio = df_cat['faturamento'].mean()
                tm_medio = df_cat['ticket_medio'].mean()
                m_col1.metric("Faturamento Médio", f"R$ {format_br(fat_medio)}")
                m_col2.metric("Ticket Médio", f"R$ {format_br(tm_medio)}")
                
                # Tabela de Dados
                df_disp = df_cat.copy()
                df_disp['faturamento'] = df_disp['faturamento'].apply(format_br)
                df_disp['ticket_medio'] = df_disp['ticket_medio'].apply(format_br)
                st.dataframe(df_disp, use_container_width=True)
                
                # Visualizações da Categoria
                st.markdown("#### 📈 Visualizações")
                tab1, tab2 = st.tabs(["Evolução da Categoria", "Ticket Médio"])
                with tab1:
                    st.plotly_chart(criar_grafico_evolucao_categoria(df_cat), use_container_width=True)
                with tab2:
                    st.plotly_chart(criar_grafico_ticket_medio(df_cat), use_container_width=True)
                st.markdown("---")
    else:
        st.info("Nenhuma categoria macro cadastrada.")

# ====================
# SEÇÃO: SUBCATEGORIAS
# ====================
elif menu == "🎯 Mercado Subcategorias":
    st.markdown("## 🎯 Subcategorias")
    categorias = list(analyzer.mercado_categoria.keys())
    if not categorias:
        st.warning("Cadastre uma Categoria Macro primeiro!")
    else:
        cat_sel = st.selectbox("Selecione a Categoria Macro:", categorias)
        with st.form("nova_sub"):
            sub = st.text_input("Nome da Subcategoria")
            col1, col2 = st.columns(2)
            fat_6m = col1.text_input("Faturamento 6M (R$)")
            uni_6m = col2.text_input("Unidades 6M")
            if st.form_submit_button("Adicionar Subcategoria"):
                if sub:
                    analyzer.add_mercado_subcategoria(cat_sel, sub, parse_large_number(fat_6m), int(parse_large_number(uni_6m)))
                    st.rerun()
        
        if cat_sel in analyzer.mercado_subcategorias:
            df_sub_raw = pd.DataFrame(analyzer.mercado_subcategorias[cat_sel])
            
            st.markdown("### 📋 Lista de Subcategorias")
            for i, row in df_sub_raw.iterrows():
                with st.expander(f"🔹 {row['subcategoria']} - R$ {format_br(row['faturamento_6m'])}"):
                    with st.form(f"edit_sub_{cat_sel}_{i}"):
                        c1, c2, c3 = st.columns(3)
                        new_sub = c1.text_input("Nome Subcategoria", value=row['subcategoria'])
                        new_fat = c2.text_input("Faturamento 6M (R$)", value=str(row['faturamento_6m']))
                        new_uni = c3.text_input("Unidades 6M", value=str(row['unidades_6m']))
                        
                        b1, b2 = st.columns(2)
                        if b1.form_submit_button("💾 Salvar"):
                            analyzer.editar_mercado_subcategoria(cat_sel, row['subcategoria'], new_sub, parse_large_number(new_fat), int(parse_large_number(new_uni)))
                            st.rerun()
                        if b2.form_submit_button("🗑️ Excluir", type="secondary"):
                            analyzer.remover_mercado_subcategoria(cat_sel, row['subcategoria'])
                            st.rerun()
            
            st.markdown("---")
            df_sub_disp = df_sub_raw.copy()
            df_sub_disp['faturamento_6m'] = df_sub_disp['faturamento_6m'].apply(format_br)
            df_sub_disp['ticket_medio'] = df_sub_disp['ticket_medio'].apply(format_br)
            st.dataframe(df_sub_disp, use_container_width=True)

# ====================
# SEÇÃO: DASHBOARD
# ====================
elif menu == "📊 Dashboard Executivo":
    st.markdown("## 📊 Dashboard Executivo")
    df_ranking = analyzer.gerar_ranking()
    if df_ranking.empty:
        st.info("Importe ou adicione dados para visualizar o dashboard.")
    else:
        col_rank1, col_rank2 = st.columns([1, 1])
        with col_rank1:
            st.markdown("### 🏆 Ranking de Oportunidades")
            df_display = df_ranking[['Categoria Macro', 'Subcategoria', 'Score', 'Status']].copy()
            st.dataframe(df_display, use_container_width=True)
        with col_rank2:
            st.plotly_chart(criar_grafico_ranking_subcategorias(df_ranking), use_container_width=True)
            
        st.markdown("---")
        sub_foco = st.selectbox("Análise Detalhada da Subcategoria:", df_ranking['Subcategoria'].tolist())
        row_foco = df_ranking[df_ranking['Subcategoria'] == sub_foco].iloc[0]
        
        # Seção de Simulação Interativa
        st.markdown("### 💰 Simulação de Cenários")
        
        with st.expander("⚙️ Ajustar Metas de Share", expanded=False):
            col_s1, col_s2, col_s3 = st.columns(3)
            s_cons = col_s1.slider("Share Conservador (%)", 0.0, 5.0, 0.2, 0.1) / 100
            s_prov = col_s2.slider("Share Provável (%)", 0.0, 10.0, 0.5, 0.1) / 100
            s_otim = col_s3.slider("Share Otimista (%)", 0.0, 20.0, 1.0, 0.1) / 100
            
            custom_shares = {
                'Conservador': {'share_alvo': s_cons, 'label': f"{s_cons*100:.1f}%"},
                'Provável': {'share_alvo': s_prov, 'label': f"{s_prov*100:.1f}%"},
                'Otimista': {'share_alvo': s_otim, 'label': f"{s_otim*100:.1f}%"}
            }
        
        # CORREÇÃO: Garantir que custom_shares seja passado corretamente
        res = analyzer.simular_cenarios(row_foco['Categoria Macro'], sub_foco, custom_shares)
        
        if res:
            # Indicadores Principais
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.markdown(f'<div class="metric-card"><div class="metric-label">Mercado 6M</div><div class="metric-value">R$ {format_br(res["mercado_6m"])}</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><div class="metric-label">Ticket Mercado</div><div class="metric-value">R$ {format_br(res["ticket_mercado"])}</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-card"><div class="metric-label">Ticket Cliente</div><div class="metric-value">R$ {format_br(row_foco["Ticket Cliente"])}</div></div>', unsafe_allow_html=True)
            m4.markdown(f'<div class="metric-card"><div class="metric-label">Share Atual</div><div class="metric-value">{res["share_atual"]:.4f}%</div></div>', unsafe_allow_html=True)
            m5.markdown(f'<div class="metric-card"><div class="metric-label">Margem</div><div class="metric-value">{analyzer.cliente_data.get("margem", 0)*100:.1f}%</div></div>', unsafe_allow_html=True)
            
            # Gráficos de Score e Ticket
            g1, g2 = st.columns(2)
            with g1: st.plotly_chart(criar_gauge_score(row_foco['Score'], row_foco['Status']), use_container_width=True)
            with g2:
                r_perm = analyzer.cliente_data.get('range_permitido', 0.20)
                l_inf, l_sup = calcular_limites_ticket_local(res['ticket_mercado'], r_perm)
                st.plotly_chart(criar_comparacao_tickets(res['ticket_mercado'], row_foco['Ticket Cliente'], l_inf, l_sup), use_container_width=True)
            
            # Tabela e Gráfico de Cenários
            st.markdown("#### 📈 Projeções de Receita e Lucro")
            df_cen = res['cenarios'].copy()
            
            c_tab1, c_tab2 = st.tabs(["Tabela de Dados", "Gráfico Comparativo"])
            with c_tab1:
                df_disp_cen = df_cen.copy()
                for col in ['Receita Projetada 6M', 'Lucro Projetado 6M', 'Delta vs Atual']:
                    df_disp_cen[col] = df_disp_cen[col].apply(format_br)
                
                # Formatar Crescimento (%) com padrão brasileiro
                df_disp_cen['Crescimento (%)'] = df_disp_cen['Crescimento (%)'].apply(lambda x: f"{x:,.1f}%".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.dataframe(df_disp_cen, use_container_width=True)
            with c_tab2:
                st.plotly_chart(criar_grafico_cenarios(df_cen), use_container_width=True)
            
            # SEÇÃO DE INSIGHTS
            st.markdown("### 💡 Insights dos Cenários")
            i_col1, i_col2, i_col3 = st.columns(3)
            
            with i_col1:
                row = df_cen.iloc[0]
                st.markdown(f"""
                <div class="insight-card" style="border-left-color: #2ecc71;">
                    <div class="insight-title">🟢 Cenário Conservador</div>
                    • Receita: R$ {format_br(row['Receita Projetada 6M'])}<br>
                    • Lucro: R$ {format_br(row['Lucro Projetado 6M'])}<br>
                    • Crescimento: {format_br(row['Crescimento (%)'])}%
                </div>
                """, unsafe_allow_html=True)
                
            with i_col2:
                row = df_cen.iloc[1]
                st.markdown(f"""
                <div class="insight-card" style="border-left-color: #f1c40f;">
                    <div class="insight-title">🟡 Cenário Provável</div>
                    • Receita: R$ {format_br(row['Receita Projetada 6M'])}<br>
                    • Lucro: R$ {format_br(row['Lucro Projetado 6M'])}<br>
                    • Crescimento: {format_br(row['Crescimento (%)'])}%
                </div>
                """, unsafe_allow_html=True)
                
            with i_col3:
                row = df_cen.iloc[2]
                st.markdown(f"""
                <div class="insight-card" style="border-left-color: #e74c3c;">
                    <div class="insight-title">🔴 Cenário Otimista</div>
                    • Receita: R$ {format_br(row['Receita Projetada 6M'])}<br>
                    • Lucro: R$ {format_br(row['Lucro Projetado 6M'])}<br>
                    • Crescimento: {format_br(row['Crescimento (%)'])}%
                </div>
                """, unsafe_allow_html=True)
