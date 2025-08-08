import streamlit as st
import time
import math
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

-------------------------

Configuração da página

-------------------------

st.set_page_config(page_title="Football Studio AI Predictor v2", layout="wide")

Mapas

emoji_map = {'C': '🔴', 'V': '🔵', 'E': '🟡'} color_name = {'C': 'Vermelho', 'V': 'Azul', 'E': 'Empate'}

Estado inicial

if 'history' not in st.session_state: # Mantemos o histórico com o formato do cassino: índice 0 = mais recente (à esquerda) st.session_state.history = []  # cada item: {'result':'C'|'V'|'E', 'timestamp': float}

if 'analysis' not in st.session_state: st.session_state.analysis = {}

-------------------------

Utilitários

-------------------------

def get_color_name(c: str) -> str: return color_name.get(c, '')

def weighted_counts(results: List[str], decay: float = 0.85) -> Dict[str, float]: """Conta resultados com peso exponencial decrescente (mais recente tem peso 1). decay em (0,1): quanto menor, mais forte o peso nas jogadas recentes.""" w = 1.0 counts = {'C': 0.0, 'V': 0.0, 'E': 0.0} for r in results: counts[r] += w w *= decay return counts

def shannon_entropy(results: List[str]) -> float: if not results: return 0.0 total = len(results) freq = Counter(results) ent = 0.0 for _, c in freq.items(): p = c / total ent -= p * math.log2(p) return ent  # em bits

def get_streaks(results: List[str]) -> Tuple[int, Tuple[str, int]]: """Retorna (max_streak, (current_color, current_length)) onde current refere-se ao streak atual (mais recente).""" if not results: return 0, ('', 0) # max streak max_streak = 1 cur = 1 for i in range(1, len(results)): if results[i] == results[i-1]: cur += 1 max_streak = max(max_streak, cur) else: cur = 1 # current streak (começando do índice 0 - mais recente) cur_color = results[0] cur_len = 1 for i in range(1, len(results)): if results[i] == cur_color: cur_len += 1 else: break return max_streak, (cur_color, cur_len)

def detect_reversal_patterns(results: List[str]) -> List[Dict]: """Detecta padrões onde uma sequência é seguida por uma inversão/queima deliberada. Ex: C C C V (inversão), ou alternância que é intencionalmente quebrada. Retorna lista de ocorrências com posição relativa (0 = mais recente).""" patterns = [] # analisamos janelas móveis pequenas for width in (4, 5, 6): if len(results) < width + 1: continue for i in range(0, len(results) - width): # janelas com estabilidade seguida de quebra window = results[i:i+width] next_idx = i + width next_val = results[next_idx] if next_idx < len(results) else None # estabilidade: pelo menos 3 dos 1os width serem iguais e o próximo ser diferente if len(window) >= 3: most_common = Counter(window).most_common(1)[0] if most_common[1] >= 3 and next_val and next_val != most_common[0]: patterns.append({'type': 'reversal', 'position': i, 'base': most_common[0], 'break': next_val, 'description': f"Reversão após estabilidade de {most_common[1]}x {get_color_name(most_common[0])} (pos {i})"}) # alternância seguida de anomalia if width >= 4: alt = all(window[j] != window[j+1] for j in range(len(window)-1)) if alt and next_val and next_val == window[0]: patterns.append({'type': 'reversal-alt', 'position': i, 'description': f"Alternância seguida de repetição atípica (pos {i})"}) return patterns

def detect_anchor_anchors(results: List[str]) -> List[Dict]: """Detecta quando empates (E) aparecem estrategicamente como 'âncoras' para resetar padrões.""" patt = [] for i, val in enumerate(results): if val == 'E': # verificar vizinhança: se antes e depois existir mudança significativa before = results[i+1:i+4]  # mais antigas after = results[0:i]  # mais recentes até o empate # se houver alternância ou padrão antes e depois um reset, considerar âncora if before and after: # padrão em before (ex: repetição) e depois diferente if len(set(before)) == 1 and (len(after) == 0 or after[0] != before[0]): patt.append({'type': 'empate-ancora', 'position': i, 'description': f"Empate atuando como âncora em pos {i}"}) return patt

