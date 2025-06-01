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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from agent_graph import build_graph, explain_chain  # Now these imports will work

app = FastAPI()

# CORS setup (keep your existing CORS configuration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build the graph
chain = build_graph()

class QuestionInput(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(input: QuestionInput):
    try:
        print(f"📥 Received question: {input.question}")
        result = await asyncio.to_thread(
            chain.invoke,
            {"question": input.question}
        )
        return {
            "question": input.question,
            "answer": result.get("final_answer", "No response generated")
        }
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return {"error": str(e)}

@app.get("/test")
async def test_chain():
    try:
        test_response = explain_chain.invoke({
            "question": "Test question",
            "semantic_results": "Test data",
            "keyword_results": "Test keywords",
            "graph_results": "Test graph",
            "current_date": "2025-05-17"
        })
        return {"response": test_response.content}
    except Exception as e:
        return {"error": str(e)}