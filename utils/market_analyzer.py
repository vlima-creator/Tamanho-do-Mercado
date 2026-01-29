#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de cálculos de mercado e análise estratégica - Suporte a Múltiplas Categorias
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class MarketAnalyzer:
    """Classe para análise de mercado e cálculo de scores com suporte a múltiplas categorias"""
    
    def __init__(self):
        self.cliente_data = {}
        # Estrutura: { 'Categoria Nome': [ {periodo, faturamento, unidades, ticket_medio} ] }
        self.mercado_categoria = {} 
        # Estrutura: { 'Categoria Nome': [ {subcategoria, faturamento_6m, unidades_6m, ticket_medio} ] }
        self.mercado_subcategorias = {}
        
    def set_cliente_data(self, empresa: str, categoria: str, ticket_medio: float,
                        margem: float, faturamento_3m: float, unidades_3m: int,
                        range_permitido: float = 20.0, ticket_custom: float = None):
        """Define dados do cliente (agora categoria é a categoria principal/inicial)"""
        self.cliente_data = {
            'empresa': empresa,
            'categoria_principal': categoria,
            'ticket_medio': ticket_medio if ticket_medio else (faturamento_3m / unidades_3m if unidades_3m > 0 else 0),
            'margem': margem / 100 if margem > 1 else margem,
            'faturamento_3m': faturamento_3m,
            'unidades_3m': unidades_3m,
            'range_permitido': range_permitido / 100 if range_permitido > 1 else range_permitido,
            'ticket_custom': ticket_custom
        }
        
    def add_mercado_categoria(self, categoria: str, periodo: str, faturamento: float, unidades: int):
        """Adiciona dados de mercado para uma categoria específica"""
        if categoria not in self.mercado_categoria:
            self.mercado_categoria[categoria] = []
            
        ticket_medio = faturamento / unidades if unidades > 0 else 0
        self.mercado_categoria[categoria].append({
            'periodo': periodo,
            'faturamento': faturamento,
            'unidades': unidades,
            'ticket_medio': ticket_medio
        })
        
    def add_mercado_subcategoria(self, categoria: str, subcategoria: str, faturamento_6m: float, unidades_6m: int):
        """Adiciona dados de mercado de subcategoria vinculada a uma categoria macro"""
        if categoria not in self.mercado_subcategorias:
            self.mercado_subcategorias[categoria] = []
            
        ticket_medio = faturamento_6m / unidades_6m if unidades_6m > 0 else 0
        self.mercado_subcategorias[categoria].append({
            'subcategoria': subcategoria,
            'faturamento_6m': faturamento_6m,
            'unidades_6m': unidades_6m,
            'ticket_medio': ticket_medio
        })
        
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
    
    def calcular_score(self, categoria: str, faturamento_6m: float, ticket_mercado: float) -> float:
        """Calcula score de priorização dentro de uma categoria"""
        if categoria not in self.mercado_subcategorias or not self.mercado_subcategorias[categoria]:
            return 0.0
            
        # Normalizar tamanho de mercado (0-1) dentro da categoria
        max_faturamento = max([s['faturamento_6m'] for s in self.mercado_subcategorias[categoria]])
        score_mercado = faturamento_6m / max_faturamento if max_faturamento > 0 else 0
        
        # Calcular score de fit de ticket (0-1)
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        range_pct = self.cliente_data.get('range_permitido', 0.20)
        
        diff_pct = abs(ticket_cliente - ticket_mercado) / ticket_mercado if ticket_mercado > 0 else 1
        
        # Score de fit: 1.0 se dentro do range, 0 se fora (conforme Excel v8)
        score_fit = 1.0 if diff_pct <= range_pct else 0.0
        
        # Score final ponderado
        score_final = (score_mercado * 0.7) + (score_fit * 0.3)
        
        return score_final
    
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
        # Garantir que estamos pegando o faturamento_3m corretamente
        faturamento_3m = float(self.cliente_data.get('faturamento_3m', 0))
        faturamento_6m_projetado = faturamento_3m * 2
        
        if mercado_6m > 0:
            return (faturamento_6m_projetado / mercado_6m) * 100
        return 0.0
    
    def gerar_ranking(self, categoria: str = None) -> pd.DataFrame:
        """Gera ranking de subcategorias. Se categoria for None, gera de todas."""
        if not self.mercado_subcategorias:
            return pd.DataFrame()
        
        ranking_data = []
        
        categorias_para_processar = [categoria] if categoria else list(self.mercado_subcategorias.keys())
        
        for cat in categorias_para_processar:
            if cat in self.mercado_subcategorias:
                for subcat in self.mercado_subcategorias[cat]:
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
        """Simula cenários de crescimento para uma subcategoria de uma categoria"""
        if categoria not in self.mercado_subcategorias:
            return {}
            
        subcat_data = next((s for s in self.mercado_subcategorias[categoria] if s['subcategoria'] == subcategoria), None)
        
        if not subcat_data:
            return {}
        
        mercado_6m = subcat_data['faturamento_6m']
        ticket_usado = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        margem = self.cliente_data.get('margem', 0)
        # Faturamento atual do cliente (3 meses) -> Projetar para 6 meses para comparação justa
        faturamento_cliente_3m = float(self.cliente_data.get('faturamento_3m', 0))
        faturamento_atual_6m = faturamento_cliente_3m * 2
        
        # Usar shares customizados se fornecidos, senão usar padrão
        if custom_shares:
            cenarios = custom_shares
        else:
            cenarios = {
                'Conservador': {'share_alvo': 0.002, 'label': '0,2%'},
                'Provável': {'share_alvo': 0.005, 'label': '0,5%'},
                'Otimista': {'share_alvo': 0.010, 'label': '1,0%'}
            }
        
        resultados = []
        
        for nome, config in cenarios.items():
            share_val = config['share_alvo']
            receita_projetada = mercado_6m * share_val
            lucro_projetado = receita_projetada * margem
            
            # Delta é a Receita Adicional (O que vamos ganhar ALÉM do que já temos)
            delta = receita_projetada - faturamento_atual_6m
            
            # Cálculo de crescimento: Quanto a receita projetada representa de aumento sobre a atual
            crescimento_pct = 0
            if faturamento_atual_6m > 0:
                crescimento_pct = (delta / faturamento_atual_6m) * 100
            elif receita_projetada > 0:
                crescimento_pct = 100.0

            resultados.append({
                'Cenário': nome,
                'Share Alvo': config.get('label', f"{share_val*100:.2f}%"),
                'Ticket Usado': ticket_usado,
                'Receita Projetada 6M': receita_projetada,
                'Lucro Projetado 6M': lucro_projetado,
                'Delta vs Atual': delta,
                'Crescimento (%)': crescimento_pct
            })
        
        return {
            'cenarios': pd.DataFrame(resultados),
            'mercado_6m': mercado_6m,
            'ticket_mercado': subcat_data['ticket_medio'],
            'share_atual': self.calcular_share_atual(mercado_6m)
        }
    
    def get_mercado_categoria_df(self, categoria: str) -> pd.DataFrame:
        """Retorna DataFrame com dados de mercado de uma categoria específica"""
        if categoria not in self.mercado_categoria:
            return pd.DataFrame()
        return pd.DataFrame(self.mercado_categoria[categoria])
    
    def remover_mercado_categoria(self, categoria):
        if categoria in self.mercado_categoria:
            del self.mercado_categoria[categoria]
        if categoria in self.mercado_subcategorias:
            del self.mercado_subcategorias[categoria]

    def remover_periodo_categoria(self, categoria, periodo):
        if categoria in self.mercado_categoria:
            self.mercado_categoria[categoria] = [
                item for item in self.mercado_categoria[categoria]
                if item['periodo'] != periodo
            ]
            # Se não sobrar nenhum período, removemos a categoria
            if not self.mercado_categoria[categoria]:
                self.remover_mercado_categoria(categoria)

    def remover_mercado_subcategoria(self, categoria, subcategoria_nome):
        if categoria in self.mercado_subcategorias:
            self.mercado_subcategorias[categoria] = [
                s for s in self.mercado_subcategorias[categoria] 
                if s['subcategoria'] != subcategoria_nome
            ]

    def editar_mercado_categoria(self, categoria_antiga, categoria_nova, periodo, faturamento, unidades):
        if categoria_antiga != categoria_nova:
            if categoria_antiga in self.mercado_categoria:
                self.mercado_categoria[categoria_nova] = self.mercado_categoria.pop(categoria_antiga)
            if categoria_antiga in self.mercado_subcategorias:
                self.mercado_subcategorias[categoria_nova] = self.mercado_subcategorias.pop(categoria_antiga)
        
        if categoria_nova in self.mercado_categoria:
            for item in self.mercado_categoria[categoria_nova]:
                if item['periodo'] == periodo:
                    item['faturamento'] = faturamento
                    item['unidades'] = unidades
                    item['ticket_medio'] = faturamento / unidades if unidades > 0 else 0

    def editar_mercado_subcategoria(self, categoria, sub_antiga, sub_nova, faturamento_6m, unidades_6m):
        if categoria in self.mercado_subcategorias:
            for sub in self.mercado_subcategorias[categoria]:
                if sub['subcategoria'] == sub_antiga:
                    sub['subcategoria'] = sub_nova
                    sub['faturamento_6m'] = faturamento_6m
                    sub['unidades_6m'] = unidades_6m
                    sub['ticket_medio'] = faturamento_6m / unidades_6m if unidades_6m > 0 else 0

    def calcular_tendencia(self, categoria: str) -> Dict:
        """Calcula a tendência de crescimento e faz projeção para os próximos 3 meses"""
        if categoria not in self.mercado_categoria or len(self.mercado_categoria[categoria]) < 2:
            return {"tendencia": "Estável", "crescimento_mensal": 0, "projecao_3m": 0}
            
        df = pd.DataFrame(self.mercado_categoria[categoria])
        # Ordenar por período (assumindo formato Jan/25, Fev/25...)
        # Para simplificar, vamos usar a ordem de inserção ou tentar converter
        df['faturamento'] = pd.to_numeric(df['faturamento'])
        
        # Cálculo de crescimento médio mensal
        df['pct_change'] = df['faturamento'].pct_change()
        crescimento_medio = df['pct_change'].mean()
        
        ult_faturamento = df['faturamento'].iloc[-1]
        projecao = ult_faturamento * (1 + crescimento_medio) ** 3
        
        tendencia = "Alta" if crescimento_medio > 0.02 else ("Baixa" if crescimento_medio < -0.02 else "Estável")
        
        return {
            "tendencia": tendencia,
            "crescimento_mensal": crescimento_medio * 100,
            "projecao_3m": projecao
        }

    def gerar_plano_acao(self, categoria: str = None) -> List[Dict]:
        """Gera recomendações estratégicas detalhadas e acionáveis"""
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
            prioridade = ""
            cor = ""
            
            # Determinar Prioridade e Cor
            if status == "FOCO":
                prioridade = "MÁXIMA (ESTRATÉGICO)"
                cor = "#FF4B4B" # Vermelho vibrante
            elif status == "OK":
                prioridade = "ALTA (OPORTUNIDADE)"
                cor = "#FFA421" # Laranja
            else:
                prioridade = "MÉDIA (MONITORAR)"
                cor = "#00D4FF" # Azul claro

            # 1. Análise de Preço (Ticket)
            if leitura == "Ticket OK":
                acoes.append(f"✅ **Preço Competitivo**: Seu ticket (R$ {ticket_cliente:,.2f}) está alinhado com o mercado (R$ {ticket_mercado:,.2f}).")
                if status == "FOCO":
                    acoes.append("🚀 **Ação**: Acelere o investimento em Ads (Publicidade) e garanta a profundidade de estoque.")
            elif "Aumentar" in leitura:
                diff = (ticket_mercado - ticket_cliente)
                acoes.append(f"⚠️ **Preço Defasado**: Seu ticket está R$ {diff:,.2f} ABAIXO da média do mercado.")
                acoes.append(f"💡 **Ação**: Você tem margem para subir o preço ou criar kits com maior valor agregado para aumentar o faturamento.")
            else:
                diff = (ticket_cliente - ticket_mercado)
                acoes.append(f"⚠️ **Preço Elevado**: Seu ticket está R$ {diff:,.2f} ACIMA da média do mercado.")
                acoes.append(f"💡 **Ação**: Avalie se o seu produto tem diferenciais que justifiquem o preço. Caso contrário, considere promoções agressivas para ganhar relevância.")

            # 2. Análise de Mercado
            if mercado > 1_000_000:
                acoes.append(f"💰 **Volume de Mercado**: Esta subcategoria movimenta R$ {mercado/1_000_000:.1f}M em 6 meses. É um oceano de oportunidades.")
            
            # 3. Sugestão de Share
            if status == "FOCO":
                acoes.append("🎯 **Meta**: Foque em atingir pelo menos 1% de share nesta subcategoria nos próximos 90 dias.")

            plano.append({
                "Subcategoria": subcat,
                "Prioridade": prioridade,
                "Ações": acoes,
                "Cor": cor,
                "Score": score
            })
            
        return plano

    def clear_data(self):
        """Limpa todos os dados"""
        self.cliente_data = {}
        self.mercado_categoria = {}
        self.mercado_subcategorias = {}
