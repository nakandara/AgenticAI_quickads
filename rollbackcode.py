# from langgraph.graph import StateGraph
# from typing import TypedDict, List
# from langchain_community.retrievers import BM25Retriever
# from langchain.retrievers import EnsembleRetriever
# from langchain_google_genai import ChatGoogleGenerativeAI
# from vector_store import load_vector_db
# from config import db, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
# from neo4j import GraphDatabase
# import asyncio
# import os
# from langchain.memory import ConversationBufferMemory
# from langchain.prompts import PromptTemplate
# from langchain_core.runnables import RunnableSequence
# from langchain.schema import Document
# from datetime import datetime

# # Initialize Neo4j AuraDB connection
# class Neo4jConnector:
#     _instance = None
    
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#             cls._instance.driver = GraphDatabase.driver(
#                 NEO4J_URI,
#                 auth=(NEO4J_USER, NEO4J_PASSWORD)
#             )
#         return cls._instance
    
#     def query(self, cypher, params=None):
#         try:
#             with self.driver.session() as session:
#                 result = session.run(cypher, params)
#                 return [dict(record) for record in result]
#         except Exception as e:
#             print(f"Neo4j query error: {str(e)}")
#             return []

# # Initialize connection
# try:
#     neo4j = Neo4jConnector()
#     test_result = neo4j.query("RETURN 1 AS test")
#     if test_result and test_result[0]['test'] == 1:
#         print(f"✅ Neo4j AuraDB connected at {datetime.now()}")
#     else:
#         raise ConnectionError("Neo4j connection test failed")
# except Exception as e:
#     print(f"❌ Neo4j connection failed: {str(e)}")
#     raise

# class GraphState(TypedDict):
#     question: str
#     raw_data: List[str]  # Maintain original field name
#     semantic_results: List[str]
#     keyword_results: List[str]
#     graph_results: List[dict]
#     final_answer: str

# # Initialize model
# api_key = os.getenv("GEMINI_API_KEY")
# llm = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     google_api_key=api_key,
#     temperature=0.7,
#     max_output_tokens=2048
# )

# # Memory setup
# memory = ConversationBufferMemory(
#     return_messages=True,
#     memory_key="chat_history",
#     input_key="question",
#     output_key="final_answer"
# )

# # Cypher queries
# GRAPH_QUERIES = {
#     "product_search": """
#     MATCH (p:Product)
#     WHERE toLower(p.name) CONTAINS toLower($query)
#     RETURN p {
#         .name,
#         .price,
#         .discount_price,
#         .quantity,
#         available_at: [(p)<-[:SELLS]-(s:Shop) | s {.name, .address, .phone}],
#         related: [(p)-[:RELATED_TO]->(r:Product) | r {.name, .price}]
#     }
#     ORDER BY p.name
#     LIMIT 5
#     """,
#     "shop_search": """
#     MATCH (s:Shop)-[:SELLS]->(p:Product)
#     WHERE toLower(s.name) CONTAINS toLower($query)
#     RETURN s {
#         .name,
#         .address,
#         .phone,
#         products: COLLECT(DISTINCT p {.name, .price})[0..5]
#     }
#     LIMIT 3
#     """
# }

# # Prompt template with enhanced instructions
# prompt = PromptTemplate.from_template("""
# # FOOD BUSINESS ASSISTANT

# ## CONTEXT SOURCES:
# 1. SEMANTIC MATCHES (contextual similarity):
# {semantic_results}

# 2. KEYWORD MATCHES (exact matches):
# {keyword_results}

# 3. KNOWLEDGE GRAPH (relationships):
# {graph_results}

# ## USER QUESTION:
# {question}

# ## RESPONSE REQUIREMENTS:
# 1. STRUCTURE:
#    - Direct answer first (1-2 sentences)
#    - Detailed breakdown (bulleted points)
#    - Related items/shops (if applicable)

