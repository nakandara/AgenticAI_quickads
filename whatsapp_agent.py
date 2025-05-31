from typing import Dict, List
from twilio.rest import Client
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class WhatsAppMessenger:
    """WhatsApp පණිවිඩ යැවීමේ පන්තිය"""
    
    def __init__(self):
        # Twilio credentials
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')  # Format: 'whatsapp:+14155238886'
        
        # Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
    def send_text_message(self, to_number: str, message: str) -> bool:
        """පෙළ පණිවිඩයක් යැවීම"""
        try:
            # WhatsApp format number
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            # Send message
            message = self.client.messages.create(
                from_=self.from_number,
                body=message,
                to=to_number
            )
            
            return True
        except Exception as e:
            print(f"WhatsApp පණිවිඩ යැවීමේ දෝෂයක්: {str(e)}")
            return False
    
    def send_report_with_media(self, to_number: str, message: str, media_files: List[str]) -> bool:
        """පණිවිඩය සහ මාධ්‍ය ගොනු යැවීම"""
        try:
            # WhatsApp format number
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            # Send message with media
            message = self.client.messages.create(
                from_=self.from_number,
                body=message,
                media_url=media_files,  # Can include PDF and image URLs
                to=to_number
            )
            
            return True
        except Exception as e:
            print(f"WhatsApp මාධ්‍ය යැවීමේ දෝෂයක්: {str(e)}")
            return False

class WhatsAppAgent:
    """WhatsApp පණිවිඩ යැවීමේ Agent"""
    
    def __init__(self):
        self.messenger = WhatsAppMessenger()
    
    def send_report(self, state: Dict) -> Dict:
        """වාර්තාව WhatsApp හරහා යැවීම"""
        try:
            # Get recipient number from environment or state
            to_number = os.getenv('DEFAULT_WHATSAPP_RECIPIENT')
            
            # Prepare message
            message_parts = [
                "🏪 *වෙළඳසැල් විශ්ලේෂණ වාර්තාව*",
                "\n📊 *විකුණුම් සාරාංශය:*"
            ]
            
            if "analysis_results" in state:
                sales_summary = state["analysis_results"].get("sales_summary", {})
                message_parts.extend([
                    f"\nමුළු විකුණුම්: රු. {sales_summary.get('total_sales', 0):,.2f}",
                    f"මුළු ඇණවුම්: {sales_summary.get('total_orders', 0)}",
                    f"සාමාන්‍ය ඇණවුම් වටිනාකම: රු. {sales_summary.get('average_order_value', 0):,.2f}"
                ])
            
            if "inventory_status" in state:
                message_parts.extend([
                    "\n\n📦 *අඩු තොග ඇති භාණ්ඩ:*"
                ])
                for item in state["inventory_status"].get("low_stock_items", []):
                    message_parts.append(f"\n• {item['productName']} - තොගය: {item['quantity']}")
            
            if "recommendations" in state:
                message_parts.extend([
                    "\n\n💡 *නිර්දේශ:*"
                ])
                for rec in state["recommendations"]:
                    message_parts.append(f"\n• {rec}")
            
            # Send text message
            message = "\n".join(message_parts)
            self.messenger.send_text_message(to_number, message)
            
            # Send media files if available
            media_files = []
            
            if "report_path" in state:
                report_path = Path(state["report_path"])
                if report_path.exists():
                    media_files.append(str(report_path))
            
            if "charts" in state:
                for chart in state["charts"]:
                    chart_path = Path(chart)
                    if chart_path.exists():
                        media_files.append(str(chart_path))
            
            if media_files:
                self.messenger.send_report_with_media(
                    to_number,
                    "📎 වාර්තාවේ ප්‍රස්තාර සහ PDF ගොනු",
                    media_files
                )
            
            state["whatsapp_sent"] = True
            return state
            
        except Exception as e:
            state["error"] = f"WhatsApp යැවීමේ දෝෂයක්: {str(e)}"
            return state 