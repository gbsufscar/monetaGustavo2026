#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste rápido do fluxo de backtests"""

from modelo.backtestes import rodar_backtestes
from datetime import date, timedelta

# Simular parâmetros do app
acoes_selecionadas = ['PETR4.SA', 'VALE3.SA']
data_inicial_bt = date(2023, 1, 1)
data_final_bt = date(2023, 12, 31)
intervalo = 'd'
cotacoes_anteriores = 100
cotacoes_segurar = 20
maiores_medias = 2
qtd_bebados = 5
simbolo_index = 'BOVA11.SA'

print("[TEST] Iniciando teste de backtests...")

try:
    resultados = rodar_backtestes(
        acoes_selecionadas=acoes_selecionadas,
        data_inicial_bt=data_inicial_bt,
        data_final_bt=data_final_bt,
        intervalo=intervalo,
        cotacoes_anteriores=cotacoes_anteriores,
        cotacoes_segurar=cotacoes_segurar,
        maiores_medias=maiores_medias,
        qtd_bebados=qtd_bebados,
        simbolo_index=simbolo_index
    )
    
    print(f"[OK] Backtests concluído com sucesso")
    print(f"[OK] Estrutura de retorno válida")
    
    # Validar estrutura
    assert isinstance(resultados, dict), "Resultado deve ser dict"
    assert "acumulados" in resultados, "Falta 'acumulados' nos resultados"
    assert isinstance(resultados["acumulados"], dict), "'acumulados' deve ser dict"
    assert "moneta" in resultados["acumulados"], "Falta 'moneta' em acumulados"
    assert "index" in resultados["acumulados"], "Falta 'index' em acumulados"
    assert "bebados" in resultados["acumulados"], "Falta 'bebados' em acumulados"
    
    print("[OK] Estrutura de resultados validada!")
    print("[OK] Teste completado com sucesso ✓")
    
except Exception as e:
    print(f"[ERROR] Erro durante teste: {e}")
    import traceback
    traceback.print_exc()
