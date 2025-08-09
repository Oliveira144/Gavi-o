import streamlit as st
import collections

# --- Configuração da página ---
st.set_page_config(
    page_title="Analisador Fantasmas de Padrões Football Studio",
    page_icon="🔮",
    layout="wide"
)

# --- Mapas ---
EMOJI_MAP = {'V': '🔴', 'A': '🔵', 'E': '🟡'}

# Mapeamento dos padrões com emojis explicativos
PADROES_INFO = {
    "Sequência Repetitiva": {
        "numero": "1",
        "emoji": "🔴",
        "descricao": "3 ou mais resultados iguais consecutivos dentro da janela."
    },
    "Sequência Repetitiva após quebra": {
        "numero": "1b",
        "emoji": "🔄",
        "descricao": "Sequência retomada após quebra dentro da janela."
    },
    "Padrão Alternado": {
        "numero": "2",
        "emoji": "🔵",
        "descricao": "Resultados alternados dentro da janela (ex: 🔴🔵🔴🔵)."
    },
    "Quebra de Padrão": {
        "numero": "3",
        "emoji": "⚠️",
        "descricao": "Mudança inesperada após padrão repetitivo dentro da janela."
    },
    "Empates Estratégicos": {
        "numero": "4",
        "emoji": "🟡",
        "descricao": "Empates ocorrendo dentro da janela; possível confusão proposital."
    },
    "Sequências Longas de Uma Cor": {
        "numero": "5",
        "emoji": "🔴",
        "descricao": "Sequência longa (>5) da mesma cor dentro da janela."
    },
    "Padrão de Dois ou Três Repetidos + Inversão": {
        "numero": "6",
        "emoji": "🔵",
        "descricao": "Ciclo 2-3 repetições seguido de inversão detectado na janela."
    },
    "Padrões de Ciclos Curtos": {
        "numero": "7",
        "emoji": "🔄",
        "descricao": "Repetição de blocos curtos detectada dentro da janela."
    },
    "Ruído Controlado / Quântico": {
        "numero": "8",
        "emoji": "❓",
        "descricao": "Janela com comportamento aparentemente aleatório/ruidoso."
    },
    "Falsos Padrões": {
        "numero": "9",
        "emoji": "🚫",
        "descricao": "Poucas repetições dentro da janela — alto ruído."
    },
    "Manipulação por Nível de Confiança": {
        "numero": "10",
        "emoji": "🔒",
        "descricao": "Empates + inversões frequentes dentro da janela — padrão sofisticado."
    }
}

# ----------------- Helpers -----------------
def oposto(cor):
    if cor == 'V': return 'A'
    if cor == 'A': return 'V'
    return None

def last_non_e_in_window(window):
    for r in reversed(window):
        if r != 'E':
            return r
    return None