def sliding_window_patterns(results: List[str]) -> List[Dict]: patterns = [] n = len(results) # windows variadas for w in (4, 6, 9): if n < w: continue for i in range(0, n - w + 1): window = results[i:i+w] # 2x2-like em janelas maiores (padrões repetidos de pares) for j in range(0, w-3): a, b, c, d = window[j], window[j+1], window[j+2], window[j+3] if a == b and c == d and a != c: patterns.append({'type': '2x2', 'position': i+j, 'description': f"Padrão 2x2 detectado pos {i+j}"}) # clusters de empates if window.count('E') >= max(2, w//4): patterns.append({'type': 'empate-cluster', 'position': i, 'description': f"Cluster de empates na janela {i}-{i+w-1}"}) # padrões camuflados: pequena repetição dentro de alternância # ex: C V C C V C -> detectamos subpadrões que se repetem subs = defaultdict(int) for k in range(0, w-2): sub = ''.join(window[k:k+3]) subs[sub] += 1 for sub, cnt in subs.items(): if cnt >= 2: patterns.append({'type': 'camuflado', 'pattern': sub, 'position': i, 'description': f"Padrão camuflado '{sub}' repetido na janela {i}-{i+w-1}"}) return patterns

-------------------------

Avaliação do nível de manipulação (1-9)

-------------------------

def get_manipulation_level(data: List[Dict]) -> Tuple[int, List[str]]: results = [d['result'] for d in data] if not results: return 1, []

# pesos temporais
weighted = weighted_counts(results, decay=0.85)
total_weight = sum(weighted.values())
# normalizar
w_c = weighted['C'] / total_weight
w_v = weighted['V'] / total_weight
w_e = weighted['E'] / total_weight

ent = shannon_entropy(results)
max_streak, (cur_color, cur_len) = get_streaks(results)

manipulation_signals = []
score = 0.0

# sinal 1: empates elevados nos últimos resultados (peso alto)
if w_e > 0.20:
    score += min(35, w_e * 100)
    manipulation_signals.append(f"Empates recentes elevados ({w_e:.0%})")

# sinal 2: domínio pesado de uma cor (com peso recente)
if w_c > 0.65:
    score += 25
    manipulation_signals.append(f"Domínio recente de {get_color_name('C')} ({w_c:.0%})")
if w_v > 0.65:
    score += 25
    manipulation_signals.append(f"Domínio recente de {get_color_name('V')} ({w_v:.0%})")

# sinal 3: streak atual longo
if cur_len >= 4 and cur_color != 'E':
    score += min(30, (cur_len - 3) * 8)
    manipulation_signals.append(f"Sequência atual longa ({cur_len}x {get_color_name(cur_color)})")

# sinal 4: reversões detectadas
reversals = detect_reversal_patterns(results)
if reversals:
    score += min(30, len(reversals) * 8)
    manipulation_signals.append(f"Reversões detectadas ({len(reversals)})")

# sinal 5: âncoras (empates usados estrategicamente)
anchors = detect_anchor_anchors(results)
if anchors:
    score += 15
    manipulation_signals.append(f"Empates como âncoras ({len(anchors)})")

# sinal 6: baixa entropia (muito ordenado) ou entropia anormalmente alta (caos controlado)
# ent varia de 0 (determinístico) até log2(3) ~= 1.585 (maior incerteza)
if ent < 0.8:
    score += 15
    manipulation_signals.append(f"Baixa entropia ({ent:.2f})")
elif ent > 1.4:
    score += 10
    manipulation_signals.append(f"Alta entropia ({ent:.2f})")

# sinal 7: padrões camuflados / repetidos
camu = sliding_window_patterns(results)
camu_count = sum(1 for p in camu if p['type'] in ('camuflado', '2x2'))
if camu_count:
    score += min(20, camu_count * 4)
    manipulation_signals.append(f"Padrões camuflados/2x2 ({camu_count})")

# sinal 8: alternância quase perfeita (pode indicar manipulação para embaralhar)
alternancias = sum(1 for i in range(1, len(results)) if results[i] != results[i-1])
alt_rate = alternancias / max(1, (len(results)-1))
if alt_rate > 0.85 and len(results) >= 8:
    score += 15
    manipulation_signals.append("Alternância muito alta")

