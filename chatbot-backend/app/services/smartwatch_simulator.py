"""Smartwatch data simulator for testing."""
import random
from app.models.schemas import DadosFisiologicos


class SmartWatchSimulator:
    """Simulate smartwatch physiological data."""
    
    @staticmethod
    def generate_data() -> DadosFisiologicos:
        """Generate random but realistic physiological data."""
        # Generate realistic values with some variation
        return DadosFisiologicos(
            frequencia_cardiaca=random.randint(60, 100),  # Normal range: 60-100 BPM
            saturacao_oxigenio=random.randint(95, 100),   # Normal range: 95-100%
            pressao_arterial_sistolica=random.randint(110, 130),  # Normal range: 110-130 mmHg
            pressao_arterial_diastolica=random.randint(70, 85),   # Normal range: 70-85 mmHg
            temperatura_corporal=round(random.uniform(36.1, 37.2), 1)  # Normal range: 36.1-37.2°C
        )


# Global smartwatch simulator instance
smartwatch_simulator = SmartWatchSimulator()