# ----------------- Detecção (apenas sobre os últimos 18 resultados) -----------------
def detectar_padrao(historico):
    """
    Analisa APENAS os últimos 18 resultados (janela) e retorna:
    (padrao_chave, meta_dict)
    meta contém: confianca, window (lista), len_window, ultimo, ultimo_valido,
                 count_atual, cor_anterior, count_anterior, empates, inversoes, repeticoes_consecutivas,
                 predicted (quando aplicável)
    """
    meta = {
        "confianca": 0,
        "window": [],
        "len_window": 0,
        "ultimo": None,
        "ultimo_valido": None,
        "count_atual": 0,
        "cor_anterior": None,
        "count_anterior": 0,
        "empates": 0,
        "inversoes": 0,
        "repeticoes_consecutivas": 0,
        "predicted": None,
    }

    if not historico or len(historico) == 0:
        return "Sem padrão suficiente", meta

    # Janela: últimos 18 resultados (ou menos, se não houver 18)
    window = historico[-18:] if len(historico) >= 18 else historico[:]
    meta["window"] = window
    meta["len_window"] = len(window)

    # Contagens básicas na janela
    meta["empates"] = window.count('E')
    meta["inversoes"] = sum(
        1 for i in range(len(window)-1)
        if window[i] != window[i+1] and window[i] != 'E' and window[i+1] != 'E'
    )
    meta["repeticoes_consecutivas"] = sum(1 for i in range(len(window)-1) if window[i] == window[i+1])

    ultimo = window[-1]
    meta["ultimo"] = ultimo
    meta["ultimo_valido"] = last_non_e_in_window(window)

    # count_atual: sequência consecutiva no final da janela (apenas dentro da janela)
    count_atual = 0
    for i in range(len(window)-1, -1, -1):
        if window[i] == ultimo:
            count_atual += 1
        else:
            break
    meta["count_atual"] = count_atual

    # cor anterior e count anterior (dentro da janela)
    idx_prev = len(window) - 1 - count_atual
    cor_anterior = None
    count_anterior = 0
    if idx_prev >= 0:
        cor_anterior = window[idx_prev]
        for j in range(idx_prev, -1, -1):
            if window[j] == cor_anterior:
                count_anterior += 1
            else:
                break
    meta["cor_anterior"] = cor_anterior
    meta["count_anterior"] = count_anterior

    # --- Prioridade de padrões (todos avaliados *apenas* na janela) ---

    # 1) Sequências Longas de Uma Cor (maior prioridade)
    if meta["count_atual"] >= 5 and ultimo != 'E':
        meta["confianca"] = min(95, 50 + meta["count_atual"] * 6)
        return "Sequências Longas de Uma Cor", meta

    # 2) Manipulação por Nível de Confiança (empates + inversões frequentes na janela)
    if meta["empates"] >= 1 and meta["inversoes"] >= 2:
        meta["confianca"] = 85
        return "Manipulação por Nível de Confiança", meta

    # 3) Padrões de Ciclos Curtos (blocos 3|3 repetidos dentro da janela)
    for i in range(0, len(window) - 5):
        b1 = window[i:i+3]
        b2 = window[i+3:i+6]
        if b1 == b2 and 'E' not in b1:
            meta["confianca"] = 80
            meta["predicted"] = b1[0]  # próximo esperado do ciclo
            return "Padrões de Ciclos Curtos", meta

    # 4) Padrão de Dois ou Três Repetidos + Inversão
    for i in range(0, len(window) - 3):
        a, b, c, d = window[i], window[i+1], window[i+2], window[i+3]
        if a == b and c != b and d == c and a != 'E' and c != 'E':
            meta["confianca"] = 75
            meta["predicted"] = c
            return "Padrão de Dois ou Três Repetidos + Inversão", meta

    # 5) Sequência Repetitiva após quebra (tudo avaliado dentro da janela)
    if meta["count_atual"] >= 3 and meta["cor_anterior"] and meta["cor_anterior"] != ultimo and meta["count_anterior"] >= 2 and ultimo != 'E':
        meta["confianca"] = min(85, 45 + meta["count_atual"] * 8)
        return "Sequência Repetitiva após quebra", meta

    # 6) Sequência Repetitiva (3 ou mais) dentro da janela
    if meta["count_atual"] >= 3 and ultimo != 'E':
        meta["confianca"] = min(75, 40 + meta["count_atual"] * 6)
        return "Sequência Repetitiva", meta

    # 7) Padrão Alternado (considera apenas não-empates dentro da janela)
    non_e_window = [x for x in window if x != 'E']
    if len(non_e_window) >= 4:
        tail = non_e_window[-8:] if len(non_e_window) >= 8 else non_e_window
        alternado = True
        for i in range(len(tail)-1):
            if tail[i] == tail[i+1]:
                alternado = False
                break
        if alternado:
            meta["confianca"] = 60
            return "Padrão Alternado", meta

    # 8) Quebra de Padrão (2 iguais + inversão) dentro da janela
    if meta["count_atual"] == 2 and len(window) >= 3 and window[-3] != ultimo:
        meta["confianca"] = 55
        return "Quebra de Padrão", meta

    # 9) Empates Estratégicos (qualquer empate dentro da janela)
    if meta["empates"] >= 1:
        meta["confianca"] = 50
        return "Empates Estratégicos", meta

    # 10) Falsos Padrões (muito ruído na janela)
    if meta["repeticoes_consecutivas"] <= 1:
        meta["confianca"] = 40
        return "Falsos Padrões", meta

    # 11) Ruído Controlado / Quântico (fallback)
    meta["confianca"] = 35
    return "Ruído Controlado / Quântico", meta

