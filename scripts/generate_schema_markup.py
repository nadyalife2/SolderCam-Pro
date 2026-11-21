#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema.org JSON-LD Generator for Triad-Omni & SolderCam Pro
Generates validated structured data for Google Rich Snippets & GEO (Perplexity/ChatGPT)
"""

import json
from typing import Dict, Any, List

def generate_software_schema(name: str, desc: str, os_req: str = "Android 10+", url: str = "https://github.com/soldercam/pro") -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": name,
        "operatingSystem": os_req,
        "applicationCategory": "UtilitiesApplication",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD"
        },
        "description": desc,
        "url": url,
        "featureList": [
            "Hardware NTC thermistor telemetry",
            "Zero-lag Camera2 manual focus & ISO control",
            "Direct battery bypass power management"
        ]
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n</script>'

def generate_article_schema(headline: str, desc: str, keywords: List[str], author: str = "Triad-Omni Engineering Team") -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": headline,
        "description": desc,
        "keywords": keywords,
        "author": {
            "@type": "Person",
            "name": author
        },
        "publisher": {
            "@type": "Organization",
            "name": "Triad-Omni Project"
        }
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n</script>'

def generate_faq_schema(qa_pairs: List[Dict[str, str]]) -> str:
    entities = []
    for pair in qa_pairs:
        entities.append({
            "@type": "Question",
            "name": pair["q"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": pair["a"]
            }
        })
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n</script>'

if __name__ == "__main__":
    print("=== Demo Schema Generation ===")
    print(generate_software_schema("SolderCam Pro", "Термо-видоискатель для пайки с NTC-телеметрией батареи."))
