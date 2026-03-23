import streamlit as st
import time
import math
import pandas as pd

# =========================
# EPIC 1 ao 6 (BackEnd)
# =========================

class Registro:
    def __init__(self, chave):
        self.chave = chave

    def __repr__(self):
        return self.chave

class Pagina:
    def __init__(self, numero_pagina):
        self.numero_pagina = numero_pagina
        self.registros = []

    def adicionar_registro(self, registro):
        self.registros.append(registro)

    def __repr__(self):
        return f"Página {self.numero_pagina} ({len(self.registros)} registros)"

def carregar_dados(caminho_arquivo, tamanho_pagina):
    paginas = []

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            palavras = [linha.strip() for linha in f if linha.strip()]
    except FileNotFoundError:
        print("Erro: Arquivo não encontrado.")
        return None, 0

    total_palavras = len(palavras)
    print(f"\nTotal de palavras carregadas: {total_palavras}")

    pagina_atual = Pagina(0)

    for palavra in palavras:
        novo_registro = Registro(palavra)
        pagina_atual.adicionar_registro(novo_registro)

        if len(pagina_atual.registros) >= tamanho_pagina:
            paginas.append(pagina_atual)
            pagina_atual = Pagina(len(paginas))

    if len(pagina_atual.registros) > 0:
        paginas.append(pagina_atual)

    print(f"Quantidade total de páginas criadas: {len(paginas)}")

    return paginas, total_palavras

class Bucket:
    def __init__(self, capacidade):
        self.capacidade = capacidade
        self.registros = []
        self.proximo = None # EPIC 3 - Ponteiro para o próximo bucket em caso de overflow

    def adicionar(self, chave, pagina):
        atual = self
        colidiu = False
        novos_overflows = 0
        
        # RN14: contabiliza colisão se o bucket original estiver cheio
        if len(atual.registros) >= self.capacidade:
            colidiu = True
        
        #RN15, 16 e 17: Algoritmo de resolução por Overflow de Buckets
        # Navega pelos buckets de overflow até encontrar um com espaço ou criar um novo
        while len(atual.registros) >= atual.capacidade: 
            if atual.proximo is None:
                atual.proximo = Bucket(atual.capacidade)
                novos_overflows += 1
            atual = atual.proximo
        atual.registros.append((chave, pagina)) # CA15 e CA17 - Adiciona o registro corretamente (seja no principal ou no overflow)
        return colidiu, novos_overflows
        
    def __repr__(self):
        if self.proximo:
            return f"{self.registros} -> OVERFLOW: {self.proximo}"
        return str(self.registros)

# Função hash escolhida pela equipe
def funcao_hash(chave, NB):
    valor = sum(ord(c) for c in chave)
    return valor % NB

def criar_buckets(NR, FR):
    NB = math.ceil(NR / FR) + 1

    print(f"\nNúmero de buckets (NB): {NB}")
    print(f"Capacidade do bucket (FR): {FR}")

    buckets = [Bucket(FR) for _ in range(NB)]
    return buckets, NB

def construir_indice(paginas, buckets, NB, NR):
    inicio = time.time()
    total_colisoes = 0
    total_buckets_overflow = 0
    
    for pagina in paginas:
        for registro in pagina.registros:
            chave = registro.chave
            bucket_id = funcao_hash(chave, NB)
            # O metodo retorna se houver colisão e se gerou novos buckets
            colidiu, overflows_criados = buckets[bucket_id].adicionar(chave, pagina.numero_pagina)

            # CA16 e CA18: Contabilização
            if colidiu:
                total_colisoes += 1
            total_buckets_overflow += overflows_criados
    
    fim = time.time()
    tempo = fim - inicio
    
    taxa_colisoes = (total_colisoes / NR) * 100 if NR > 0 else 0
    buckets_estourados = sum(1 for b in buckets if b.proximo is not None)
    taxa_overflow = (buckets_estourados / NB) * 100 if NB > 0 else 0 

    print(f"\n=== Resultados da Construção do Índice ===")
    print(f"Tempo de construção: {tempo:.6f} segundos")
    print(f"Total de colisões (registros que excederam o bucket): {total_colisoes}")
    print(f"Total de buckets de overflow criados: {total_buckets_overflow}")
    print(f"📈 Taxa de Colisões: {taxa_colisoes:.2f}% dos registros")
    print(f"📈 Taxa de Overflow: {taxa_overflow:.2f}% dos buckets originais")
    return tempo, total_colisoes, total_buckets_overflow, taxa_colisoes, taxa_overflow

def buscar_chave(chave_busca, buckets, NB, paginas):
    bucket_id = funcao_hash(chave_busca, NB)
    atual = buckets[bucket_id]
    
    custo_leituras = 0 # Contabiliza leitura de blocos (páginas de índice + páginas de dados)
    caminho_buckets = []

    while atual is not None:
        custo_leituras += 1 # Simulando a leitura de um bucket (bloco do índice) do disco
        caminho_buckets.append(str(atual.registros)) # Guarda o estado atual do bucket

        for chave_idx, numero_pagina in atual.registros:
            if chave_idx == chave_busca:
                pagina_alvo = paginas[numero_pagina]
                custo_leituras += 1 # Simulando a leitura da página de dados do disco
                
                for registro in pagina_alvo.registros:
                    if registro.chave == chave_busca:
                        return True, numero_pagina, custo_leituras, bucket_id, caminho_buckets
        
        atual = atual.proximo
    return False, None, custo_leituras, bucket_id, caminho_buckets
                             
