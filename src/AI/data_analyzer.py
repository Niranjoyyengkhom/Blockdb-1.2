"""
AI Data Analyzer for IEDB
=========================
Provides intelligent data analysis, insights, and recommendations.
"""

import os
import logging
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from collections import defaultdict, Counter

logger = logging.getLogger("IEDB.AI.DataAnalyzer")

class AIDataAnalyzer:
    """
    AI-powered data analyzer for intelligent insights and recommendations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.analysis_cache = {}
        self.analysis_history = []
        
    def analyze_data_patterns(self, data: List[Dict], tenant_id: str, 
                            analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analyze data patterns and provide insights
        
        Args:
            data: List of data records to analyze
            tenant_id: Tenant identifier
            analysis_type: Type of analysis to perform
            
        Returns:
            Dict containing analysis results and insights
        """
        try:
            logger.info(f"Analyzing data patterns for tenant {tenant_id}, type: {analysis_type}")
            
            if not data:
                return {"error": "No data provided for analysis"}
            
            analysis_id = f"{tenant_id}_{analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Perform different types of analysis
            results = {
                "analysis_id": analysis_id,
                "tenant_id": tenant_id,
                "analysis_type": analysis_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_summary": self._get_data_summary(data),
                "patterns": self._identify_patterns(data),
                "insights": self._generate_insights(data),
                "recommendations": self._generate_recommendations(data, analysis_type),
                "quality_score": self._calculate_data_quality(data)
            }
            
            # Cache results
            self.analysis_cache[analysis_id] = results
            self.analysis_history.append({
                "analysis_id": analysis_id,
                "timestamp": results["timestamp"],
                "tenant_id": tenant_id,
                "type": analysis_type,
                "record_count": len(data)
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            return {"error": str(e), "analysis_type": analysis_type}
    
    def _get_data_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """Generate basic data summary statistics"""
        if not data:
            return {"error": "No data to summarize"}
        
        summary = {
            "total_records": len(data),
            "fields": {},
            "data_types": defaultdict(int),
            "null_counts": defaultdict(int),
            "unique_counts": defaultdict(int)
        }
        
        # Analyze each field
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())
        
        for field in all_fields:
            values = [record.get(field) for record in data]
            non_null_values = [v for v in values if v is not None]
            
            field_info: Dict[str, Any] = {
                "total_count": len(values),
                "non_null_count": len(non_null_values),
                "null_count": values.count(None),
                "unique_count": len(set(str(v) for v in non_null_values if v is not None))
            }
            
            # Determine data type
            if non_null_values:
                sample_value = non_null_values[0]
                if isinstance(sample_value, (int, float)):
                    field_info["data_type"] = "numeric"
                    if len(non_null_values) > 1:
                        numeric_values = [v for v in non_null_values if isinstance(v, (int, float))]
                        if numeric_values:
                            field_info["min"] = min(numeric_values)
                            field_info["max"] = max(numeric_values)
                            field_info["mean"] = statistics.mean(numeric_values)
                            field_info["median"] = statistics.median(numeric_values)
                elif isinstance(sample_value, bool):
                    field_info["data_type"] = "boolean"
                elif isinstance(sample_value, str):
                    field_info["data_type"] = "string"
                    field_info["avg_length"] = statistics.mean([len(str(v)) for v in non_null_values])
                else:
                    field_info["data_type"] = "other"
            else:
                field_info["data_type"] = "unknown"
            
            summary["fields"][field] = field_info
            summary["data_types"][field_info["data_type"]] += 1
        
        return summary
    
    def _identify_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Identify patterns in the data"""
        patterns = {
            "common_values": {},
            "value_distributions": {},
            "correlations": [],
            "anomalies": []
        }
        
        # Find common values for each field
        for field in data[0].keys() if data else []:
            values = [record.get(field) for record in data if record.get(field) is not None]
            if values:
                value_counts = Counter(values)
                patterns["common_values"][field] = value_counts.most_common(5)
                
                # Calculate distribution
                total = len(values)
                distribution = {str(k): v/total for k, v in value_counts.items()}
                patterns["value_distributions"][field] = distribution
        
        # Simple anomaly detection (values that appear only once)
        for field, common_vals in patterns["common_values"].items():
            single_occurrences = [val for val, count in common_vals if count == 1]
            if single_occurrences:
                patterns["anomalies"].append({
                    "field": field,
                    "type": "rare_values",
                    "values": single_occurrences[:10]  # Limit to first 10
                })
        
        return patterns
    
    def _generate_insights(self, data: List[Dict]) -> List[Dict]:
        """Generate insights from data analysis"""
        insights = []
        
        if not data:
            return insights
        
        # Data completeness insight
        total_fields = len(data[0].keys()) if data else 0
        filled_fields = sum(1 for record in data for value in record.values() if value is not None)
        completeness = filled_fields / (len(data) * total_fields) if data and total_fields else 0
        
        insights.append({
            "type": "data_quality",
            "metric": "completeness",
            "value": completeness,
            "description": f"Data is {completeness:.1%} complete",
            "severity": "high" if completeness < 0.7 else "medium" if completeness < 0.9 else "low"
        })
        
        # Record count insight
        insights.append({
            "type": "volume",
            "metric": "record_count",
            "value": len(data),
            "description": f"Dataset contains {len(data)} records",
            "severity": "low" if len(data) > 100 else "medium" if len(data) > 10 else "high"
        })
        
        # Field variety insight
        unique_fields = set()
        for record in data:
            unique_fields.update(record.keys())
        
        insights.append({
            "type": "structure",
            "metric": "field_variety",
            "value": len(unique_fields),
            "description": f"Dataset has {len(unique_fields)} unique fields",
            "severity": "low"
        })
        
        return insights
    
    def _generate_recommendations(self, data: List[Dict], analysis_type: str) -> List[Dict]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if not data:
            recommendations.append({
                "type": "data_collection",
                "priority": "high",
                "description": "No data available for analysis",
                "action": "Start collecting data to enable meaningful analysis"
            })
            return recommendations
        
        # Data quality recommendations
        summary = self._get_data_summary(data)
        for field, info in summary.get("fields", {}).items():
            null_rate = info.get("null_count", 0) / info.get("total_count", 1)
            if null_rate > 0.3:
                recommendations.append({
                    "type": "data_quality",
                    "priority": "medium",
                    "description": f"Field '{field}' has {null_rate:.1%} missing values",
                    "action": f"Consider data validation or default values for '{field}'"
                })
        
        # Performance recommendations
        if len(data) > 1000:
            recommendations.append({
                "type": "performance",
                "priority": "low",
                "description": "Large dataset detected",
                "action": "Consider implementing data pagination or indexing"
            })
        
        # Analysis-specific recommendations
        if analysis_type == "security":
            recommendations.append({
                "type": "security",
                "priority": "high",
                "description": "Security analysis completed",
                "action": "Review data access patterns and implement appropriate controls"
            })
        
        return recommendations
    
    def _calculate_data_quality(self, data: List[Dict]) -> float:
        """Calculate overall data quality score (0-1)"""
        if not data:
            return 0.0
        
        quality_factors = []
        
        # Completeness factor
        total_fields = sum(len(record) for record in data)
        filled_fields = sum(1 for record in data for value in record.values() if value is not None)
        completeness = filled_fields / total_fields if total_fields else 0
        quality_factors.append(completeness)
        
        # Consistency factor (simplified)
        if len(data) > 1:
            field_consistency = []
            all_fields = set()
            for record in data:
                all_fields.update(record.keys())
            
            for field in all_fields:
                field_presence = sum(1 for record in data if field in record)
                consistency = field_presence / len(data)
                field_consistency.append(consistency)
            
            avg_consistency = statistics.mean(field_consistency) if field_consistency else 0
            quality_factors.append(avg_consistency)
        
        return statistics.mean(quality_factors) if quality_factors else 0.0
    
    def get_analysis_history(self, tenant_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get analysis history"""
        history = self.analysis_history
        
        if tenant_id:
            history = [a for a in history if a.get("tenant_id") == tenant_id]
        
        return history[-limit:] if limit else history
    
    def get_cached_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Retrieve cached analysis results"""
        return self.analysis_cache.get(analysis_id)
    
    def generate_report(self, analysis_results: Dict) -> Dict[str, Any]:
        """Generate a formatted analysis report"""
        return {
            "report_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": f"Data Analysis Report - {analysis_results.get('analysis_type', 'General')}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "executive_summary": self._create_executive_summary(analysis_results),
            "detailed_findings": analysis_results,
            "next_steps": self._suggest_next_steps(analysis_results)
        }
    
    def _create_executive_summary(self, results: Dict) -> str:
        """Create executive summary from analysis results"""
        summary_parts = []
        
        data_summary = results.get("data_summary", {})
        record_count = data_summary.get("total_records", 0)
        quality_score = results.get("quality_score", 0)
        
        summary_parts.append(f"Analyzed {record_count} records with {quality_score:.1%} overall quality.")
        
        insights = results.get("insights", [])
        high_priority_insights = [i for i in insights if i.get("severity") == "high"]
        if high_priority_insights:
            summary_parts.append(f"Found {len(high_priority_insights)} high-priority issues requiring attention.")
        
        recommendations = results.get("recommendations", [])
        if recommendations:
            summary_parts.append(f"Generated {len(recommendations)} recommendations for improvement.")
        
        return " ".join(summary_parts)
    
    def _suggest_next_steps(self, results: Dict) -> List[str]:
        """Suggest next steps based on analysis"""
        next_steps = []
        
        recommendations = results.get("recommendations", [])
        high_priority = [r for r in recommendations if r.get("priority") == "high"]
        
        if high_priority:
            next_steps.append("Address high-priority recommendations first")
        
        quality_score = results.get("quality_score", 0)
        if quality_score < 0.8:
            next_steps.append("Implement data quality improvements")
        
        next_steps.extend([
            "Schedule regular data analysis",
            "Monitor key metrics over time",
            "Consider automation for repetitive tasks"
        ])
        
        return next_steps