# 2. CONTENT:
#    - Always include prices in LKR format (e.g., 1,500 LKR)
#    - Mention availability status
#    - Highlight discounts/special offers
#    - Include shop contact info when relevant

# 3. FORMATTING:
#    - Use Markdown for readability
#    - Bold important numbers/names
#    - Separate sections with ---

# 4. UNCERTAINTY HANDLING:
#    - If conflicting info: "Discrepancy noted: [detail]"
#    - If missing data: "Please contact 077-6694351 for [missing info]"

# ## CURRENT DATE: {current_date}

# Generate the most helpful response possible:
# """)

# # Chain setup
# explain_chain: RunnableSequence = prompt | llm

# # Initialize retrievers
# vector_db = load_vector_db()
# semantic_retriever = vector_db.as_retriever(
#     search_type="similarity",
#     search_kwargs={"k": 5, "score_threshold": 0.7}
# )

# def get_bm25_documents():
#     documents = []
#     for collection_name in ['inventories', 'shops', 'invoiceitems']:
#         for doc in db[collection_name].find({}, {"_id": 0}):
#             text = f"{doc.get('productName', doc.get('shopName', ''))}\n"
#             text += f"{doc.get('description', doc.get('shopAddress', ''))}\n"
#             text += f"Price: {doc.get('price', doc.get('productPrice', 'N/A'))} LKR"
#             documents.append(Document(
#                 page_content=text,
#                 metadata={
#                     "source": collection_name,
#                     "name": doc.get('productName', doc.get('shopName', 'Unknown'))
#                 }
#             ))
#     return documents

# keyword_retriever = BM25Retriever.from_documents(get_bm25_documents())
# keyword_retriever.k = 5

# retriever = EnsembleRetriever(
#     retrievers=[semantic_retriever],
#     weights=[0.6, 0.4]
# )

# def format_semantic_results(docs):
#     return [f"[collection: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}" for doc in docs]

# def format_keyword_results(docs):
#     return [f"[collection: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}" for doc in docs]

# def format_graph_results(results):
#     if not results:
#         return []
    
#     formatted = []
#     for item in results:
#         if 'p' in item:  # Product result
#             product = item['p']
#             formatted.append(
#                 f"Product: {product['name']}\n"
#                 f"Price: {product.get('price', 'N/A')} LKR\n"
#                 f"Discount: {product.get('discount_price', 'N/A')} LKR\n"
#                 f"Quantity: {product.get('quantity', 'N/A')}"
#             )
#         elif 's' in item:  # Shop result
#             shop = item['s']
#             formatted.append(
#                 f"Shop: {shop['name']}\n"
#                 f"Address: {shop.get('address', 'N/A')}\n"
#                 f"Phone: {shop.get('phone', 'N/A')}"
#             )
#     return formatted

# def retrieve_step(state: GraphState):
#     question = state["question"]
#     print(f"\n🔍 Retrieving data for: {question}")
    
#     try:
#         # 1. Hybrid Search
#         semantic_docs = semantic_retriever.invoke(question)
#         keyword_docs = keyword_retriever.invoke(question)
        
#         # 2. Graph Search
#         if any(word in question.lower() for word in ['shop', 'store', 'location']):
#             graph_results = neo4j.query(GRAPH_QUERIES["shop_search"], {"query": question})
#         else:
#             graph_results = neo4j.query(GRAPH_QUERIES["product_search"], {"query": question})
        
#         # Combine all results into raw_data
#         raw_data = (
#             format_semantic_results(semantic_docs) + 
#             format_keyword_results(keyword_docs) + 
#             format_graph_results(graph_results)
#         )
        
#         return {
#             "question": question,
#             "raw_data": raw_data,
#             "semantic_results": "\n".join(format_semantic_results(semantic_docs)),
#             "keyword_results": "\n".join(format_keyword_results(keyword_docs)),
#             "graph_results": "\n".join(format_graph_results(graph_results))
#         }
#     except Exception as e:
#         print(f"⚠️ Retrieval error: {str(e)}")
#         return state

