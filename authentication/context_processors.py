from .models import UserThemePreference


def user_theme_preferences(request):
    """
    Context processor to add user theme preferences to all templates
    """
    if request.user.is_authenticated:
        try:
            theme_preference = request.user.theme_preference
            return {
                "user_theme": {
                    "mode": theme_preference.theme_mode,
                    "primary_color": theme_preference.primary_color,
                    "secondary_color": theme_preference.secondary_color,
                    "accent_color": theme_preference.accent_color,
                    "background_color": theme_preference.background_color,
                    "text_color": theme_preference.text_color,
                    "sidebar_color": theme_preference.sidebar_color,
                    "card_color": theme_preference.card_color,
                }
            }
        except UserThemePreference.DoesNotExist:
            # Return default theme if no preference is set
            return {
                "user_theme": {
                    "mode": "light",
                    "primary_color": "#3498db",
                    "secondary_color": "#2c3e50",
                    "accent_color": "#e74c3c",
                    "background_color": "#f8f9fa",
                    "text_color": "#343a40",
                    "sidebar_color": "#2c3e50",
                    "card_color": "#ffffff",
                }
            }
    else:
        # Return default theme for anonymous users
        return {
            "user_theme": {
                "mode": "light",
                "primary_color": "#3498db",
                "secondary_color": "#2c3e50",
                "accent_color": "#e74c3c",
                "background_color": "#f8f9fa",
                "text_color": "#343a40",
                "sidebar_color": "#2c3e50",
                "card_color": "#ffffff",
            }
        }