# ----------------- Sugestão (usa exclusivamente o meta da janela) -----------------
def sugerir_aposta(padrao_chave, meta):
    ultimo = meta.get("ultimo")
    ultimo_valido = meta.get("ultimo_valido")
    conf = meta.get("confianca", 0)
    count_atual = meta.get("count_atual", 0)

    # Cada caso usa apenas dados da janela (meta)
    if padrao_chave == "Sequência Repetitiva após quebra":
        if ultimo and ultimo != 'E':
            return f"Aposte em {EMOJI_MAP[ultimo]}", f"Sequência retomada após quebra ({count_atual}x) dentro dos últimos {meta['len_window']} resultados. Confiança ≈ {conf}%."
        if ultimo_valido:
            return f"Aposte em {EMOJI_MAP[ultimo_valido]}", f"Última cor válida {EMOJI_MAP[ultimo_valido]} dentro da janela; aposte com cautela. Confiança ≈ {conf}%."
        return "Aguardar", "Últimos resultados são empates — aguardar cor válida dentro da janela."

    if padrao_chave == "Sequência Repetitiva":
        if ultimo_valido:
            opp = oposto(ultimo_valido)
            if opp:
                return f"Aposte em {EMOJI_MAP[opp]}", f"Sequência de {count_atual} detectada dentro da janela; sugerimos apostar no oposto esperando quebra — Confiança ≈ {conf}%."
        return "Aguardar", "Sequência identificada dentro da janela mas sem referência válida."

    if padrao_chave == "Padrão Alternado":
        if ultimo_valido:
            opp = oposto(ultimo_valido)
            return f"Aposte em {EMOJI_MAP[opp]}", f"Padrão alternado nos últimos {meta['len_window']} resultados — apostar no oposto do último válido. Confiança ≈ {conf}%."
        return "Sem sugestão clara", "Padrão alternado identificado na janela, mas sem referência válida."

    if padrao_chave == "Quebra de Padrão":
        if ultimo_valido:
            return f"Aposte em {EMOJI_MAP[ultimo_valido]}", f"Quebra de padrão detectada dentro da janela — apostar na continuidade do último (Confiança ≈ {conf}%)."
        return "Aguardar", "Quebra detectada mas sem cor válida na janela."

    if padrao_chave == "Empates Estratégicos":
        if ultimo_valido:
            return f"Aposte em {EMOJI_MAP[ultimo_valido]}", f"Empates detectados na janela — apostar na última cor válida {EMOJI_MAP[ultimo_valido]} com cautela. Confiança ≈ {conf}%."
        return "Aguardar", "Janela composta apenas por empates — aguardar cor válida."

    if padrao_chave == "Sequências Longas de Uma Cor":
        return "Aguardar", f"Sequência muito longa ({count_atual}x) dentro da janela — risco alto; evitar entradas (Confiança ≈ {conf}%)."

    if padrao_chave == "Padrão de Dois ou Três Repetidos + Inversão":
        pred = meta.get("predicted")
        if pred:
            return f"Aposte em {EMOJI_MAP[pred]}", f"Padrão 2/3 + inversão detectado na janela — sugerimos {EMOJI_MAP[pred]} (Confiança ≈ {conf}%)."
        if ultimo_valido:
            return f"Aposte em {EMOJI_MAP[ultimo_valido]}", f"Padrão detectado dentro da janela; usar última cor válida como referência (Confiança ≈ {conf}%)."
        return "Aguardar", "Padrão detectado mas sem referência confiável na janela."

    if padrao_chave == "Padrões de Ciclos Curtos":
        pred = meta.get("predicted")
        if pred:
            return f"Aposte em {EMOJI_MAP[pred]}", f"Ciclo curto detectado na janela; próxima esperada: {EMOJI_MAP[pred]} (Confiança ≈ {conf}%)."
        return "Aguardar", "Ciclo curto detectado mas predição não confiável."

    if padrao_chave == "Falsos Padrões":
        return "Evitar aposta", f"Alto ruído dentro da janela — evitar apostas (Confiança ≈ {conf}%)."

    if padrao_chave == "Manipulação por Nível de Confiança":
        return "Aposte com cautela", f"Padrão complexo (empates+inversões) na janela — apostar valores baixos e com gestão (Confiança ≈ {conf}%)."

    if padrao_chave == "Ruído Controlado / Quântico":
        return "Sem sugestão clara", "Janela muito ruidosa/aleatória — aguardar mais dados."

    if padrao_chave == "Sem padrão suficiente":
        return "Sem sugestão", "Histórico insuficiente para análise (janela vazia)."

    # fallback
    return "Sem sugestão clara", "Padrão não identificável com confiança suficiente."

