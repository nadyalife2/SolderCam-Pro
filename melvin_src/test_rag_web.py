import knowledge_rag
import web_tools
import time

print("1. Testing Knowledge RAG...")
knowledge_rag.init_knowledge_db()
fact = knowledge_rag.search_knowledge("кто такой рик")
print(f"RAG Fact: '{fact}'")

print("2. Testing Web Tools (Weather)...")
w = web_tools.get_live_weather("Москва")
print(f"Weather: '{w}'")

print("3. Testing Web Tools (Currency)...")
c = web_tools.get_currency_rates()
print(f"Currency: '{c}'")

print("4. Testing Web Tools (Wikipedia)...")
wiki = web_tools.search_wikipedia_fact("кто такой Илон Маск")
print(f"Wikipedia: '{wiki}'")
