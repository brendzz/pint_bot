from bot.config import ECONOMY_HEALTH_MESSAGES, SECRET_ECONOMY_MESSAGES
from fractions import Fraction

def get_economy_health(total_in_circulation: Fraction) -> str:
    economy_health_message=max(
            (
                health
                for health in ECONOMY_HEALTH_MESSAGES
                if total_in_circulation >= health["threshold"]
            ),
            key=lambda h: h["threshold"],
            default={"message": "The economy is in an unknown state"}
        )["message"]
    return economy_health_message

def get_secret_message(total_in_circulation: Fraction) -> str:
    secret_message = SECRET_ECONOMY_MESSAGES.get(total_in_circulation)
    if secret_message:
        return f"\n{secret_message}"
    else:
        return ""