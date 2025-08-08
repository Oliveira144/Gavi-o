import streamlit as st
import time
import math
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

# -------------------------
# Configuração da página
# -------------------------
st.set_page_config(page_title="Football Studio AI Predictor v2", layout="wide")

# Mapas
emoji_map = {'C': '🔴', 'V': '🔵', 'E': '🟡'}
color_name = {'C': 'Vermelho', 'V': 'Azul', 'E': 'Empate'}

# Estado inicial
if 'history' not in st.session_state:
    st.session_state.history = []  # Histórico: índice 0 = mais recente (à esquerda)
if 'analysis' not in st.session_state:
    st.session_state.analysis = {}

# -------------------------
# Utilitários
# -------------------------

def get_color_name(c: str) -> str:
    return color_name.get(c, '')

def weighted_counts(results: List[str], decay: float = 0.85) -> Dict[str, float]:
    w = 1.0
    counts = {'C': 0.0, 'V': 0.0, 'E': 0.0}
    for r in results:
        counts[r] += w
        w *= decay
    return counts

def shannon_entropy(results: List[str]) -> float:
    if not results:
        return 0.0
    total = len(results)
    freq = Counter(results)
    ent = 0.0
    for _, c in freq.items():
        p = c / total
        ent -= p * math.log2(p)
    return ent

def get_streaks(results: List[str]) -> Tuple[int, Tuple[str, int]]:
    if not results:
        return 0, ('', 0)
    max_streak = 1
    cur = 1
    for i in range(1, len(results)):
        if results[i] == results[i-1]:
            cur += 1
            max_streak = max(max_streak, cur)
        else:
            cur = 1
    cur_color = results[0]
    cur_len = 1
    for i in range(1, len(results)):
        if results[i] == cur_color:
            cur_len += 1
        else:
            break
    return max_streak, (cur_color, cur_len)

def detect_reversal_patterns(results: List[str]) -> List[Dict]:
    patterns = []
    for width in (4, 5, 6):
        if len(results) < width + 1:
            continue
        for i in range(len(results) - width):
            window = results[i:i+width]
            next_idx = i + width
            next_val = results[next_idx] if next_idx < len(results) else None
            if len(window) >= 3:
                most_common = Counter(window).most_common(1)[0]
                if most_common[1] >= 3 and next_val and next_val != most_common[0]:
                    patterns.append({'type': 'reversal', 'position': i, 'base': most_common[0], 'break': next_val,
                                     'description': f"Reversão após estabilidade de {most_common[1]}x {get_color_name(most_common[0])} (pos {i})"})
            if width >= 4:
                alt = all(window[j] != window[j+1] for j in range(len(window)-1))
                if alt and next_val and next_val == window[0]:
                    patterns.append({'type': 'reversal-alt', 'position': i,
                                     'description': f"Alternância seguida de repetição atípica (pos {i})"})
    return patterns

def detect_anchor_anchors(results: List[str]) -> List[Dict]:
    patt = []
    for i, val in enumerate(results):
        if val == 'E':
            before = results[i+1:i+4]
            after = results[0:i]
            if before and after:
                if len(set(before)) == 1 and (len(after) == 0 or after[0] != before[0]):
                    patt.append({'type': 'empate-ancora', 'position': i, 'description': f"Empate atuando como âncora em pos {i}"})
    return patt