# def explain_step(state: GraphState) -> GraphState:
#     print("🧠 Generating explanation...")
    
#     response = asyncio.run(
#         asyncio.to_thread(
#             explain_chain.invoke,
#             {
#                 "data": "\n\n".join(state["raw_data"]),
#                 "question": state["question"],
#                 "semantic_results": state["semantic_results"],
#                 "keyword_results": state["keyword_results"],
#                 "graph_results": state["graph_results"],
#                 "current_date": datetime.now().strftime("%Y-%m-%d")
#             }
#         )
#     )

#     memory.chat_memory.add_ai_message(response.content)
#     print("✅ Got response from LLM.")

#     return {
#         "question": state["question"],
#         "raw_data": state["raw_data"],
#         "final_answer": response,  # Keep the full response object
#         "semantic_results": state["semantic_results"],
#         "keyword_results": state["keyword_results"],
#         "graph_results": state["graph_results"]
#     }

# def final_step(state: GraphState) -> GraphState:
#     """Maintain the exact original response format"""
#     return {
#         "question": state["question"],
#         "raw_data": state["raw_data"],
#         "final_answer": state["final_answer"],  # Full response object
#         "response": state["final_answer"].content  # Just the content for backward compatibility
#     }
# def build_graph():
#     workflow = StateGraph(GraphState)
#     workflow.add_node("retrieve", retrieve_step)
#     workflow.add_node("explain", explain_step)
#     workflow.add_node("final", final_step)
    
#     workflow.set_entry_point("retrieve")
#     workflow.add_edge("retrieve", "explain")
#     workflow.add_edge("explain", "final")
    
#     return workflow.compile()

# __all__ = ["build_graph", "explain_chain", "neo4j"]




# from fastapi import FastAPI, Query
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import asyncio
# from agent_graph import build_graph, explain_chain  # Now these imports will work
# from analytics import SalesAnalytics
# from typing import Optional
# from smart_agents import create_agent_workflow, AgentState

# app = FastAPI()

# # CORS setup (keep your existing CORS configuration)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize components
# chain = build_graph()
# analytics = SalesAnalytics()
# agent_workflow = create_agent_workflow()

# class QuestionInput(BaseModel):
#     question: str

# @app.post("/ask")
# async def ask_question(input: QuestionInput):
#     try:
#         print(f"📥 Received question: {input.question}")
#         result = await asyncio.to_thread(
#             chain.invoke,
#             {"question": input.question}
#         )
#         return {
#             "question": input.question,
#             "answer": result.get("final_answer", "No response generated")
#         }
#     except Exception as e:
#         print(f"❌ Error occurred: {e}")
#         return {"error": str(e)}

# @app.get("/test")
# async def test_chain():
#     try:
#         test_response = explain_chain.invoke({
#             "question": "Test question",
#             "semantic_results": "Test data",
#             "keyword_results": "Test keywords",
#             "graph_results": "Test graph",
#             "current_date": "2025-05-17"
#         })
#         return {"response": test_response.content}
#     except Exception as e:
#         return {"error": str(e)}

# # New Analytics Endpoints
# @app.get("/analytics/trending-products")
# async def get_trending_products(days: Optional[int] = Query(30, gt=0), limit: Optional[int] = Query(10, gt=0)):
#     """Get trending products based on sales volume."""
#     try:
#         return analytics.get_trending_products(days=days, limit=limit)
#     except Exception as e:
#         return {"error": str(e)}

# @app.get("/analytics/sales-summary")
# async def get_sales_summary(days: Optional[int] = Query(30, gt=0)):
#     """Get overall sales summary."""
#     try:
#         return analytics.get_sales_summary(days=days)
#     except Exception as e:
#         return {"error": str(e)}

