from typing import List
import os
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import seaborn as sns
from analytics import SalesAnalytics
from langchain_google_genai import ChatGoogleGenerativeAI

class ReportingAgent:
    """Agent for generating reports and visualizations"""
    def __init__(self):
        self.analytics = SalesAnalytics()
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
        
    def generate_report(self, state: dict) -> dict:
        try:
            # Create reports directory if it doesn't exist
            os.makedirs("reports", exist_ok=True)
            
            # Generate charts
            chart_paths = self._generate_charts(state)
            state["charts"] = chart_paths
            
            # Generate PDF report
            report_path = self._generate_pdf_report(state)
            state["report_path"] = report_path
            
            return state
        except Exception as e:
            state["error"] = str(e)
            return state
    
    def _generate_charts(self, state: dict) -> List[str]:
        """Generate visualization charts"""
        chart_paths = []
        
        try:
            # Get data from state
            analysis = state.get("analysis_results", {})
            inventory = state.get("inventory_status", {})
            
            # Trending Products Chart
            if "trending_products" in analysis:
                plt.figure(figsize=(10, 6))
                trending_data = analysis["trending_products"]
                products = [item["product"] for item in trending_data]
                sales = [item["sales"] for item in trending_data]
                
                sns.barplot(x=sales, y=products)
                plt.title("Trending Products - Last 30 Days")
                plt.xlabel("Sales Count")
                
                chart_path = f"reports/trending_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(chart_path)
                plt.close()
                chart_paths.append(chart_path)
            
            # Low Stock Items Chart
            if "low_stock_items" in inventory:
                plt.figure(figsize=(10, 6))
                low_stock = inventory["low_stock_items"]
                products = [item["product"] for item in low_stock]
                stock = [item["quantity"] for item in low_stock]
                
                sns.barplot(x=stock, y=products, color="red")
                plt.title("Low Stock Items")
                plt.xlabel("Current Stock")
                
                chart_path = f"reports/low_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(chart_path)
                plt.close()
                chart_paths.append(chart_path)
            
            return chart_paths
        except Exception as e:
            print(f"Error generating charts: {str(e)}")
            return []
    
    def _generate_pdf_report(self, state: dict) -> str:
        """Generate PDF report with analysis and charts"""
        try:
            # Initialize PDF
            pdf = FPDF()
            pdf.add_page()
            
            # Add title
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Business Analytics Report", ln=True, align="C")
            pdf.ln(10)
            
            # Add date
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            pdf.ln(10)
            
            # Add analysis results
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Analysis Results", ln=True)
            pdf.set_font("Arial", "", 12)
            
            analysis = state.get("analysis_results", {})
            for key, value in analysis.items():
                pdf.multi_cell(0, 10, f"{key}: {str(value)}")
            pdf.ln(5)
            
            # Add inventory status
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Inventory Status", ln=True)
            pdf.set_font("Arial", "", 12)
            
            inventory = state.get("inventory_status", {})
            for key, value in inventory.items():
                pdf.multi_cell(0, 10, f"{key}: {str(value)}")
            pdf.ln(5)
            
            # Add recommendations
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Recommendations", ln=True)
            pdf.set_font("Arial", "", 12)
            
            recommendations = state.get("recommendations", [])
            for rec in recommendations:
                pdf.multi_cell(0, 10, f"- {rec}")
            pdf.ln(5)
            
            # Add charts
            if state.get("charts"):
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "Visualizations", ln=True)
                
                for chart_path in state["charts"]:
                    if os.path.exists(chart_path):
                        pdf.image(chart_path, x=10, w=190)
                        pdf.ln(5)
            
            # Save PDF
            report_path = f"reports/business_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(report_path)
            
            return report_path
        except Exception as e:
            print(f"Error generating PDF report: {str(e)}")
            return None 