import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import statistics

class EstimationLearningSystem:
    def __init__(self, data_file: str = "estimation_history.json"):
        self.data_file = data_file
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load estimation history from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        """Save estimation history to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def record_estimation(self, jira_ticket: str, estimated_hours: float, 
                         complexity: str, phases: Dict, method: str, 
                         description: str = "", actual_hours: Optional[float] = None):
        """Record a new estimation"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'jira_ticket': jira_ticket,
            'description': description,
            'estimated_hours': estimated_hours,
            'actual_hours': actual_hours,
            'complexity': complexity,
            'phases': phases,
            'method': method,
            'accuracy': None if actual_hours is None else abs(estimated_hours - actual_hours) / actual_hours
        }
        
        self.history.append(record)
        self._save_history()
        return record
    
    def update_actual_hours(self, jira_ticket: str, actual_hours: float):
        """Update actual hours for a completed ticket"""
        for record in reversed(self.history):
            if record['jira_ticket'] == jira_ticket:
                record['actual_hours'] = actual_hours
                record['accuracy'] = abs(record['estimated_hours'] - actual_hours) / actual_hours
                self._save_history()
                return True
        return False
    
    def get_accuracy_stats(self) -> Dict:
        """Get overall accuracy statistics"""
        completed = [r for r in self.history if r['actual_hours'] is not None]
        if not completed:
            return {'message': 'No completed estimations yet'}
        
        accuracies = [r['accuracy'] for r in completed]
        return {
            'total_estimations': len(self.history),
            'completed_estimations': len(completed),
            'avg_accuracy_error': statistics.mean(accuracies),
            'median_accuracy_error': statistics.median(accuracies),
            'best_accuracy': min(accuracies),
            'worst_accuracy': max(accuracies)
        }
    
    def get_complexity_adjustments(self) -> Dict:
        """Calculate adjustment factors based on historical accuracy"""
        completed = [r for r in self.history if r['actual_hours'] is not None]
        if len(completed) < 3:
            return {}
        
        adjustments = {}
        for complexity in ['Low', 'Medium', 'High']:
            complexity_records = [r for r in completed if r['complexity'] == complexity]
            if len(complexity_records) >= 2:
                # Calculate average ratio of actual/estimated
                ratios = [r['actual_hours'] / r['estimated_hours'] for r in complexity_records]
                adjustments[complexity] = statistics.mean(ratios)
        
        return adjustments
    
    def get_improved_estimate(self, base_estimate: Dict) -> Dict:
        """Apply learning adjustments to improve estimate"""
        adjustments = self.get_complexity_adjustments()
        
        if not adjustments or base_estimate['complexity'] not in adjustments:
            return base_estimate
        
        # Apply learned adjustment factor
        factor = adjustments[base_estimate['complexity']]
        improved_estimate = base_estimate.copy()
        improved_estimate['total_hours'] = round(base_estimate['total_hours'] * factor, 2)
        
        # Adjust phases proportionally
        for phase, hours in improved_estimate['phases'].items():
            improved_estimate['phases'][phase] = round(hours * factor, 2)
        
        improved_estimate['learning_applied'] = True
        improved_estimate['adjustment_factor'] = factor
        
        return improved_estimate