# ----------------- UI -----------------
if 'historico' not in st.session_state:
    st.session_state.historico = collections.deque(maxlen=200)  # manter histórico maior, mas analisar só a janela de 18

st.title("🔮 Analisador — Análise com Janela de 18 Resultados (garantido)")
st.markdown("---")

st.markdown("### 1. Inserir Resultados")
st.write("Insira manualmente o resultado da rodada ou use os botões:")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🔴 Vitória da Casa", use_container_width=True):
        st.session_state.historico.append('V')
with col2:
    if st.button("🔵 Vitória do Visitante", use_container_width=True):
        st.session_state.historico.append('A')
with col3:
    if st.button("🟡 Empate", use_container_width=True):
        st.session_state.historico.append('E')
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Desfazer", help="Remove o último resultado", use_container_width=True):
        if st.session_state.historico:
            st.session_state.historico.pop()
with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Limpar Histórico", help="Apaga todo o histórico", use_container_width=True):
        st.session_state.historico.clear()

st.markdown("---")

st.markdown("### 2. Histórico de Resultados (exibindo os mais recentes primeiro)")
if st.session_state.historico:
    historico_list = list(st.session_state.historico)
    hist_emojis = [EMOJI_MAP[r] for r in reversed(historico_list)]
    linhas = [hist_emojis[i:i+9] for i in range(0, len(hist_emojis), 9)]
    for linha in linhas[:10]:
        st.markdown(" ".join(linha))
else:
    st.info("Nenhum resultado registrado ainda")

st.markdown("---")

modo_debug = st.checkbox("Modo Debug — mostrar meta da janela (últimos 18)", value=False)

# Análise e sugestão (baseada exclusivamente na janela de 18)
if st.session_state.historico:
    historico_list = list(st.session_state.historico)
    padrao_chave, meta = detectar_padrao(historico_list)
    info = PADROES_INFO.get(padrao_chave, {
        "numero": "?",
        "emoji": "❔",
        "descricao": "Padrão não identificado."
    })

    aposta, explicacao = sugerir_aposta(padrao_chave, meta)

    detalhe = ""
    if meta.get("count_atual", 0) >= 2 and meta.get("ultimo") and meta.get("ultimo") != 'E':
        detalhe = f" ({meta['count_atual']}x {EMOJI_MAP[meta['ultimo']]})"
    display_padrao = f"{padrao_chave}{detalhe}"

    st.markdown(f"**Padrão Detectado: {info['numero']}. {display_padrao} {info['emoji']}**")
    st.write(info["descricao"])

    conf = meta.get("confianca", 0)
    st.metric("Confiança da Detecção (janela)", f"{conf}%")
    try:
        st.progress(conf / 100.0)
    except Exception:
        st.progress(conf)

    if isinstance(aposta, str) and aposta.startswith("Aposte"):
        st.success(f"**Sugestão de Aposta:** {aposta}")
    elif isinstance(aposta, str) and (aposta.startswith("Evitar") or aposta.startswith("Aguardar") or aposta.startswith("Sem") or aposta.startswith("Aposte com cautela")):
        st.warning(f"**Recomendação:** {aposta}")
    else:
        st.info(f"**Recomendação:** {aposta}")

    st.info(f"**Explicação:** {explicacao}")

    if modo_debug:
        st.markdown("---")
        st.write("**DEBUG — metadados calculados sobre a janela (últimos 18)**")
        st.json(meta)
        st.write("Padrão chave:", padrao_chave)
else:
    st.info("Insira resultados para começar a análise")

st.markdown("---")
st.write("Analisador de padrões Football Studio - Use com responsabilidade")