def sliding_window_patterns(results: List[str]) -> List[Dict]:
    patterns = []
    n = len(results)
    for w in (4, 6, 9):
        if n < w:
            continue
        for i in range(n - w + 1):
            window = results[i:i+w]
            for j in range(w-3):
                a, b, c, d = window[j], window[j+1], window[j+2], window[j+3]
                if a == b and c == d and a != c:
                    patterns.append({'type': '2x2', 'position': i+j, 'description': f"Padrão 2x2 detectado pos {i+j}"})
            if window.count('E') >= max(2, w//4):
                patterns.append({'type': 'empate-cluster', 'position': i, 'description': f"Cluster de empates na janela {i}-{i+w-1}"})
            subs = defaultdict(int)
            for k in range(w-2):
                sub = ''.join(window[k:k+3])
                subs[sub] += 1
            for sub, cnt in subs.items():
                if cnt >= 2:
                    patterns.append({'type': 'camuflado', 'pattern': sub, 'position': i,
                                     'description': f"Padrão camuflado '{sub}' repetido na janela {i}-{i+w-1}"})
    return patterns

def get_manipulation_level(data: List[Dict]) -> Tuple[int, List[str]]:
    results = [d['result'] for d in data]
    if not results:
        return 1, []

    weighted = weighted_counts(results, decay=0.85)
    total_weight = sum(weighted.values())
    w_c = weighted['C'] / total_weight
    w_v = weighted['V'] / total_weight
    w_e = weighted['E'] / total_weight

    ent = shannon_entropy(results)
    max_streak, (cur_color, cur_len) = get_streaks(results)

    manipulation_signals = []
    score = 0.0

    if w_e > 0.20:
        score += min(35, w_e * 100)
        manipulation_signals.append(f"Empates recentes elevados ({w_e:.0%})")

    if w_c > 0.65:
        score += 25
        manipulation_signals.append(f"Domínio recente de {get_color_name('C')} ({w_c:.0%})")
    if w_v > 0.65:
        score += 25
        manipulation_signals.append(f"Domínio recente de {get_color_name('V')} ({w_v:.0%})")

    if cur_len >= 4 and cur_color != 'E':
        score += min(30, (cur_len - 3) * 8)
        manipulation_signals.append(f"Sequência atual longa ({cur_len}x {get_color_name(cur_color)})")

    reversals = detect_reversal_patterns(results)
    if reversals:
        score += min(30, len(reversals) * 8)
        manipulation_signals.append(f"Reversões detectadas ({len(reversals)})")

    anchors = detect_anchor_anchors(results)
    if anchors:
        score += 15
        manipulation_signals.append(f"Empates como âncoras ({len(anchors)})")

    if ent < 0.8:
        score += 15
        manipulation_signals.append(f"Baixa entropia ({ent:.2f})")
    elif ent > 1.4:
        score += 10
        manipulation_signals.append(f"Alta entropia ({ent:.2f})")

    camu = sliding_window_patterns(results)
    camu_count = sum(1 for p in camu if p['type'] in ('camuflado', '2x2'))
    if camu_count:
        score += min(20, camu_count * 4)
        manipulation_signals.append(f"Padrões camuflados/2x2 ({camu_count})")

    alternancias = sum(1 for i in range(1, len(results)) if results[i] != results[i-1])
    alt_rate = alternancias / max(1, (len(results)-1))
    if alt_rate > 0.85 and len(results) >= 8:
        score += 15
        manipulation_signals.append("Alternância muito alta")

    level = min(max(int(score // 10) + 1, 1), 9)

    strong = sum(1 for s in manipulation_signals if any(k in s for k in ['Sequência', 'Domínio', 'Reversões', 'Empates', 'Baixa entropia']))
    if level >= 8 and strong < 2:
        level = 7

    return level, manipulation_signals

def predict_next(data: List[Dict], level: int) -> Dict:
    results = [d['result'] for d in data]
    if not results:
        return {'probs': {'C': 33, 'V': 33, 'E': 34}, 'top': None, 'confidence': 0}

    weighted = weighted_counts(results, decay=0.88)
    w_total = sum(weighted.values())
    p_c = weighted['C'] / w_total
    p_v = weighted['V'] / w_total
    p_e = weighted['E'] / w_total

    base = {'C': p_c, 'V': p_v, 'E': p_e}
    _, (cur_color, cur_len) = get_streaks(results)
    probs = base.copy()

    if cur_len >= 4 and cur_color in ('C', 'V'):
        opp = 'V' if cur_color == 'C' else 'C'
        probs[opp] += 0.30 * (cur_len - 3)
        probs['E'] += 0.10 * (cur_len - 3)
        probs[cur_color] *= max(0.2, 1 - 0.25 * (cur_len - 3))

    last10 = results[:10]
    if last10.count('E') >= 2:
        probs['E'] += 0.25
        probs['C'] *= 0.8
        probs['V'] *= 0.8

    revs = detect_reversal_patterns(results)
    if revs:
        probs = {k: v * 1.0 for k, v in probs.items()}
        probs['E'] += 0.08 * len(revs)

    total = sum(probs.values())
    probs = {k: max(0.0, v/total) for k, v in probs.items()}
    probs_pct = {k: round(v*100) for k, v in probs.items()}

    top_color = max(probs, key=probs.get)
    top_prob = probs[top_color]
    sorted_probs = sorted(probs.values(), reverse=True)
    gap = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else sorted_probs[0]
    confidence = int(min(95, max(30, top_prob * 100 + gap * 50 - level * 3)))

    return {'probs': probs_pct, 'top': top_color, 'confidence': confidence}

def detect_breach(data: List[Dict], level: int, manipulation_signals: List[str]) -> bool:
    results = [d['result'] for d in data]
    if level >= 7:
        return True
    if any('Empates' in s or 'âncora' in s.lower() for s in manipulation_signals):
        return True
    ent = shannon_entropy(results)
    camu = sliding_window_patterns(results)
    camu_sign = any(p['type'] in ('camuflado', '2x2') for p in camu)
    if ent < 0.7 and camu_sign:
        return True
    return False

def analyze():
    data = st.session_state.history
    if len(data) < 5:
        st.session_state.analysis = {}
        return

    level, manipulation_signals = get_manipulation_level(data)
    results = [d['result'] for d in data]
    patterns = []
    patterns.extend(detect_reversal_patterns(results))
    patterns.extend(detect_anchor_anchors(results))
    patterns.extend(sliding_window_patterns(results))

    pred = predict_next(data, level)
    breach = detect_breach(data, level, manipulation_signals)

    recommendation = 'Aguardar'
    if pred['top'] and pred['probs'][pred['top']] >= 60 and not breach and level <= 5:
        recommendation = 'Apostar'
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

def add_result(result: str):
    st.session_state.history.insert(0, {'result': result, 'timestamp': time.time()})
    if len(st.session_state.history) > 90:
        st.session_state.history = st.session_state.history[:90]
    analyze()

def reset():
    st.session_state.history = []
    st.session_state.analysis = {}

# -------------------------
# Interface Streamlit
# -------------------------

st.title("🎯 Football Studio - IA Avançada (v2)")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎮 Inserir Resultado (formato cassino: mais recente à ESQUERDA)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("🔴 Vermelho (C)", on_click=add_result, args=("C",))
    with c2:
        st.button("🔵 Azul (V)", on_click=add_result, args=("V",))
    with c3:
        st.button("🟡 Empate (E)", on_click=add_result, args=("E",))
    st.button("🔄 Resetar Histórico", on_click=reset)

    if st.session_state.history:
        st.subheader("📊 Histórico Completo (mais recente à esquerda)")
        hist = st.session_state.history
        for i in range(0, len(hist), 12):
            row = hist[i:i+12]
            st.markdown("**" + " ".join(emoji_map[d['result']] for d in row) + "**")
    else:
        st.info("Nenhum resultado inserido ainda.")

with col2:
    st.subheader("📈 Análise em Tempo Real")
    analysis = st.session_state.analysis
    if analysis:
        st.write(f"🔢 Nível de Manipulação: {analysis['manipulation_level']}/9")
        if analysis['manipulation_signals']:
            st.write("⚠️ Tipos de Manipulação Detectados:")
            for t in analysis['manipulation_signals']:
                st.write(f"- {t}")

        pred = analysis['prediction']
        probs = pred.get('probs', {})
        top = pred.get('top')
        confidence = pred.get('confidence')

        st.write(f"🎯 Previsão Principal: {emoji_map.get(top, '...')} ({confidence}%)")
        st.write("🎲 Probabilidades detalhadas:")
        st.write(f"🔴 Vermelho (C): {probs.get('C', 0)}%")
        st.write(f"🔵 Azul (V): {probs.get('V', 0)}%")
        st.write(f"🟡 Empate (E): {probs.get('E', 0)}%")

        st.write("🔎 Padrões Detectados:")
        unique_patterns = set()
        for p in analysis['patterns']:
            desc = p.get('description', '')
            if desc and desc not in unique_patterns:
                st.write(f"- {desc}")
                unique_patterns.add(desc)

        st.write(f"⚠️ Brecha Detectada: {'Sim' if analysis['breach_detected'] else 'Não'}")
        st.write(f"✅ Recomendação: {analysis['recommendation']}")
    else:
        st.info("Insira resultados para análise aparecer aqui.")