# @app.get("/analytics/daily-trend")
# async def get_daily_sales_trend(days: Optional[int] = Query(30, gt=0)):
#     """Get daily sales trend."""
#     try:
#         return analytics.get_daily_sales_trend(days=days)
#     except Exception as e:
#         return {"error": str(e)}

# @app.get("/analytics/category-performance")
# async def get_category_performance(days: Optional[int] = Query(30, gt=0)):
#     """Get sales performance by category."""
#     try:
#         return analytics.get_category_performance(days=days)
#     except Exception as e:
#         return {"error": str(e)}

# @app.get("/analytics/stock-alerts")
# async def get_stock_alerts(threshold: Optional[int] = Query(10, gt=0)):
#     """Get products with low stock levels."""
#     try:
#         return analytics.get_stock_alerts(threshold=threshold)
#     except Exception as e:
#         return {"error": str(e)}

# @app.get("/analytics/shop-performance")
# async def get_shop_performance(days: Optional[int] = Query(30, gt=0)):
#     """Get sales performance by shop."""
#     try:
#         return analytics.get_shop_performance(days=days)
#     except Exception as e:
#         return {"error": str(e)}

# # New Multi-Agent endpoint
# @app.post("/smart-analysis")
# async def run_smart_analysis(input: QuestionInput):
#     """බුද්ධිමත් විශ්ලේෂණ පද්ධතිය"""
#     try:
#         # Initialize state
#         initial_state = AgentState(
#             current_input=input.question,
#             messages=[],
#             actions=[]
#         )
        
#         # Run workflow
#         result = await asyncio.to_thread(
#             agent_workflow.invoke,
#             initial_state
#         )
        
#         return {
#             "status": "success",
#             "question": input.question,
#             "response": result.get("final_response", "No response generated")
#         }
#     except Exception as e:
#         return {"error": str(e)}










# from langgraph.graph import StateGraph
# from typing import TypedDict, List
# from langchain_community.retrievers import BM25Retriever
# from langchain.retrievers import EnsembleRetriever
# from langchain_google_genai import ChatGoogleGenerativeAI
# from vector_store import load_vector_db
# from config import db, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
# from neo4j import GraphDatabase
# import asyncio
# import os
# from langchain.memory import ConversationBufferMemory
# from langchain.prompts import PromptTemplate
# from langchain_core.runnables import RunnableSequence
# from langchain.schema import Document
# from datetime import datetime

# # Initialize Neo4j AuraDB connection
# class Neo4jConnector:
#     _instance = None
#     _is_connected = False
    
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#             try:
#                 cls._instance.driver = GraphDatabase.driver(
#                     NEO4J_URI,
#                     auth=(NEO4J_USER, NEO4J_PASSWORD)
#                 )
#                 cls._instance._is_connected = True
#             except Exception as e:
#                 print(f"⚠️ Warning - Neo4j connection failed: {str(e)}")
#                 cls._instance.driver = None
#                 cls._instance._is_connected = False
#         return cls._instance
    
#     def query(self, cypher, params=None):
#         if not self._is_connected:
#             print("⚠️ Warning: Neo4j is not connected. Returning empty result.")
#             return []
            
#         try:
#             with self.driver.session() as session:
#                 result = session.run(cypher, params)
#                 return [dict(record) for record in result]
#         except Exception as e:
#             print(f"⚠️ Warning - Neo4j query error: {str(e)}")
#             return []

# # Initialize connection
# neo4j = Neo4jConnector()
# try:
#     if neo4j._is_connected:
#         test_result = neo4j.query("RETURN 1 AS test")
#         if test_result and test_result[0]['test'] == 1:
#             print(f"✅ Neo4j AuraDB connected at {datetime.now()}")
#         else:
#             print("⚠️ Warning: Neo4j connection test failed, but app will continue running")
#     else:
#         print("⚠️ Warning: Neo4j is not connected, but app will continue running")
# except Exception as e:
#     print(f"⚠️ Warning: Neo4j connection test failed: {str(e)}, but app will continue running")