def executar_table_scan(chave_busca, paginas):
    registros_lidos = []
    custo_paginas = 0
    encontrado = False 
    pagina_encontrada = None

    inicio_ts = time.time()
    for pagina in paginas:
        custo_paginas += 1 #Conta leitura da página 
        for registro in pagina.registros:
            registros_lidos.append(registro.chave)
            if registro.chave == chave_busca:
                encontrado = True
                pagina_encontrada = pagina.numero_pagina
                break # Para a busca no registro atual
            if encontrado:
                break # Para a busca nas paginas
    tempo_ts = time.time() - inicio_ts
    return encontrado, pagina_encontrada, custo_paginas, tempo_ts, registros_lidos

# =========================
# EPIC 7 — INTERFACE GRÁFICA (FRONTEND)
# =========================
st.set_page_config(page_title="Simulador de Hash Estático", layout="wide")
st.title("Simulador de Índice Hash Estático")

if 'indexado' not in st.session_state:
    st.session_state.indexado = False

with st.sidebar:
    st.header("Configurações")
    tam_pagina = st.number_input("Tamanho da Paágina", min_value= 1, value= 1000)
    fr_bucket = st.number_input("Capacidade do Bucket (FR)", min_value= 1, value= 3)
    arquivo = st.text_input("Nome do arquivo", value= "words.txt")

    if st.button("Carregar e construir índice"):
        with st.spinner("Construindo índice"):
            paginas, nr = carregar_dados(arquivo, tam_pagina)
            if paginas:
                nb = math.ceil(nr / fr_bucket) + 1
                buckets = [Bucket(fr_bucket) for _ in range(nb)]

                inicio = time.time()
                colisoes = 0
                overflows = 0 
                for p in paginas:
                    for reg in p.registros:
                        c, o = buckets[funcao_hash(reg.chave, nb)].adicionar(reg.chave, p.numero_pagina)
                        if c: colisoes += 1
                        overflows += o
                fim = time.time()

                st.session_state.paginas = paginas 
                st.session_state.buckets = buckets
                st.session_state.nb = nb
                st.session_state.nr = nr 
                st.session_state.tempo = fim - inicio
                st.session_state.colisoes = colisoes
                st.session_state.overflows = overflows
                st.session_state.indexado = True
                st.success("Índice construído com sucesso!")
            else:
                st.error("Erro: Arquivo não encontrado")

if st.session_state.indexado:
    tab1, tab2, tab3 = st.tabs(["Estatísticas", "Visualização", "Busca"])
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Registros", st.session_state.nr)
        c2.metric("Tempo de Construção", f"{st.session_state.tempo:.4f}s")
        c3.metric("Buckets Criados", st.session_state.nb)
        
        st.write(f"**Colisões:** {st.session_state.colisoes}")
        st.write(f"**Novos Buckets de Overflow:** {st.session_state.overflows}")

    with tab2:
        st.subheader("Visualização de Páginas (CA27)")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.info(f"Primeira Página (ID: 0)")
            st.write([r.chave for r in st.session_state.paginas[0].registros[:10]], "...")
        with col_p2:
            st.info(f"Última Página (ID: {len(st.session_state.paginas)-1})")
            st.write([r.chave for r in st.session_state.paginas[-1].registros[:10]], "...")

        st.subheader("Visualização de Buckets (CA28)")
        # Mostra apenas os primeiros 10 buckets para não travar a UI
        buckets_com_dados = [(i, b) for i, b in enumerate(st.session_state.buckets) if len(b.registros) > 0][:10]

        if not buckets_com_dados:
            st.warning("Nenhum bucket preenchido encontrado")
        else:
            st.write(f"Exibindo os primeiros {len(buckets_com_dados)} buckets ocupados: ")
            for idx, bucket in buckets_com_dados:
                with st.expander(f"Bucket {idx} ({len(bucket.registros)} registros)"):
                    df_bucket = pd.DataFrame(bucket.registros, columns=["Chave", "Página"])
                    st.table(df_bucket)

                    if bucket.proximo:
                        st.warning("Este bucket possui OverFlow")
                        atual_overflow = bucket.proximo
                        while atual_overflow:
                            st.write("Registros em Overflow: ", atual_overflow.registros)
                            atual_overflow = atual_overflow.proximo

    with tab3:
        chave_busca = st.text_input("Digite a chave para busca:")
        if chave_busca:
            # Lógica de Busca por Índice
            b_id = funcao_hash(chave_busca, st.session_state.nb)
            inicio_idx = time.time()
            
            # Simulação de busca
            encontrado = False
            custo_idx = 0
            bucket_alvo = st.session_state.buckets[b_id]
            while bucket_alvo:
                custo_idx += 1
                for k, p in bucket_alvo.registros:
                    if k == chave_busca:
                        encontrado = True
                        pag_id = p
                        break
                if encontrado: break
                bucket_alvo = bucket_alvo.proximo
            tempo_idx = time.time() - inicio_idx

            # Lógica de Table Scan
            inicio_ts = time.time()
            custo_ts = 0
            for p in st.session_state.paginas:
                custo_ts += 1
                if any(r.chave == chave_busca for r in p.registros): break
            tempo_ts = time.time() - inicio_ts

            # Resultados (CA29 - Destaque)
            if encontrado:
                st.success(f"✅ Encontrado na Página {pag_id} via Bucket {b_id}!")
                
                res_df = pd.DataFrame({
                    "Método": ["Índice Hash", "Table Scan"],
                    "Custo (Leituras)": [custo_idx + 1, custo_ts],
                    "Tempo (s)": [f"{tempo_idx:.8f}", f"{tempo_ts:.8f}"]
                })
                st.table(res_df)
                
                economia = ((custo_ts - (custo_idx+1)) / custo_ts) * 100
                st.info(f"O índice foi {economia:.2f}% mais eficiente em termos de I/O.")
            else:
                st.error("Registro não encontrado.")

else:
    st.info("Aguardando carregamento dos dados na barra lateral.")               