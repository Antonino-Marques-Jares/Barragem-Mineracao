#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Barragens no Brasil - ETL

Fonte:
  - Informações das Barragens: https://dados.gov.br/dados/conjuntos-dados/barragens-de-mineracao
  - Atualizado em: 19/06/2025

Autor: Antonino Marques Jares
"""

import json
import os
import re
from datetime import datetime

import pandas as pd


# ---------------------------------------------------------------------------
# Configurações de caminhos
# ---------------------------------------------------------------------------
# Diretório onde está o CSV original (bronze)
URL_ETL = r"D:\ETL\nivel_01_bronze\barragens"
PLANILHA_ORIGEM = os.path.join(URL_ETL, "Barragens.csv")

# Diretório do projeto (onde o arquivo JSON será salvo)
URL_PROJETO = os.getcwd()

# Pasta de saída do JSON
PASTA_JSON = os.path.join(URL_PROJETO, "etl")
ARQUIVO_JSON = os.path.join(PASTA_JSON, "barragens_de_mineracao.json")


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def dms_to_float(dms_str):
    """
    Converte coordenadas no formato DMS (ex: -04°31'24.900") para graus
    decimais (float). Retorna None se a entrada for inválida ou vazia.
    """
    if pd.isna(dms_str) or not isinstance(dms_str, str) or dms_str.strip() == "":
        return None

    try:
        # Padroniza a string removendo espaços e caracteres especiais
        dms_str = dms_str.strip().replace('″', '"').replace("''", '"')

        # Expressão regular para extrair componentes
        match = re.match(r'^(-?\d+)°\s*(\d+)\'\s*(\d+\.?\d*)\s*["\']?$', dms_str)
        if not match:
            return None

        graus, minutos, segundos = map(float, match.groups())

        # Calcula o valor decimal
        sinal = -1 if graus < 0 else 1
        decimal = abs(graus) + minutos / 60 + segundos / 3600
        return decimal * sinal

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Etapa 1: leitura e inspeção do CSV original
# ---------------------------------------------------------------------------
def ler_barragens():
    """Lê o CSV original e exibe colunas e primeiras linhas."""
    try:
        df = pd.read_csv(
            PLANILHA_ORIGEM,
            sep=",",
            encoding="latin-1",
            on_bad_lines="warn",
        )
        colunas = df.columns.tolist()
        print(colunas)
        print(df.head(10))
        return df
    except Exception as e:
        print(f"\nERRO CRÍTICO: {str(e)}")
        return None
    finally:
        print("Fim")


# ---------------------------------------------------------------------------
# Etapa 2: transformação (renomear, converter coordenadas)
# ---------------------------------------------------------------------------
def transformar_barragens():
    """Carrega e transforma os dados. Retorna o DataFrame pronto (ou None)."""
    try:
        print(f"Diretório do projeto: {URL_PROJETO}")

        # Carrega os dados
        df = pd.read_csv(
            PLANILHA_ORIGEM,
            sep=",",
            encoding="latin-1",
            on_bad_lines="warn",
        )

        # Renomeia colunas
        df = df.rename(columns={
            "ID": "ID",
            "Nome da mina": "MINA",
            "UF": "UF",
            "Município": "MUNICIPIO",
            "Latitude": "LATITUDE",
            "Longitude": "LONGITUDE",
            "Categoria de Risco - CRI": "RISCO",
        })

        # Converte coordenadas
        df["LATITUDE"] = df["LATITUDE"].apply(dms_to_float)
        df["LONGITUDE"] = df["LONGITUDE"].apply(dms_to_float)

        # Seleciona colunas e trata valores nulos
        colunas_selecionadas = [
            "ID", "MINA", "UF", "MUNICIPIO",
            "LATITUDE", "LONGITUDE", "RISCO",
        ]
        df = df[colunas_selecionadas]

        df["MINA"] = df["MINA"].fillna("Nome da mina não informado")
        df["RISCO"] = df["RISCO"].fillna("Não informado")

        return df
    except Exception as e:
        print(f"\nERRO CRÍTICO: {str(e)}")
        return None
    finally:
        print("Processamento concluído")


# ---------------------------------------------------------------------------
# Etapa 3: exportação para JSON (etl/barragens_de_mineracao.json)
# ---------------------------------------------------------------------------
def exportar_json(df):
    """Exporta o DataFrame para etl/barragens_de_mineracao.json com metadados."""
    if df is None:
        print("\nERRO: DataFrame vazio ou inválido. JSON não gerado.")
        return

    try:
        # Garante que a pasta 'etl' exista
        os.makedirs(PASTA_JSON, exist_ok=True)

        # Estrutura final do JSON
        payload = {
            "metadados": {
                "data_de_atualizacao": datetime.now().strftime("%d-%m-%Y"),
                "responsavel": "Antonino Marques Jares",
                "nome_programa": os.path.basename(__file__),
            },
            "dados": df.to_dict(orient="records"),
        }

        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)

        print(f"Arquivo JSON salvo em: {ARQUIVO_JSON}")
    except Exception as e:
        print(f"\nERRO CRÍTICO: {str(e)}")
    finally:
        print("Fim")


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Garante que o diretório do projeto existe
    os.makedirs(URL_PROJETO, exist_ok=True)

    print("=" * 60)
    print("ETAPA 1 - Leitura e inspeção do CSV original")
    print("=" * 60)
    ler_barragens()

    print("\n" + "=" * 60)
    print("ETAPA 2 - Transformação dos dados")
    print("=" * 60)
    df_transformado = transformar_barragens()

    print("\n" + "=" * 60)
    print("ETAPA 3 - Exportação para JSON (etl/barragens_de_mineracao.json)")
    print("=" * 60)
    exportar_json(df_transformado)