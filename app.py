#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Streamlit - Tamanho do Mercado
Dashboard interativo para análise estratégica de múltiplas categorias macro
Layout Modernizado - Versão Dark Theme - Suporte Mensal Híbrido
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os
import json
import re
import io
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.pdf_generator import PDFReportGenerator

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
    page_title="Inteligência de Mercado",
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
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    try:
        s = str(val).replace('R$', '').replace('$', '').strip()
        if not s: return 0.0
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'): s = s.replace('.', '').replace(',', '.')
            else: s = s.replace(',', '')
        elif ',' in s: s = s.replace(',', '.')
        return float(s)
    except:
        return 0.0

def calcular_limites_ticket_local(ticket_mercado, range_permitido=0.20):
    """Calcula limites inferior e superior baseado no ticket do mercado"""
    if not ticket_mercado: return 0.0, 0.0
    inf = ticket_mercado * (1 - range_permitido)
    sup = ticket_mercado * (1 + range_permitido)
    return inf, sup

def criar_metric_card(icon_svg, label, value, border_color="#1E3A8A"):
    """Cria um card de métrica estilizado com ícone circular"""
    return f"""
    <div style="
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 16px;
        padding: 24px 20px;
        text-align: left;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="
            width: 45px;
            height: 45px;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        ">
            {icon_svg}
        </div>
        <div>
            <div style="
                font-size: 0.7rem;
                color: #FFFFFF;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 8px;
                font-weight: 600;
                opacity: 0.8;
            ">{label}</div>
            <div style="
                font-size: 1.5rem;
                color: #FFFFFF;
                font-weight: 700;
            ">{value}</div>
        </div>
    </div>
    """

# Ícones SVG Estilizados
SVG_ICONS = {
    "box": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"></path><path d="m3.3 7 8.7 5 8.7-5"></path><path d="M12 22V12"></path></svg>',
    "dollar": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
    "chart": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    "target": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>',
    "user": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
    "file": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>'
}

# --- INICIALIZAÇÃO ---

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MarketAnalyzer()

# --- LÓGICA DE IMPORTAÇÃO EXCEL ---

def processar_excel(file):
    try:
        temp_analyzer = MarketAnalyzer()
        xls = pd.ExcelFile(file)
        
        # 1. Cliente
        df_cliente = pd.read_excel(file, sheet_name="Cliente", header=None)
        def get_val_by_label(labels, default=""):
            for i in range(len(df_cliente)):
                cell_val = str(df_cliente.iloc[i, 0]).strip().lower()
                for label in labels:
                    if label.lower() in cell_val: return df_cliente.iloc[i, 1]
            return default

        empresa = str(get_val_by_label(["Empresa"], "Empresa Exemplo"))
        cat_macro_cliente = str(get_val_by_label(["Categoria Macro"], "Geral"))
        ticket_medio = safe_float(get_val_by_label(["Ticket Médio"], 0))
        margem = safe_float(get_val_by_label(["Margem"], 0))
        fat_3m = safe_float(get_val_by_label(["Faturamento"], 0))
        uni_3m = int(safe_float(get_val_by_label(["Unidades"], 0)))
        
        temp_analyzer.set_cliente_data(
            empresa=empresa, categoria=cat_macro_cliente, ticket_medio=ticket_medio,
            margem=margem, faturamento_3m=fat_3m, unidades_3m=uni_3m
        )
        
        # 2. Mercado Categoria
        df_cat = pd.read_excel(file, sheet_name="Mercado_Categoria", skiprows=2)
        def find_col(df, names):
            for col in df.columns:
                if any(n.lower() in str(col).lower() for n in names): return col
            return None

        col_cat = find_col(df_cat, ["Categoria"])
        col_per = find_col(df_cat, ["Periodo", "Período"])
        col_fat = find_col(df_cat, ["Faturamento"])
        col_uni = find_col(df_cat, ["Unidades"])

        if col_cat and col_per:
            for _, row in df_cat.iterrows():
                if pd.notna(row[col_cat]) and pd.notna(row[col_per]):
                    raw_per = row[col_per]
                    per_val = raw_per.strftime('%d/%m/%Y') if isinstance(raw_per, datetime) else str(raw_per).strip()
                    temp_analyzer.add_mercado_categoria(str(row[col_cat]), per_val, safe_float(row[col_fat]), int(safe_float(row[col_uni])))
        
        # 3. Mercado Subcategoria (MENSAL HÍBRIDO)
        # Se existir a aba Mercado_Subcategoria_Mensal, processamos ela
        if "Mercado_Subcategoria_Mensal" in xls.sheet_names:
            df_sub_m = pd.read_excel(file, sheet_name="Mercado_Subcategoria_Mensal", skiprows=2)
            c_cat = find_col(df_sub_m, ["Categoria"])
            c_sub = find_col(df_sub_m, ["Subcategoria"])
            c_per = find_col(df_sub_m, ["Periodo", "Período"])
            c_fat = find_col(df_sub_m, ["Faturamento"])
            c_uni = find_col(df_sub_m, ["Unidades"])
            
            if c_cat and c_sub and c_per:
                for _, row in df_sub_m.iterrows():
                    raw_per = row[c_per]
                    per_val = raw_per.strftime('%d/%m/%Y') if isinstance(raw_per, datetime) else str(raw_per).strip()
                    temp_analyzer.add_mercado_subcategoria(
                        str(row[c_cat]), str(row[c_sub]), per_val, 
                        safe_float(row[c_fat]), int(safe_float(row[c_uni]))
                    )
        # Fallback para o modelo clássico de 6 meses se não houver a mensal
        elif "Mercado_Subcategoria" in xls.sheet_names:
            df_sub = pd.read_excel(file, sheet_name="Mercado_Subcategoria", skiprows=2)
            c_cat = find_col(df_sub, ["Categoria"])
            c_sub = find_col(df_sub, ["Subcategoria"])
            c_fat = find_col(df_sub, ["Faturamento"])
            c_uni = find_col(df_sub, ["Unidades"])
            if c_cat and c_sub:
                for _, row in df_sub.iterrows():
                    temp_analyzer.add_mercado_subcategoria(
                        str(row[c_cat]), str(row[c_sub]), "Consolidado 6M", 
                        safe_float(row[c_fat]), int(safe_float(row[c_uni]))
                    )

        st.session_state.analyzer = temp_analyzer
        st.success(f"✅ Dados de {empresa} importados com sucesso!")
        return True
    except Exception as e:
        st.error(f"❌ Erro na importação: {e}")
        return False

