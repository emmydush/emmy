def user_theme_preferences(request):
    """
    Context processor to add user theme preferences to all templates
    """
    # Return default theme for all users since theme functionality has been removed
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