# normalizar score e converter em level 1-9
# score pode variar amplamente; mapeamos para 1..9
level = min(max(int(score // 10) + 1, 1), 9)

# garantimos que níveis 8-9 só ocorram com sinais múltiplos fortes
strong = sum(1 for s in manipulation_signals if any(k in s for k in ['Sequência', 'Domínio', 'Reversões', 'Empates', 'Baixa entropia']))
if level >= 8 and strong < 2:
    level = 7

return level, manipulation_signals

-------------------------

Predição multi-caminho com probabilidades

-------------------------

def predict_next(data: List[Dict], level: int) -> Dict: results = [d['result'] for d in data] n = len(results) if n == 0: return {'probs': {'C': 33, 'V': 33, 'E': 34}, 'top': None, 'confidence': 0}

# Pesos e sinais
weighted = weighted_counts(results, decay=0.88)
w_total = sum(weighted.values())
p_c = weighted['C'] / w_total
p_v = weighted['V'] / w_total
p_e = weighted['E'] / w_total

# baseline probs (convertendo para porcentagem)
base = {'C': p_c, 'V': p_v, 'E': p_e}

# ajustar por streak atual (preferir quebra quando streak longo)
_, (cur_color, cur_len) = get_streaks(results)
probs = base.copy()

# Se streak atual >=4 -> maior probabilidade de quebra; o break tende a ser o opp color ou empate
if cur_len >= 4 and cur_color in ('C', 'V'):
    opp = 'V' if cur_color == 'C' else 'C'
    probs[opp] += 0.30 * (cur_len - 3)  # aumenta chance do oposto
    probs['E'] += 0.10 * (cur_len - 3)
    probs[cur_color] *= max(0.2, 1 - 0.25 * (cur_len - 3))

# Se empates recentes altos, aumentar prob de empate
last10 = results[:10]
if last10.count('E') >= 2:
    probs['E'] += 0.25
    probs['C'] *= 0.8
    probs['V'] *= 0.8

# Se reversões detectadas recentemente, aumentar prob de repeats curtas
revs = detect_reversal_patterns(results)
if revs:
    # modera distribuição para favorecer repetições curtas e quebras planejadas
    probs = {k: v * 1.0 for k, v in probs.items()}
    probs['E'] += 0.08 * len(revs)

# Normalizar e converter em porcentagem
total = sum(probs.values())
probs = {k: max(0.0, v/total) for k, v in probs.items()}
probs_pct = {k: round(v*100) for k, v in probs.items()}

# confiança: combinação do top prob e influência do level (quanto maior o level, mais cautela)
top_color = max(probs, key=probs.get)
top_prob = probs[top_color]
# confiança inicial baseada na diferença entre top e segundo
sorted_probs = sorted(probs.values(), reverse=True)
gap = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else sorted_probs[0]
confidence = int(min(95, max(30, top_prob * 100 + gap * 50 - level * 3)))

return {'probs': probs_pct, 'top': top_color, 'confidence': confidence}

-------------------------

Detecta brechas/risco

-------------------------

def detect_breach(data: List[Dict], level: int, manipulation_signals: List[str]) -> bool: results = [d['result'] for d in data] # Regra 1: nível alto -> consideramos brecha provável if level >= 7: return True # Regra 2: empates foram usados como âncora e aparecem recentemente if any('Empates' in s or 'âncora' in s.lower() for s in manipulation_signals): return True # Regra 3: baixa entropia e repetição de padrões camuflados ent = shannon_entropy(results) camu = sliding_window_patterns(results) camu_sign = any(p['type'] in ('camuflado', '2x2') for p in camu) if ent < 0.7 and camu_sign: return True return False

-------------------------

Análise combinada

-------------------------

def analyze(): data = st.session_state.history if len(data) < 5: st.session_state.analysis = {} return

level, manipulation_signals = get_manipulation_level(data)
results = [d['result'] for d in data]
patterns = []
patterns.extend(detect_reversal_patterns(results))
patterns.extend(detect_anchor_anchors(results))
patterns.extend(sliding_window_patterns(results))

pred = predict_next(data, level)
breach = detect_breach(data, level, manipulation_signals)

recommendation = 'Aguardar'
# regra de recomendação: se top prob > 60% e sem brecha e level baixo-medio
if pred['top'] and pred['probs'][pred['top']] >= 60 and not breach and level <= 5:
    recommendation = 'Apostar'
# se top entre 50-60 -> só se level <=4
elif pred['top'] and pred['probs'][pred['top']] >= 50 and not breach and level <= 4:
    recommendation = 'Apostar'

st.session_state.analysis = {
    'manipulation_level': level,
    'manipulation_signals': manipulation_signals,
    'patterns': patterns,
    'prediction': pred,
    'breach_detected': breach,
    'recommendation': recommendation,
    'last_updated': time.time()
}

-------------------------

Ações do usuário (inserir/reset)

-------------------------

def add_result(result: str): # inserimos no índice 0 para manter formato do cassino (mais recente à esquerda) st.session_state.history.insert(0, {'result': result, 'timestamp': time.time()}) # limitamos histórico para 90 resultados (9 cols x 10 linhas) if len(st.session_state.history) > 90: st.session_state.history = st.session_state.history[:90] analyze()

def reset(): st.session_state.history = [] st.session_state.analysis = {}

-------------------------

Interface Streamlit

-------------------------

st.title("🎯 Football Studio - IA Avançada (v2)") col1, col2 = st.columns([2, 1])

with col1: st.subheader("🎮 Inserir Resultado (formato cassino: mais recente à ESQUERDA)") c1, c2, c3 = st.columns(3) with c1: st.button("🔴 Vermelho (C)", on_click=add_result, args=("C",)) with c2: st.button("🔵 Azul (V)", on_click=add_result, args=("V",)) with c3: st.button("🟡 Empate (E)", on_click=add_result, args=("E",)) st.button("🔄 Resetar Histórico", on_click=reset)

# Exibir histórico: mais recente à esquerda, 9 por linha
st.subheader("📊 Histórico (mais recente à esquerda)")
if st.session_state.history:
    hist = st.session_state.history  # já tem ordem desejada
    # mostramos até 10 linhas de 9 resultados
    rows = [hist[i:i+9] for i in range(0, min(len(hist), 90), 9)]
    for row in rows:
        st.markdown("**" + " ".join(emoji_map[d['result']] for d in row) + "**")
    st.write(f"Total registrado: {len(hist)}")

    # Estatísticas e visualização rápida
    st.subheader("📈 Estatísticas Rápidas")
    total = len(hist)
    freq = Counter([d['result'] for d in hist])
    st.write(f"🔢 Distribuição (mais recente ponderado): C={freq['C']} V={freq['V']} E={freq['E']}")
else:
    st.info("Nenhum resultado inserido ainda.")

with col2: st.subheader("📈 Análise em Tempo Real (avançada)") analysis = st.session_state.analysis if analysis: st.write(f"🔢 Nível de Manipulação: {analysis['manipulation_level']}/9") if analysis['manipulation_signals']: st.write("⚠️ Sinais de Manipulação Detectados:") for s in analysis['manipulation_signals']: st.write(f"- {s}")

# Predição multi-caminho
    pred = analysis['prediction']
    probs = pred['probs']
    st.write("🎯 Previsão multi-caminho:")
    st.write(f"- {emoji_map['C']} Vermelho: {probs['C']}%")
    st.write(f"- {emoji_map['V']} Azul: {probs['V']}%")
    st.write(f"- {emoji_map['E']} Empate: {probs['E']}%")
    st.write(f"💡 Top: {emoji_map.get(pred['top'], '...')}  Confiança: {pred['confidence']}%")

    st.write("🔎 Padrões detectados:")
    shown = set()
    for p in analysis['patterns']:
        desc = p.get('description', str(p))
        if desc not in shown:
            st.write(f"- {desc}")
            shown.add(desc)

    st.write(f"⚠️ Brecha detectada: {'Sim' if analysis['breach_detected'] else 'Não'}")
    st.write(f"✅ Recomendação: {analysis['recommendation']}")
else:
    st.write("Aguardando mais dados para análise (mínimo 5 resultados)...")

Ao carregar a página, podemos analisar automaticamente se já houver dados

if st.session_state.history and not st.session_state.analysis: analyze()

Rodapé com dicas rápidas

st.markdown("---") st.caption("Dicas: o algoritmo dá mais peso às jogadas recentes, detecta reversões e empates-âncora, e gera probabilidades para cada cor. Níveis 7-9 indicam sinais fortes de manipulação — agir com cautela.")