# --- UI PRINCIPAL ---

def main():
    st.sidebar.title("🚀 Menu")
    with st.sidebar.expander("📥 Upload de Dados", expanded=True):
        uploaded_file = st.file_uploader("Suba sua planilha", type=["xlsx"])
        if uploaded_file:
            if processar_excel(uploaded_file):
                st.rerun()

    if not hasattr(st.session_state, 'analyzer') or not st.session_state.analyzer.cliente_data:
        st.info("Por favor, faça o upload da planilha para começar.")
        return

    analyzer = st.session_state.analyzer
    tab1, tab2, tab3 = st.tabs(["📊 Análise Mensal", "🎯 Visão 6 Meses", "📂 Gestão"])

    with tab1:
        st.title("📈 Análise Mensal de Subcategorias")
        cats = list(analyzer.mercado_subcategorias.keys())
        if cats:
            sel_cat = st.selectbox("Selecione a Categoria:", cats, key="sel_cat_mensal")
            subs = list(analyzer.mercado_subcategorias[sel_cat].keys())
            sel_sub = st.selectbox("Selecione a Subcategoria:", subs)
            
            hist = analyzer.mercado_subcategorias[sel_cat][sel_sub]
            df_h = pd.DataFrame(hist)
            if not df_h.empty:
                st.plotly_chart(px.line(df_h, x="periodo", y="faturamento", title=f"Evolução Mensal: {sel_sub}"), use_container_width=True)
                st.dataframe(df_h)
        else:
            st.warning("Nenhum dado mensal encontrado.")

    with tab2:
        st.title("🎯 Visão Consolidada e Projeções (6 Meses)")
        df_ranking = analyzer.gerar_ranking()
        if not df_ranking.empty:
            st.plotly_chart(criar_grafico_ranking_subcategorias(df_ranking), use_container_width=True)
            st.dataframe(df_ranking)
            
            st.markdown("---")
            sel_sub_proj = st.selectbox("Selecione para Projeção:", df_ranking['Subcategoria'].tolist())
            row = df_ranking[df_ranking['Subcategoria'] == sel_sub_proj].iloc[0]
            res = analyzer.simular_cenarios(row['Categoria Macro'], sel_sub_proj)
            st.plotly_chart(criar_grafico_cenarios(res['cenarios']), use_container_width=True)
            st.dataframe(res['cenarios'])

if __name__ == "__main__":
    main()
