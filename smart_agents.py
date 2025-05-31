from typing import Dict, List, Any
from langchain.agents import Tool
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, Graph
from analytics import SalesAnalytics
from config import db
from langchain_google_genai import ChatGoogleGenerativeAI
from reporting_agents import ReportingAgent
from whatsapp_agent import WhatsAppAgent
import os

# ප්‍රධාන Agent State Class එක
class AgentState(dict):
    """Agent තත්ව පන්තිය"""
    current_input: str
    messages: List[BaseMessage]
    actions: List[AgentAction]
    final_response: str = None
    report_path: str = None
    charts: List[str] = None
    whatsapp_sent: bool = False

# විශ්ලේෂණ Agent
class AnalyticsAgent:
    """විකුණුම් දත්ත විශ්ලේෂණය කරන Agent"""
    def __init__(self):
        self.analytics = SalesAnalytics()
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

    def analyze(self, state: AgentState) -> AgentState:
        query = state["current_input"]
        try:
            # විකුණුම් විශ්ලේෂණය
            trending = self.analytics.get_trending_products(days=30)
            summary = self.analytics.get_sales_summary(days=30)
            
            # විශ්ලේෂණ වාර්තාව සැකසීම
            analysis = {
                "trending_products": trending,
                "sales_summary": summary
            }
            
            state["analysis_results"] = analysis
            return state
        except Exception as e:
            state["error"] = str(e)
            return state

# තොග කළමනාකරණ Agent
class InventoryAgent:
    """තොග මට්ටම් පරීක්ෂා කරන Agent"""
    def __init__(self):
        self.analytics = SalesAnalytics()
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

    def check_inventory(self, state: AgentState) -> AgentState:
        try:
            # අඩු තොග ඇති භාණ්ඩ සොයාගැනීම
            low_stock = self.analytics.get_stock_alerts(threshold=10)
            
            state["inventory_status"] = {
                "low_stock_items": low_stock
            }
            return state
        except Exception as e:
            state["error"] = str(e)
            return state

# නිර්දේශ Agent
class RecommendationAgent:
    """නිර්දේශ ජනනය කරන Agent"""
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

    def generate_recommendations(self, state: AgentState) -> AgentState:
        try:
            analysis = state.get("analysis_results", {})
            inventory = state.get("inventory_status", {})
            
            # දත්ත විශ්ලේෂණය කර නිර්දේශ ජනනය
            recommendations = []
            
            if analysis.get("trending_products"):
                recommendations.append("ජනප්‍රිය භාණ්ඩ වල තොග මට්ටම් වැඩි කරන්න")
            
            if inventory.get("low_stock_items"):
                recommendations.append("අඩු තොග ඇති භාණ්ඩ ඇණවුම් කරන්න")
            
            state["recommendations"] = recommendations
            return state
        except Exception as e:
            state["error"] = str(e)
            return state

# ප්‍රධාන Workflow සැකසීම
def create_agent_workflow() -> Graph:
    """Multi-Agent Workflow එක සැකසීම"""
    
    # Agents සැකසීම
    analytics_agent = AnalyticsAgent()
    inventory_agent = InventoryAgent()
    recommendation_agent = RecommendationAgent()
    reporting_agent = ReportingAgent()
    whatsapp_agent = WhatsAppAgent()
    
    # Workflow Graph එක සැකසීම
    workflow = StateGraph(AgentState)
    
    # Nodes එකතු කිරීම
    workflow.add_node("analyze", analytics_agent.analyze)
    workflow.add_node("check_inventory", inventory_agent.check_inventory)
    workflow.add_node("recommend", recommendation_agent.generate_recommendations)
    workflow.add_node("report", reporting_agent.generate_report)
    workflow.add_node("send_whatsapp", whatsapp_agent.send_report)
    
    # Edges සැකසීම
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "check_inventory")
    workflow.add_edge("check_inventory", "recommend")
    workflow.add_edge("recommend", "report")
    workflow.add_edge("report", "send_whatsapp")
    
    # අවසාන පියවර සැකසීම
    def last_step(state: AgentState) -> AgentState:
        if state.get("error"):
            state["final_response"] = f"දෝෂයක් ඇති විය: {state['error']}"
        else:
            response_parts = [
                "විශ්ලේෂණ වාර්තාව:",
                "\nප්‍රවණතා:",
                str(state.get("analysis_results", {})),
                "\nතොග තත්වය:",
                str(state.get("inventory_status", {})),
                "\nනිර්දේශ:",
                "\n".join(state.get("recommendations", [])),
                "\nවාර්තා:",
                f"\nPDF වාර්තාව: {state.get('report_path', 'Not generated')}",
                "\nප්‍රස්තාර:",
                "\n".join(state.get("charts", [])),
                "\nWhatsApp යැවීම:",
                "සාර්ථකයි" if state.get("whatsapp_sent") else "අසාර්ථකයි"
            ]
            state["final_response"] = "\n".join(response_parts)
        return state
    
    workflow.add_node("last_step", last_step)
    workflow.add_edge("send_whatsapp", "last_step")
    
    return workflow.compile() 