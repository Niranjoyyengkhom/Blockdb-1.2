"""
AI Insight Generator for IEDB
=============================
Generates intelligent insights, trends, and predictive analytics.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from collections import defaultdict

logger = logging.getLogger("IEDB.AI.InsightGenerator")

class AIInsightGenerator:
    """
    AI-powered insight generator for intelligent database insights and predictions
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.insight_cache = {}
        self.trend_data = defaultdict(list)
        
    def generate_insights(self, data: List[Dict], tenant_id: str, 
                         insight_type: str = "comprehensive",
                         time_range: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate intelligent insights from data
        
        Args:
            data: Data to analyze for insights
            tenant_id: Tenant identifier
            insight_type: Type of insights to generate
            time_range: Time range for analysis
            
        Returns:
            Dict containing generated insights
        """
        try:
            logger.info(f"Generating insights for tenant {tenant_id}, type: {insight_type}")
            
            insight_id = f"insight_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            insights = {
                "insight_id": insight_id,
                "tenant_id": tenant_id,
                "insight_type": insight_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_points": len(data),
                "key_insights": self._extract_key_insights(data, insight_type),
                "trends": self._identify_trends(data, time_range),
                "predictions": self._generate_predictions(data),
                "anomalies": self._detect_anomalies(data),
                "recommendations": self._generate_insight_recommendations(data, insight_type),
                "confidence_score": self._calculate_confidence(data)
            }
            
            # Cache insights
            self.insight_cache[insight_id] = insights
            
            # Update trend data
            self.trend_data[tenant_id].append({
                "timestamp": datetime.now(timezone.utc),
                "data_points": len(data),
                "insight_count": len(insights["key_insights"])
            })
            
            return insights
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return {"error": str(e), "insight_type": insight_type}
    
    def _extract_key_insights(self, data: List[Dict], insight_type: str) -> List[Dict]:
        """Extract key insights from data"""
        insights = []
        
        if not data:
            return insights
        
        # Data volume insights
        insights.append({
            "category": "volume",
            "title": "Data Volume Analysis",
            "description": f"Dataset contains {len(data)} records",
            "impact": "medium" if len(data) > 100 else "low",
            "actionable": len(data) < 10
        })
        
        # Data structure insights
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())
        
        insights.append({
            "category": "structure",
            "title": "Data Structure Complexity",
            "description": f"Dataset has {len(all_fields)} unique fields",
            "impact": "high" if len(all_fields) > 20 else "medium" if len(all_fields) > 10 else "low",
            "actionable": len(all_fields) > 15
        })
        
        # Data completeness insights
        total_possible_values = len(data) * len(all_fields)
        actual_values = sum(1 for record in data for value in record.values() if value is not None)
        completeness = actual_values / total_possible_values if total_possible_values else 0
        
        insights.append({
            "category": "quality",
            "title": "Data Completeness",
            "description": f"Data is {completeness:.1%} complete",
            "impact": "high" if completeness < 0.7 else "medium" if completeness < 0.9 else "low",
            "actionable": completeness < 0.8
        })
        
        # Field usage insights
        field_usage = defaultdict(int)
        for record in data:
            for field in record:
                if record[field] is not None:
                    field_usage[field] += 1
        
        if field_usage:
            most_used_field = max(field_usage, key=lambda x: field_usage[x])
            least_used_field = min(field_usage, key=lambda x: field_usage[x])
            
            insights.append({
                "category": "usage",
                "title": "Field Usage Patterns",
                "description": f"Most used: {most_used_field} ({field_usage[most_used_field]} records), Least used: {least_used_field} ({field_usage[least_used_field]} records)",
                "impact": "medium",
                "actionable": field_usage[least_used_field] < len(data) * 0.1
            })
        
        return insights
    
    def _identify_trends(self, data: List[Dict], time_range: Optional[str]) -> List[Dict]:
        """Identify trends in the data"""
        trends = []
        
        # Simple trend analysis based on data patterns
        if len(data) > 1:
            trends.append({
                "type": "growth",
                "metric": "record_count",
                "direction": "stable",
                "strength": 0.5,
                "description": f"Dataset size appears stable at {len(data)} records",
                "period": time_range or "current"
            })
        
        # Field complexity trend
        field_counts = [len(record.keys()) for record in data]
        if field_counts:
            avg_fields = sum(field_counts) / len(field_counts)
            trends.append({
                "type": "complexity",
                "metric": "field_diversity",
                "direction": "stable",
                "strength": 0.6,
                "description": f"Average {avg_fields:.1f} fields per record",
                "period": time_range or "current"
            })
        
        return trends
    
    def _generate_predictions(self, data: List[Dict]) -> List[Dict]:
        """Generate predictive insights"""
        predictions = []
        
        if len(data) < 10:
            predictions.append({
                "category": "growth",
                "prediction": "Limited data for reliable predictions",
                "confidence": 0.2,
                "timeframe": "short_term",
                "basis": "Insufficient historical data"
            })
        else:
            predictions.append({
                "category": "volume",
                "prediction": "Data volume likely to remain stable",
                "confidence": 0.7,
                "timeframe": "short_term",
                "basis": f"Based on current {len(data)} records"
            })
        
        # Data quality prediction
        null_count = sum(1 for record in data for value in record.values() if value is None)
        total_values = sum(len(record) for record in data)
        null_rate = null_count / total_values if total_values else 0
        
        if null_rate > 0.2:
            predictions.append({
                "category": "quality",
                "prediction": "Data quality may degrade without intervention",
                "confidence": 0.8,
                "timeframe": "medium_term",
                "basis": f"Current null rate: {null_rate:.1%}"
            })
        
        return predictions
    
    def _detect_anomalies(self, data: List[Dict]) -> List[Dict]:
        """Detect anomalies in the data"""
        anomalies = []
        
        if not data:
            return anomalies
        
        # Check for records with unusual field counts
        field_counts = [len(record.keys()) for record in data]
        if field_counts:
            avg_fields = sum(field_counts) / len(field_counts)
            threshold = avg_fields * 0.5  # 50% below average
            
            unusual_records = [(i, count) for i, count in enumerate(field_counts) if count < threshold]
            if unusual_records:
                anomalies.append({
                    "type": "structural",
                    "description": f"Found {len(unusual_records)} records with unusually few fields",
                    "severity": "medium",
                    "affected_records": len(unusual_records),
                    "details": f"Average: {avg_fields:.1f} fields, anomalies have < {threshold:.1f} fields"
                })
        
        # Check for completely empty records
        empty_records = [i for i, record in enumerate(data) if not any(record.values())]
        if empty_records:
            anomalies.append({
                "type": "data_quality",
                "description": f"Found {len(empty_records)} completely empty records",
                "severity": "high",
                "affected_records": len(empty_records),
                "details": "Records contain only null or empty values"
            })
        
        return anomalies
    
    def _generate_insight_recommendations(self, data: List[Dict], insight_type: str) -> List[Dict]:
        """Generate recommendations based on insights"""
        recommendations = []
        
        if not data:
            recommendations.append({
                "priority": "high",
                "category": "data_collection",
                "action": "Start data collection",
                "description": "No data available for meaningful insights",
                "impact": "Enables all analysis capabilities"
            })
            return recommendations
        
        # Data volume recommendations
        if len(data) < 100:
            recommendations.append({
                "priority": "medium",
                "category": "volume",
                "action": "Increase data collection",
                "description": f"Current {len(data)} records may limit insight accuracy",
                "impact": "Improves prediction reliability"
            })
        
        # Data quality recommendations
        null_count = sum(1 for record in data for value in record.values() if value is None)
        total_values = sum(len(record) for record in data)
        null_rate = null_count / total_values if total_values else 0
        
        if null_rate > 0.1:
            recommendations.append({
                "priority": "medium",
                "category": "quality",
                "action": "Implement data validation",
                "description": f"High null rate ({null_rate:.1%}) affects insight quality",
                "impact": "Improves data completeness and insight accuracy"
            })
        
        # Monitoring recommendations
        recommendations.append({
            "priority": "low",
            "category": "monitoring",
            "action": "Set up automated insights",
            "description": "Regular insight generation for trend tracking",
            "impact": "Enables proactive data management"
        })
        
        return recommendations
    
    def _calculate_confidence(self, data: List[Dict]) -> float:
        """Calculate confidence score for insights"""
        if not data:
            return 0.0
        
        confidence_factors = []
        
        # Data volume factor
        volume_factor = min(len(data) / 1000, 1.0)  # Max confidence at 1000+ records
        confidence_factors.append(volume_factor)
        
        # Data completeness factor
        total_possible = sum(len(record.keys()) for record in data)
        total_filled = sum(1 for record in data for value in record.values() if value is not None)
        completeness_factor = total_filled / total_possible if total_possible else 0
        confidence_factors.append(completeness_factor)
        
        # Data consistency factor
        if len(data) > 1:
            all_fields = set()
            for record in data:
                all_fields.update(record.keys())
            
            field_consistency = []
            for field in all_fields:
                presence = sum(1 for record in data if field in record)
                consistency = presence / len(data)
                field_consistency.append(consistency)
            
            avg_consistency = sum(field_consistency) / len(field_consistency) if field_consistency else 0
            confidence_factors.append(avg_consistency)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    
    def get_trend_analysis(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis for a tenant over specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        relevant_trends = [
            trend for trend in self.trend_data.get(tenant_id, [])
            if trend["timestamp"] >= cutoff_date
        ]
        
        if not relevant_trends:
            return {"error": "No trend data available for the specified period"}
        
        # Calculate trend metrics
        data_points_trend = [t["data_points"] for t in relevant_trends]
        insight_counts_trend = [t["insight_count"] for t in relevant_trends]
        
        return {
            "period_days": days,
            "data_points": {
                "values": data_points_trend,
                "trend": "increasing" if data_points_trend[-1] > data_points_trend[0] else "decreasing",
                "average": sum(data_points_trend) / len(data_points_trend)
            },
            "insight_generation": {
                "values": insight_counts_trend,
                "trend": "increasing" if insight_counts_trend[-1] > insight_counts_trend[0] else "decreasing",
                "average": sum(insight_counts_trend) / len(insight_counts_trend)
            },
            "analysis_frequency": len(relevant_trends) / days
        }
    
    def get_cached_insights(self, insight_id: str) -> Optional[Dict]:
        """Retrieve cached insights"""
        return self.insight_cache.get(insight_id)
    
    def get_insight_summary(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of all insights generated"""
        relevant_insights = []
        
        for insight in self.insight_cache.values():
            if tenant_id is None or insight.get("tenant_id") == tenant_id:
                relevant_insights.append(insight)
        
        if not relevant_insights:
            return {"message": "No insights available"}
        
        return {
            "total_insights": len(relevant_insights),
            "insight_types": list(set(i.get("insight_type") for i in relevant_insights)),
            "average_confidence": sum(i.get("confidence_score", 0) for i in relevant_insights) / len(relevant_insights),
            "recent_insights": sorted(relevant_insights, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
        }