# class GraphState(TypedDict):
#     question: str
#     raw_data: List[str]  # Maintain original field name
#     semantic_results: List[str]
#     keyword_results: List[str]
#     graph_results: List[dict]
#     final_answer: str

# # Initialize model
# api_key = os.getenv("GEMINI_API_KEY")
# llm = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     google_api_key=api_key,
#     temperature=0.7,
#     max_output_tokens=2048
# )

# # Memory setup
# memory = ConversationBufferMemory(
#     return_messages=True,
#     memory_key="chat_history",
#     input_key="question",
#     output_key="final_answer"
# )

# # Cypher queries
# GRAPH_QUERIES = {
#     "product_search": """
#     MATCH (p:Product)
#     WHERE toLower(p.name) CONTAINS toLower($query)
#     RETURN p {
#         .name,
#         .price,
#         .discount_price,
#         .quantity,
#         available_at: [(p)<-[:SELLS]-(s:Shop) | s {.name, .address, .phone}],
#         related: [(p)-[:RELATED_TO]->(r:Product) | r {.name, .price}]
#     }
#     ORDER BY p.name
#     LIMIT 5
#     """,
#     "shop_search": """
#     MATCH (s:Shop)-[:SELLS]->(p:Product)
#     WHERE toLower(s.name) CONTAINS toLower($query)
#     RETURN s {
#         .name,
#         .address,
#         .phone,
#         products: COLLECT(DISTINCT p {.name, .price})[0..5]
#     }
#     LIMIT 3
#     """
# }

# # Prompt template with enhanced instructions
# prompt = PromptTemplate.from_template("""
# # FOOD BUSINESS ASSISTANT

# ## CONTEXT SOURCES:
# 1. SEMANTIC MATCHES (contextual similarity):
# {semantic_results}

# 2. KEYWORD MATCHES (exact matches):
# {keyword_results}

# 3. KNOWLEDGE GRAPH (relationships):
# {graph_results}

# ## USER QUESTION:
# {question}

# ## RESPONSE REQUIREMENTS:
# 1. STRUCTURE:
#    - Direct answer first (1-2 sentences)
#    - Detailed breakdown (bulleted points)
#    - Related items/shops (if applicable)

# 2. CONTENT:
#    - Always include prices in LKR format (e.g., 1,500 LKR)
#    - Mention availability status
#    - Highlight discounts/special offers
#    - Include shop contact info when relevant

# 3. FORMATTING:
#    - Use Markdown for readability
#    - Bold important numbers/names
#    - Separate sections with ---

# 4. UNCERTAINTY HANDLING:
#    - If conflicting info: "Discrepancy noted: [detail]"
#    - If missing data: "Please contact 077-6694351 for [missing info]"

# ## CURRENT DATE: {current_date}

# Generate the most helpful response possible:
# """)

# # Chain setup
# explain_chain: RunnableSequence = prompt | llm

# # Initialize retrievers
# vector_db = load_vector_db()
# semantic_retriever = vector_db.as_retriever(
#     search_type="similarity",
#     search_kwargs={"k": 5, "score_threshold": 0.7}
# )

# # Temporarily disabled keyword retriever
# # def get_bm25_documents():
# #     documents = []
# #     for collection_name in ['inventories', 'shops', 'invoiceitems']:
# #         for doc in db[collection_name].find({}, {"_id": 0}):
# #             text = f"{doc.get('productName', doc.get('shopName', ''))}\n"
# #             text += f"{doc.get('description', doc.get('shopAddress', ''))}\n"
# #             text += f"Price: {doc.get('price', doc.get('productPrice', 'N/A'))} LKR"
# #             documents.append(Document(
# #                 page_content=text,
# #                 metadata={
# #                     "source": collection_name,
# #                     "name": doc.get('productName', doc.get('shopName', 'Unknown'))
# #                 }
# #             ))
# #     return documents

