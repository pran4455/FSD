from abc import ABC, abstractmethod
from typing import Dict, List

class InvestmentStrategy(ABC):
    
    @abstractmethod
    def get_asset_allocation(self) -> Dict[str, float]:
        
        pass
    
    @abstractmethod
    def get_expected_return(self) -> float:
        
        pass
    
    @abstractmethod
    def get_risk_level(self) -> str:
        
        pass
    
    @abstractmethod
    def get_rebalancing_threshold(self) -> float:
        
        pass
    
    @abstractmethod
    def get_recommendations(self) -> List[str]:
        
        pass
    
    def calculate_projection(self, initial_savings: float, monthly_contribution: float, 
                           years: int) -> Dict[str, float]:
        
        monthly_return = self.get_expected_return() / 100 / 12
        months = years * 12
        
        total_value = initial_savings
        total_contributions = 0
        
        for _ in range(months):
            total_value = total_value * (1 + monthly_return) + monthly_contribution
            total_contributions += monthly_contribution
        
        investment_returns = total_value - initial_savings - total_contributions
        
        return {
            'total_value': round(total_value, 2),
            'total_contributions': round(total_contributions, 2),
            'investment_returns': round(investment_returns, 2),
            'initial_savings': initial_savings,
            'expected_return': self.get_expected_return()
        }

class ConservativeStrategy(InvestmentStrategy):
    
    def get_asset_allocation(self) -> Dict[str, float]:
        return {
            'bonds': 60.0,
            'stocks': 25.0,
            'cash': 10.0,
            'gold': 5.0
        }
    
    def get_expected_return(self) -> float:
        return 6.5
    
    def get_risk_level(self) -> str:
        return "Low Risk - Capital Preservation Focus"
    
    def get_rebalancing_threshold(self) -> float:
        return 5.0
    
    def get_recommendations(self) -> List[str]:
        return [
            "Focus on high-quality government and corporate bonds",
            "Invest in large-cap, dividend-paying stocks",
            "Maintain emergency fund in liquid assets",
            "Consider fixed deposits and debt mutual funds",
            "Avoid high-volatility investments"
        ]

class ModerateStrategy(InvestmentStrategy):
    
    def get_asset_allocation(self) -> Dict[str, float]:
        return {
            'stocks': 50.0,
            'bonds': 35.0,
            'real_estate': 10.0,
            'gold': 5.0
        }
    
    def get_expected_return(self) -> float:
        return 9.0
    
    def get_risk_level(self) -> str:
        return "Moderate Risk - Balanced Growth"
    
    def get_rebalancing_threshold(self) -> float:
        return 7.0
    
    def get_recommendations(self) -> List[str]:
        return [
            "Diversify across equity and debt instruments",
            "Mix of large-cap and mid-cap stocks",
            "Include index funds for broad market exposure",
            "Consider REITs for real estate exposure",
            "Review portfolio quarterly"
        ]

class AggressiveStrategy(InvestmentStrategy):
    
    def get_asset_allocation(self) -> Dict[str, float]:
        return {
            'stocks': 75.0,
            'alternative_investments': 15.0,
            'bonds': 7.0,
            'cash': 3.0
        }
    
    def get_expected_return(self) -> float:
        return 12.0
    
    def get_risk_level(self) -> str:
        return "High Risk - Maximum Growth Potential"
    
    def get_rebalancing_threshold(self) -> float:
        return 10.0
    
    def get_recommendations(self) -> List[str]:
        return [
            "Focus on growth stocks and emerging markets",
            "Include small-cap and mid-cap stocks for higher returns",
            "Consider sector-specific funds (tech, healthcare)",
            "Explore alternative investments (crypto, commodities)",
            "Long-term horizon required (10+ years)",
            "Be prepared for market volatility"
        ]

class StrategyFactory:
    
    @staticmethod
    def create_strategy(risk_profile: str) -> InvestmentStrategy:
        
        risk_profile = risk_profile.lower().strip()
        
        if risk_profile in ['low', 'conservative']:
            return ConservativeStrategy()
        elif risk_profile in ['medium', 'moderate', 'balanced']:
            return ModerateStrategy()
        elif risk_profile in ['high', 'aggressive']:
            return AggressiveStrategy()
        else:
            return ModerateStrategy()
    
    @staticmethod
    def get_available_strategies() -> List[Dict[str, str]]:
        
        return [
            {
                'name': 'Conservative',
                'risk_profile': 'Low',
                'description': 'Low risk, steady returns, capital preservation',
                'expected_return': '6.5%'
            },
            {
                'name': 'Moderate',
                'risk_profile': 'Medium',
                'description': 'Balanced risk-return, diversified portfolio',
                'expected_return': '9.0%'
            },
            {
                'name': 'Aggressive',
                'risk_profile': 'High',
                'description': 'High risk, maximum growth potential',
                'expected_return': '12.0%'
            }
        ]
