import os
import time
import math

# =========================
# EPIC 1 — Carga dos dados
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

# =========================
# EPIC 2 e 3 — Índice Hash, Colisões e Overflow
# =========================

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

def construir_indice(paginas, buckets, NB):
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
    
    print(f"\n=== Resultados da Construção do Índice ===")
    print(f"Tempo de construção: {tempo:.6f} segundos")
    print(f"Total de colisões (registros que excederam o bucket): {total_colisoes}")
    print(f"Total de buckets de overflow criados: {total_buckets_overflow}")

# =========================
# EPIC 4 — Pesquisa por Índice
# =========================
def buscar_chave(chave_busca, buckets, NB, paginas):
    bucket_id = funcao_hash(chave_busca, NB)
    atual = buckets[bucket_id]
    
    custo_leituras = 0 # Contabiliza leitura de blocos (páginas de índice + páginas de dados)
    
    while atual is not None:
        custo_leituras += 1 # Simulando a leitura de um bucket (bloco do índice) do disco
        for chave_idx, numero_pagina in atual.registros:
            if chave_idx == chave_busca:
                pagina_alvo = paginas[numero_pagina]
                custo_leituras += 1 # Simulando a leitura da página de dados do disco
                
                for registro in pagina_alvo.registros:
                    if registro.chave == chave_busca:
                        return True, numero_pagina, custo_leituras
        
        atual = atual.proximo
    return False, None, custo_leituras
                            
        


# =========================
# Programa principal
# =========================

if __name__ == "__main__":

    print("=== Simulador de Índice Hash Estático ===")

    try:
        tamanho_pagina = int(input("Informe o tamanho da página: "))

        if tamanho_pagina <= 0:
            print("Erro: tamanho da página inválido")
            exit()

        paginas, NR = carregar_dados('words.txt', tamanho_pagina)

        if not paginas:
            exit()

        # Mostrar páginas
        primeira = paginas[0]
        ultima = paginas[-1]

        print("\n--- Primeira Página ---")
        print(primeira.numero_pagina)
        print(primeira.registros[:5])

        print("\n--- Última Página ---")
        print(ultima.numero_pagina)
        print(ultima.registros[:5])

        # =====================
        # EPIC 2 e 3 Execução
        # =====================

        FR = int(input("\nInforme a capacidade do bucket (FR) (Ex: 5): "))

        buckets, NB = criar_buckets(NR, FR)

        construir_indice(paginas, buckets, NB)

        print("\nExemplo de 10 buckets que sofreram OverFlow: ")

        mostrados = 0

        for i, bucket in enumerate(buckets):
            if bucket.registros:  # só entra no IF se o bucket tiver um 'proximo' (ou seja, se deu overflow)
                print(f"Bucket {i}: {bucket}")
                mostrados += 1

            if mostrados == 10:
                break
        # =====================
        # EPIC 4 Execução
        # =====================
        print("\n=== Sistema de Busca ===")
        print("Digite 'sair' para encerrar a busca.")
        
        while True:
            chave_busca = input("\nDigite a palavra que deseja buscar: ").strip()
            
            if chave_busca.lower() == 'sair':
                print("Encerrando o simulador")
                break
            
            if not chave_busca:
                continue
            
            inicio_busca = time.time()
            encontrada, num_pagina, custo = buscar_chave(chave_busca, buckets, NB, paginas)
            tempo_busca = time.time() - inicio_busca
            
            if encontrada:
                print(f"✅ Palavra '{chave_busca}' encontrada!")
                print(f"📄 Localização: Página {num_pagina}")
                print(f"⏱️ Tempo de busca: {tempo_busca:.6f} segundos")
                print(f"📊 Custo estimado: {custo} leituras de bloco (índice + dados)")
            else:
                print(f"❌ Palavra '{chave_busca}' NÃO encontrada.")
                print(f"📊 Custo estimado na tentativa: {custo} leituras de bloco de índice")
           
    except ValueError:
        print("Erro: digite um número inteiro válido.")