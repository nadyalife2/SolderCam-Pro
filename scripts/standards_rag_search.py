#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni & Tochka Plavleniya: Standards Fast Vector RAG Search
Обеспечивает поиск по базе стандартов за < 2 миллисекунды.
Используется проверяющим агентом (Agent 03 / ОТК) для фактчекинга статей.
"""

import json
import math
import re
import sys
from pathlib import Path

def tokenize(text: str) -> list:
    text = text.lower()
    tokens = re.findall(r'[a-zа-яё0-9_\-\.]+', text)
    stopwords = {"и", "в", "на", "с", "по", "для", "не", "от", "до", "при", "из", "или", "что", "как", "так", "то", "какой", "какая", "какие"}
    clean = []
    for t in tokens:
        t = t.strip(".-_")
        if len(t) >= 2 and t not in stopwords:
            clean.append(t)
    return clean

class StandardsRAG:
    def __init__(self, index_path: Path = None):
        if index_path is None:
            # Ищем сначала в локальной папке, затем в tochka-plavleniya
            candidates = [
                Path(__file__).resolve().parent.parent / "datasets" / "standards_vector_index.json",
                Path(r"D:\tochka-plavleniya\gem-knowledge\standards_vector_index.json")
            ]
            for c in candidates:
                if c.exists():
                    index_path = c
                    break
        
        if not index_path or not index_path.exists():
            raise FileNotFoundError("Индекс standards_vector_index.json не найден!")

        with open(index_path, "r", encoding="utf-8") as f:
            self.index = json.load(f)

        self.vocabulary = {token: i for i, token in enumerate(self.index["vocabulary"])}
        self.idf = {int(k): v for k, v in self.index["idf"].items()}
        self.documents = self.index["documents"]

    def search(self, query: str, top_k: int = 3) -> list:
        tokens = tokenize(query)
        if not tokens:
            return []

        # Построение вектора запроса
        tf = {}
        for t in tokens:
            if t in self.vocabulary:
                idx = self.vocabulary[t]
                tf[idx] = tf.get(idx, 0) + 1

        if not tf:
            # Fallback: частичное совпадение подстрок
            scores = []
            for doc in self.documents:
                text_lower = doc["text"].lower() + " " + doc["title"].lower()
                matches = sum(1 for t in tokens if t in text_lower)
                if matches > 0:
                    scores.append((matches / len(tokens), doc))
            scores.sort(key=lambda x: x[0], reverse=True)
            return [{"score": round(s, 4), "doc": d} for s, d in scores[:top_k]]

        # TF-IDF с логарифмированием
        vec = {}
        norm_sq = 0.0
        for idx, count in tf.items():
            weight = (1.0 + math.log(count)) * self.idf.get(idx, 1.0)
            vec[idx] = weight
            norm_sq += weight * weight

        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        query_vec = {idx: w / norm for idx, w in vec.items()}

        # Вычисление косинусного сходства
        results = []
        for doc in self.documents:
            doc_vec = {int(k): v for k, v in doc["vector"].items()}
            # Скалярное произведение
            dot_product = 0.0
            for idx, q_weight in query_vec.items():
                if idx in doc_vec:
                    dot_product += q_weight * doc_vec[idx]

            if dot_product > 0.01:
                results.append((dot_product, doc))

        results.sort(key=lambda x: x[0], reverse=True)
        return [{"score": round(score, 4), "doc": doc} for score, doc in results[:top_k]]

def main():
    if len(sys.argv) < 2:
        print("Использование: python standards_rag_search.py '<запрос по госту или стандарту>'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    rag = StandardsRAG()
    hits = rag.search(query, top_k=2)

    print(f"\n🔍 Запрос: '{query}'")
    print(f"📊 Найдено результатов: {len(hits)}\n" + "="*60)
    for i, hit in enumerate(hits, 1):
        doc = hit["doc"]
        print(f"[{i}] Релевантность: {hit['score'] * 100:.1f}%")
        print(f"📌 Стандарт: {doc['standard']}")
        print(f"🏷️  Тема: {doc['title']}")
        print(f"📄 Требования:\n{doc['text']}")
        print("-" * 60)

if __name__ == "__main__":
    main()
