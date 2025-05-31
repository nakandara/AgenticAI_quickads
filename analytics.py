from datetime import datetime, timedelta
from typing import List, Dict, Any
from config import db
from pymongo import DESCENDING
import pandas as pd
from collections import defaultdict

class SalesAnalytics:
    def __init__(self):
        self.invoice_items = db['invoiceitems']
        self.inventory = db['inventories']
        self.shops = db['shops']

    def get_trending_products(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending products based on sales volume in the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'createdAt': {'$gte': cutoff_date}
                }
            },
            {
                '$group': {
                    '_id': '$productId',
                    'productName': {'$first': '$productName'},
                    'total_quantity': {'$sum': '$quantity'},
                    'total_sales': {'$sum': '$amount'},
                    'average_price': {'$avg': '$price'},
                    'sale_count': {'$sum': 1}
                }
            },
            {
                '$sort': {'total_quantity': -1}
            },
            {
                '$limit': limit
            }
        ]
        
        trending = list(self.invoice_items.aggregate(pipeline))
        
        # Enrich with current inventory data
        for product in trending:
            inventory_data = self.inventory.find_one({'_id': product['_id']})
            if inventory_data:
                product['current_stock'] = inventory_data.get('quantity', 0)
                product['current_price'] = inventory_data.get('price', 0)
        
        return trending

    def get_sales_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get overall sales summary for the specified period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'createdAt': {'$gte': cutoff_date}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_sales': {'$sum': '$amount'},
                    'total_items': {'$sum': '$quantity'},
                    'average_order_value': {'$avg': '$amount'},
                    'total_orders': {'$sum': 1}
                }
            }
        ]
        
        summary = list(self.invoice_items.aggregate(pipeline))
        return summary[0] if summary else {}

    def get_daily_sales_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily sales trend for the specified period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'createdAt': {'$gte': cutoff_date}
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$createdAt'
                        }
                    },
                    'total_sales': {'$sum': '$amount'},
                    'total_items': {'$sum': '$quantity'},
                    'order_count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id': 1}
            }
        ]
        
        return list(self.invoice_items.aggregate(pipeline))

    def get_category_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get sales performance by category."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'createdAt': {'$gte': cutoff_date}
                }
            },
            {
                '$lookup': {
                    'from': 'inventories',
                    'localField': 'productId',
                    'foreignField': '_id',
                    'as': 'inventory'
                }
            },
            {
                '$unwind': '$inventory'
            },
            {
                '$group': {
                    '_id': '$inventory.inventoryCategoryId',
                    'total_sales': {'$sum': '$amount'},
                    'total_items': {'$sum': '$quantity'},
                    'product_count': {'$addToSet': '$productId'}
                }
            },
            {
                '$project': {
                    'category': '$_id',
                    'total_sales': 1,
                    'total_items': 1,
                    'product_count': {'$size': '$product_count'}
                }
            },
            {
                '$sort': {'total_sales': -1}
            }
        ]
        
        return list(self.invoice_items.aggregate(pipeline))

    def get_stock_alerts(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Get products with low stock levels."""
        pipeline = [
            {
                '$match': {
                    'quantity': {'$lte': threshold}
                }
            },
            {
                '$project': {
                    'productName': 1,
                    'quantity': 1,
                    'price': 1,
                    'brandName': 1,
                    'productType': 1
                }
            },
            {
                '$sort': {'quantity': 1}
            }
        ]
        
        return list(self.inventory.aggregate(pipeline))

    def get_shop_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get sales performance by shop."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'createdAt': {'$gte': cutoff_date}
                }
            },
            {
                '$group': {
                    '_id': '$shopId',
                    'total_sales': {'$sum': '$amount'},
                    'total_items': {'$sum': '$quantity'},
                    'order_count': {'$sum': 1}
                }
            },
            {
                '$lookup': {
                    'from': 'shops',
                    'localField': '_id',
                    'foreignField': '_id',
                    'as': 'shop'
                }
            },
            {
                '$unwind': '$shop'
            },
            {
                '$project': {
                    'shop_name': '$shop.shopName',
                    'total_sales': 1,
                    'total_items': 1,
                    'order_count': 1,
                    'average_order_value': {'$divide': ['$total_sales', '$order_count']}
                }
            },
            {
                '$sort': {'total_sales': -1}
            }
        ]
        
        return list(self.invoice_items.aggregate(pipeline)) 