# # keyword_retriever = BM25Retriever.from_documents(get_bm25_documents())
# # keyword_retriever.k = 5

# # Using only semantic retriever for now
# retriever = EnsembleRetriever(
#     retrievers=[semantic_retriever],
#     weights=[1.0]  # 100% weight to semantic retriever
# )

# def format_semantic_results(docs):
#     return [f"[collection: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}" for doc in docs]

# def format_keyword_results(docs):
#     return []  # Return empty list since keyword search is disabled
#     # return [f"[collection: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}" for doc in docs]

# def format_graph_results(results):
#     if not results or not neo4j._is_connected:
#         return ["⚠️ Graph database is currently unavailable"]
    
#     formatted = []
#     for item in results:
#         if 'p' in item:  # Product result
#             product = item['p']
#             formatted.append(
#                 f"Product: {product['name']}\n"
#                 f"Price: {product.get('price', 'N/A')} LKR\n"
#                 f"Discount: {product.get('discount_price', 'N/A')} LKR\n"
#                 f"Quantity: {product.get('quantity', 'N/A')}"
#             )
#         elif 's' in item:  # Shop result
#             shop = item['s']
#             formatted.append(
#                 f"Shop: {shop['name']}\n"
#                 f"Address: {shop.get('address', 'N/A')}\n"
#                 f"Phone: {shop.get('phone', 'N/A')}"
#             )
#     return formatted

# def retrieve_step(state: GraphState):
#     """Retrieve relevant information from multiple sources."""
#     question = state["question"]
    
#     # Get semantic search results
#     semantic_docs = semantic_retriever.get_relevant_documents(question)
#     semantic_results = format_semantic_results(semantic_docs)
    
#     # Get keyword search results (currently disabled)
#     keyword_results = []
    
#     # Get graph results only if Neo4j is connected
#     graph_results = []
#     if neo4j._is_connected:
#         for query_name, cypher in GRAPH_QUERIES.items():
#             results = neo4j.query(cypher, {"query": question.lower()})
#             if results:
#                 graph_results.extend(results)
    
#     return {
#         **state,
#         "semantic_results": semantic_results,
#         "keyword_results": keyword_results,
#         "graph_results": graph_results
#     }

# def explain_step(state: GraphState) -> GraphState:
#     print("🧠 Generating explanation...")
    
#     response = asyncio.run(
#         asyncio.to_thread(
#             explain_chain.invoke,
#             {
#                 "data": "\n\n".join(state["raw_data"]),
#                 "question": state["question"],
#                 "semantic_results": state["semantic_results"],
#                 "keyword_results": state["keyword_results"],
#                 "graph_results": state["graph_results"],
#                 "current_date": datetime.now().strftime("%Y-%m-%d")
#             }
#         )
#     )

#     memory.chat_memory.add_ai_message(response.content)
#     print("✅ Got response from LLM.")

#     return {
#         "question": state["question"],
#         "raw_data": state["raw_data"],
#         "final_answer": response,  # Keep the full response object
#         "semantic_results": state["semantic_results"],
#         "keyword_results": state["keyword_results"],
#         "graph_results": state["graph_results"]
#     }

# def final_step(state: GraphState) -> GraphState:
#     """Maintain the exact original response format"""
#     return {
#         "question": state["question"],
#         "raw_data": state["raw_data"],
#         "final_answer": state["final_answer"],  # Full response object
#         "response": state["final_answer"].content  # Just the content for backward compatibility
#     }

# def build_graph():
#     workflow = StateGraph(GraphState)
#     workflow.add_node("retrieve", retrieve_step)
#     workflow.add_node("explain", explain_step)
#     workflow.add_node("final", final_step)
    
#     workflow.set_entry_point("retrieve")
#     workflow.add_edge("retrieve", "explain")
#     workflow.add_edge("explain", "final")
    
#     return workflow.compile()

# __all__ = ["build_graph", "explain_chain", "neo4j"]
