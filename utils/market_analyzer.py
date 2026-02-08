#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de cálculos de mercado e análise estratégica - Suporte a Múltiplas Categorias e Dados Mensais
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class MarketAnalyzer:
    """Classe para análise de mercado e cálculo de scores com suporte a múltiplas categorias e dados mensais"""
    
    def __init__(self):
        self.cliente_data = {
            'cac': 0.0,
            'investimento_mkt': 0.0
        }
        # Estrutura: { 'Categoria Nome': [ {periodo, faturamento, unidades, ticket_medio} ] }
        self.mercado_categoria = {} 
        # Estrutura: { 'Categoria Nome': [ {subcategoria, periodo, faturamento, unidades, ticket_medio} ] }
        self.mercado_subcategorias = {}
        
    def set_cliente_data(self, empresa: str, categoria: str, ticket_medio: float,
                        margem: float, faturamento_3m: float, unidades_3m: int,
                        range_permitido: float = 20.0, ticket_custom: float = None,
                        cac: float = 0.0, investimento_mkt: float = 0.0):
        """Define dados do cliente com novos campos de CAC e Investimento"""
        self.cliente_data.update({
            'empresa': empresa,
            'categoria_principal': categoria,
            'ticket_medio': ticket_medio if ticket_medio else (faturamento_3m / unidades_3m if unidades_3m > 0 else 0),
            'margem': margem / 100 if margem > 1 else margem,
            'faturamento_3m': faturamento_3m,
            'unidades_3m': unidades_3m,
            'range_permitido': range_permitido / 100 if range_permitido > 1 else range_permitido,
            'ticket_custom': ticket_custom,
            'cac': cac,
            'investimento_mkt': investimento_mkt
        })
        
    def add_mercado_categoria(self, categoria: str, periodo: str, faturamento: float, unidades: int):
        """Adiciona dados de mercado para uma categoria específica"""
        if categoria not in self.mercado_categoria:
            self.mercado_categoria[categoria] = []
            
        # Garantir tipos numéricos
        faturamento = float(faturamento) if faturamento else 0.0
        unidades = int(float(unidades)) if unidades else 0
            
        ticket_medio = faturamento / unidades if unidades > 0 else 0
        self.mercado_categoria[categoria].append({
            'periodo': periodo,
            'faturamento': faturamento,
            'unidades': unidades,
            'ticket_medio': ticket_medio
        })
        
    def add_mercado_subcategoria(self, categoria: str, subcategoria: str, faturamento: float, unidades: int, periodo: str = None):
        """Adiciona dados de mercado de subcategoria vinculada a uma categoria macro (suporta dados mensais)"""
        if categoria not in self.mercado_subcategorias:
            self.mercado_subcategorias[categoria] = []
            
        # Garantir tipos numéricos
        faturamento = float(faturamento) if faturamento else 0.0
        unidades = int(float(unidades)) if unidades else 0
            
        ticket_medio = faturamento / unidades if unidades > 0 else 0
        self.mercado_subcategorias[categoria].append({
            'subcategoria': subcategoria,
            'periodo': periodo,
            'faturamento': faturamento,
            'unidades': unidades,
            'ticket_medio': ticket_medio
        })
        
    def get_subcategorias_consolidadas(self, categoria: str = None) -> List[Dict]:
        """Consolida os dados mensais das subcategorias para análise de 6 meses (ou total disponível)"""
        if not self.mercado_subcategorias:
            return []
            
        categorias_para_processar = [categoria] if categoria else list(self.mercado_subcategorias.keys())
        consolidado = []
        
        for cat in categorias_para_processar:
            if cat in self.mercado_subcategorias:
                df_sub = pd.DataFrame(self.mercado_subcategorias[cat])
                if df_sub.empty: continue
                
                # Agrupar por subcategoria e somar faturamento e unidades
                df_grouped = df_sub.groupby('subcategoria').agg({
                    'faturamento': 'sum',
                    'unidades': 'sum'
                }).reset_index()
                
                for _, row in df_grouped.iterrows():
                    faturamento_total = row['faturamento']
                    unidades_total = row['unidades']
                    ticket_medio = faturamento_total / unidades_total if unidades_total > 0 else 0
                    
                    consolidado.append({
                        'categoria': cat,
                        'subcategoria': row['subcategoria'],
                        'faturamento_6m': faturamento_total,
                        'unidades_6m': unidades_total,
                        'ticket_medio': ticket_medio
                    })
        return consolidado

    def calcular_fit_ticket(self, ticket_mercado: float) -> Tuple[str, str]:
        """Calcula fit do ticket cliente vs mercado"""
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        range_pct = self.cliente_data.get('range_permitido', 0.20)
        
        limite_inferior = ticket_mercado * (1 - range_pct)
        limite_superior = ticket_mercado * (1 + range_pct)
        
        if limite_inferior <= ticket_cliente <= limite_superior:
            return "DENTRO", "Ticket OK"
        elif ticket_cliente < limite_inferior:
            return "ABAIXO", "Aumentar ticket"
        else:
            return "ACIMA", "Reduzir ticket"
    
    def calcular_confianca(self, categoria: str, subcategoria: str) -> Dict:
        """Calcula o Índice de Confiança da Projeção (0 a 100%)"""
        score = 100
        motivos = []
        
        # 1. Histórico de Mercado
        historico = self.mercado_categoria.get(categoria, [])
        if len(historico) < 3:
            score -= 30
            motivos.append("Pouco histórico de mercado (menos de 3 meses)")
        
        # 2. Discrepância de Ticket
        subcat_data = next((s for s in self.get_subcategorias_consolidadas(categoria) if s['subcategoria'] == subcategoria), None)
        if subcat_data:
            ticket_mercado = subcat_data['ticket_medio']
            ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
            if ticket_mercado > 0:
                diff = abs(ticket_cliente - ticket_mercado) / ticket_mercado
                if diff > 0.5:
                    score -= 20
                    motivos.append("Ticket muito fora da média do mercado (>50%)")
        
        # 3. Dados do Cliente
        if self.cliente_data.get('faturamento_3m', 0) == 0:
            score -= 40
            motivos.append("Faturamento atual do cliente não informado")
            
        return {
            "score": max(0, score),
            "nivel": "Alta" if score >= 80 else ("Média" if score >= 50 else "Baixa"),
            "motivos": motivos
        }

    def calcular_score(self, categoria: str, faturamento_6m: float, ticket_mercado: float) -> float:
        """Calcula score de priorização baseado na Matriz GUT adaptada"""
        subcats_cat = self.get_subcategorias_consolidadas(categoria)
        if not subcats_cat:
            return 0.0
            
        # G - Gravidade (Tamanho do Mercado - 40%)
        max_faturamento = max([s['faturamento_6m'] for s in subcats_cat])
        g = faturamento_6m / max_faturamento if max_faturamento > 0 else 0
        
        # U - Urgência (Fit de Ticket/Competitividade - 40%)
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        range_pct = self.cliente_data.get('range_permitido', 0.20)
        diff_pct = abs(ticket_cliente - ticket_mercado) / ticket_mercado if ticket_mercado > 0 else 1
        
        if diff_pct <= range_pct:
            u = 1.0
        elif ticket_cliente < ticket_mercado:
            u = 0.7 # Competitivo por volume
        else:
            u = 0.3 # Barreira de preço
            
        # T - Tendência (Margem e Potencial de Lucro - 20%)
        margem = self.cliente_data.get('margem', 0)
        t = margem
        
        score_final = (g * 0.4) + (u * 0.4) + (t * 0.2)
        return min(1.0, score_final)
    
    def calcular_status(self, score: float, fit_ticket: str) -> str:
        """Determina status baseado no score e fit de ticket"""
        if score >= 0.7 and fit_ticket == "DENTRO":
            return "FOCO"
        elif score >= 0.4 or fit_ticket == "DENTRO":
            return "OK"
        else:
            return "EVITAR"
    
    def calcular_share_atual(self, mercado_6m: float) -> float:
        """Calcula share atual do cliente no mercado da subcategoria"""
        faturamento_3m = float(self.cliente_data.get('faturamento_3m', 0))
        faturamento_6m_projetado = faturamento_3m * 2
        
        if mercado_6m > 0:
            return (faturamento_6m_projetado / mercado_6m) * 100
        return 0.0
    
    def gerar_ranking(self, categoria: str = None) -> pd.DataFrame:
        """Gera ranking de subcategorias consolidando dados mensais"""
        subcategorias_consolidadas = self.get_subcategorias_consolidadas(categoria)
        if not subcategorias_consolidadas:
            return pd.DataFrame()
        
        ranking_data = []
        
        for subcat in subcategorias_consolidadas:
            cat = subcat['categoria']
            score = self.calcular_score(cat, subcat['faturamento_6m'], subcat['ticket_medio'])
            fit_status, leitura = self.calcular_fit_ticket(subcat['ticket_medio'])
            status = self.calcular_status(score, fit_status)
            
            ranking_data.append({
                'Categoria Macro': cat,
                'Subcategoria': subcat['subcategoria'],
                'Mercado (R$)': subcat['faturamento_6m'],
                'Unidades 6M': subcat['unidades_6m'],
                'Ticket Mercado': subcat['ticket_medio'],
                'Ticket Cliente': self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0),
                'Score': score,
                'Status': status,
                'Leitura': leitura
            })
        
        if not ranking_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(ranking_data)
        df = df.sort_values(['Score'], ascending=False).reset_index(drop=True)
        
        return df
    
    def simular_cenarios(self, categoria: str, subcategoria: str, custom_shares: Dict = None) -> Dict:
        """Simula cenários de crescimento para uma subcategoria consolidada"""
        subcats_consolidadas = self.get_subcategorias_consolidadas(categoria)
        subcat_data = next((s for s in subcats_consolidadas if s['subcategoria'] == subcategoria), None)
        
        if not subcat_data:
            return {}
        
        mercado_6m = subcat_data['faturamento_6m']
        ticket_usado = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        margem = self.cliente_data.get('margem', 0)
        fat_3m = self.cliente_data.get('faturamento_3m', 0)
        faturamento_cliente_3m = float(fat_3m) if fat_3m else 0
        
        faturamento_base_comparacao = faturamento_cliente_3m * 2
        
        if custom_shares:
            cenarios = custom_shares
        else:
            cenarios = {
                'Conservador': {'share_alvo': 0.002, 'label': '0,2%'},
                'Provável': {'share_alvo': 0.005, 'label': '0,5%'},
                'Otimista': {'share_alvo': 0.01, 'label': '1,0%'}
            }
            
        resultados = []
        for nome, dados in cenarios.items():
            share = dados['share_alvo']
            receita_projetada = mercado_6m * share
            lucro_projetado = receita_projetada * margem
            delta = receita_projetada - faturamento_base_comparacao
            crescimento_pct = (delta / faturamento_base_comparacao * 100) if faturamento_base_comparacao > 0 else 0
            
            resultados.append({
                'Cenário': nome,
                'Share Alvo': dados.get('label', f"{share*100:.1f}%"),
                'Receita Projetada 6M': receita_projetada,
                'Lucro Projetado 6M': lucro_projetado,
                'Delta vs Atual': delta,
                'Crescimento (%)': crescimento_pct
            })
            
        return {
            'subcategoria': subcategoria,
            'mercado_6m': mercado_6m,
            'share_atual': self.calcular_share_atual(mercado_6m),
            'cenarios': pd.DataFrame(resultados)
        }

    def calcular_tendencia(self, categoria: str, subcategoria: str = None) -> Dict:
        """Calcula tendência de crescimento baseada no histórico da categoria ou subcategoria"""
        if subcategoria:
            # Filtrar dados mensais apenas da subcategoria específica
            historico = [item for item in self.mercado_subcategorias_mensal if item['subcategoria'] == subcategoria]
        else:
            historico = self.mercado_categoria.get(categoria, [])
            
        if len(historico) < 2:
            return {
                "tendencia": "Estável",
                "crescimento_mensal": 0.0,
                "projecao_3m": 0.0,
                "mensal": [0, 0, 0],
                "confianca": 0.5
            }
            
        df = pd.DataFrame(historico)
        # Garantir ordenação cronológica para o cálculo da tendência
        df['periodo_dt'] = pd.to_datetime(df['periodo'], errors='coerce')
        df = df.dropna(subset=['periodo_dt']).sort_values('periodo_dt')
        
        df['faturamento'] = df['faturamento'].astype(float)
        
        # Cálculo de crescimento médio mensal
        df['crescimento'] = df['faturamento'].pct_change()
        crescimento_medio = df['crescimento'].mean()
        
        # Índice de confiança baseado na volatilidade e quantidade de dados
        volatilidade = df['crescimento'].std() if len(df) > 2 else 0.5
        confianca = max(0.3, min(0.95, (1 - volatilidade) * (len(df) / 12)))
        
        ultimo_fat = df['faturamento'].iloc[-1]
        proj_mensal = []
        for i in range(1, 4):
            proj_mensal.append(ultimo_fat * (1 + crescimento_medio) ** i)
            
        projecao_total_3m = sum(proj_mensal)
        
        return {
            "tendencia": "Alta" if crescimento_medio > 0.02 else ("Baixa" if crescimento_medio < -0.02 else "Estável"),
            "crescimento_mensal": crescimento_medio * 100,
            "projecao_3m": projecao_total_3m,
            "mensal": proj_mensal,
            "confianca": confianca
        }

    def identificar_anomalias(self, categoria: str) -> List[Dict]:
        """Detecta discrepâncias críticas entre o desempenho do cliente e o mercado"""
        anomalias = []
        df_ranking = self.gerar_ranking(categoria)
        if df_ranking.empty: return []
        
        for _, row in df_ranking.iterrows():
            subcat = row['Subcategoria']
            ticket_m = float(row['Ticket Mercado'])
            ticket_c = float(row['Ticket Cliente'])
            status = row['Status']
            
            # 1. Anomalia de Preço Crítica (>40% de diferença)
            if ticket_m > 0:
                diff_pct = (ticket_c - ticket_m) / ticket_m
                if diff_pct > 0.4:
                    anomalias.append({
                        "tipo": "Preço Crítico (Alto)",
                        "subcategoria": subcat,
                        "mensagem": f"Seu preço está {diff_pct*100:.1f}% ACIMA da média. Risco alto de perda de volume.",
                        "severidade": "Alta"
                    })
                elif diff_pct < -0.4:
                    anomalias.append({
                        "tipo": "Preço Crítico (Baixo)",
                        "subcategoria": subcat,
                        "mensagem": f"Seu preço está {abs(diff_pct)*100:.1f}% ABAIXO da média. Risco de erosão de margem.",
                        "severidade": "Média"
                    })
            
            # 2. Anomalia de Performance (Score Baixo em Mercado Grande)
            if status == "EVITAR" and row['Mercado (R$)'] > df_ranking['Mercado (R$)'].median():
                anomalias.append({
                    "tipo": "Oportunidade Perdida",
                    "subcategoria": subcat,
                    "mensagem": "Mercado volumoso, mas sua competitividade é baixa. Reavaliar portfólio.",
                    "severidade": "Baixa"
                })
        return anomalias

    def gerar_plano_acao(self, categoria: str = None) -> List[Dict]:
        """Gera recomendações estratégicas detalhadas e acionáveis com Matriz de Recomendação Automática"""
        df_ranking = self.gerar_ranking(categoria)
        if df_ranking.empty:
            return []
            
        plano = []
        for _, row in df_ranking.iterrows():
            score = row['Score']
            status = row['Status']
            leitura = row['Leitura']
            subcat = row['Subcategoria']
            mercado = row['Mercado (R$)']
            ticket_mercado = row['Ticket Mercado']
            ticket_cliente = row['Ticket Cliente']
            
            acoes = []
            
            # Matriz de Recomendação Automática (Ação Imediata)
            if status == "FOCO" and leitura == "Ticket OK":
                rec_curta = "ESCALAR AGRESSIVO"
                acao_imediata = "Aumentar investimento em Ads em 20% e garantir estoque para 60 dias."
            elif status == "FOCO" and "Aumentar" in leitura:
                rec_curta = "AJUSTAR MARGEM"
                acao_imediata = "Subir preço gradualmente (3-5%) e monitorar conversão."
            elif status == "OK" and leitura == "Ticket OK":
                rec_curta = "MANTER E OTIMIZAR"
                acao_imediata = "Focar em melhorar o CTR dos anúncios e fotos dos produtos."
            elif status == "EVITAR" and "Reduzir" in leitura:
                rec_curta = "REVISAR CUSTOS"
                acao_imediata = "Negociar com fornecedores ou buscar novos SKUs. Preço atual é barreira."
            else:
                rec_curta = "MONITORAR"
                acao_imediata = "Acompanhar movimentação dos concorrentes semanalmente."
            
            # Detalhes das ações
            if leitura == "Ticket OK":
                acoes.append(f"✅ **Preço Competitivo**: Alinhado com o mercado (R$ {ticket_mercado:,.2f}).")
            elif "Aumentar" in leitura:
                acoes.append(f"⚠️ **Preço Defasado**: R$ {(ticket_mercado - ticket_cliente):,.2f} abaixo da média.")
            else:
                acoes.append(f"⚠️ **Preço Elevado**: R$ {(ticket_cliente - ticket_mercado):,.2f} acima da média.")
            acoes.append(f"🚀 **Ação Imediata**: {acao_imediata}")
            
            plano.append({
                "Subcategoria": subcat,
                "Prioridade": "MÁXIMA" if status == "FOCO" else ("ALTA" if status == "OK" else "MÉDIA"),
                "Cor": "#FF4B4B" if status == "FOCO" else ("#FFA421" if status == "OK" else "#1E3A8A"),
                "Ações": acoes,
                "Recomendacao_Curta": rec_curta,
                "Acao_Imediata": acao_imediata,
                "Score": score
            })
            
        return plano

    def clear_data(self):
        """Limpa todos os dados"""
        self.cliente_data = {}
        self.mercado_categoria = {}
        self.mercado_subcategorias = {}

    def editar_mercado_subcategoria(self, categoria: str, sub_antiga: str, sub_nova: str, faturamento: float, unidades: int):
        """Edita uma subcategoria (atualiza todos os registros mensais dela)"""
        if categoria in self.mercado_subcategorias:
            for item in self.mercado_subcategorias[categoria]:
                if item['subcategoria'] == sub_antiga:
                    item['subcategoria'] = sub_nova
                    # Nota: A edição manual via interface substitui o valor total, 
                    # o que pode ser complexo com dados mensais. 
                    # Por simplicidade, mantemos a lógica de atualização do nome.
            
    def remover_mercado_subcategoria(self, categoria: str, subcategoria: str):
        """Remove todos os registros de uma subcategoria"""
        if categoria in self.mercado_subcategorias:
            self.mercado_subcategorias[categoria] = [
                item for item in self.mercado_subcategorias[categoria] 
                if item['subcategoria'] != subcategoria
            ]
