from tkinter.ttk import Style


class BaseTheme:
    """Base theme with default layout and reusable settings."""
    colors = {
        "primary": "#000000",
        "secondary": "#FFFFFF",
        "background": "#FAFAFA",
        "light_bg": "#F0F0F0",
        "text": "#000000",
        "accent": "#CCCCCC",
        "highlight": "#888888",
        "progress_bg": "#888888",
        "progress_trough": "#F0F0F0",
    }

    @classmethod
    def apply_style(cls, style: Style):
        """Apply a consistent theme style using the theme's color set."""
        colors = cls.colors

        # Frame and Label
        style.configure("TFrame", background=colors["background"])
        style.configure("TLabel", background=colors["background"], foreground=colors["text"])

        # Button
        style.configure("TButton", background=colors["primary"], foreground="white", padding=(10, 5))

        # Entry
        style.configure("TEntry", fieldbackground=colors["light_bg"], foreground=colors["text"])

        # Combobox
        style.configure("TCombobox", fieldbackground=colors["background"], background=colors["primary"],
                        foreground=colors["text"], arrowcolor=colors["secondary"])

        # Label frame and its label
        style.configure("TLabelframe", background=colors["background"], foreground=colors["text"])
        style.configure("TLabelframe.Label", background=colors["background"], foreground=colors["text"],
                        font=("Helvetica", 10, "bold"))  # Bolder font for labels

        # Progress bar
        style.configure("Horizontal.TProgressbar", troughcolor=colors["progress_trough"],
                        background=colors["progress_bg"])

        # Button state configuration
        style.map("TButton",
                  background=[('active', colors["highlight"]), ('pressed', colors["secondary"]),
                              ('disabled', '#CCCCCC')],
                  foreground=[('active', colors["primary"]), ('pressed', 'white'), ('disabled', '#666666')])

    @classmethod
    def get_colors(cls):
        """Retrieve the theme's color dictionary for widget customization."""
        return {
            "bg": cls.colors["background"],
            "fg": cls.colors["text"],
            "entry_bg": cls.colors["light_bg"],
            "entry_fg": cls.colors["text"],
            "listbox_bg": cls.colors["light_bg"],
            "listbox_fg": cls.colors["text"],
            "text_bg": cls.colors["light_bg"],
            "text_fg": cls.colors["text"],
            "progress_bg": cls.colors["progress_bg"],
            "progress_trough": cls.colors["progress_trough"],
            "highlight": cls.colors["highlight"],
            "accent": cls.colors["accent"]
        }


class ShibaInuTheme(BaseTheme):
    colors = {
        "primary": "#F00500",
        "secondary": "#FFFFFF",
        "background": "#FFC98D",
        "light_bg": "#FFFFFF",
        "text": "#000000",  # High contrast against background
        "accent": "#FFA409",
        "highlight": "#FFB800",
        "progress_bg": "#F00500",
        "progress_trough": "#FFC98D",
    }


class Win311Theme(BaseTheme):
    colors = {
        "primary": "#000080",
        "secondary": "#FFFFFF",
        "background": "#D3D3D3",  # Lighter gray for better contrast
        "light_bg": "#FFFFFF",
        "text": "#000000",
        "accent": "#808080",
        "highlight": "#606080",
        "progress_bg": "#000080",
        "progress_trough": "#D3D3D3",
    }


class ClearBlueTheme(BaseTheme):
    colors = {
        "primary": "#0177B7",  # Darker blue for higher contrast
        "secondary": "#FFFFFF",
        "background": "#E8F6FF",
        "light_bg": "#D0E8FF",
        "text": "#003366",  # Darker text for clarity
        "accent": "#90C0C6",
        "highlight": "#6DA3D7",
        "progress_bg": "#0177B7",
        "progress_trough": "#E8F6FF",
    }


class WinampTheme(BaseTheme):
    colors = {
        "primary": "#F1D579",  # Bold yellow
        "secondary": "#444444",  # Mid-tone gray for clarity
        "background": "#303030",  # Darker gray
        "light_bg": "#444444",  # Lighter gray for entries
        "text": "#F1D579",  # High contrast yellow text
        "accent": "#808080",
        "highlight": "#505050",
        "progress_bg": "#F1D579",
        "progress_trough": "#444444",
    }


class DeusExTheme(BaseTheme):
    colors = {
        "primary": "#FFD700",
        "secondary": "#00AA00",
        "background": "#000000",  # Black background
        "light_bg": "#1A1A1A",  # Slightly lighter for input fields
        "text": "#00FF00",  # Bright green for high contrast
        "accent": "#008000",
        "highlight": "#FFD700",
        "progress_bg": "#FFD700",
        "progress_trough": "#1A1A1A",
    }


class BlackAndWhiteTheme(BaseTheme):
    colors = {
        "primary": "#000000",
        "secondary": "#FFFFFF",
        "background": "#FFFFFF",
        "light_bg": "#FFFFFF",
        "text": "#000000",  # Black text on white background
        "accent": "#CCCCCC",
        "highlight": "#808080",
        "progress_bg": "#000000",
        "progress_trough": "#FFFFFF",
    }


class SepiaTheme(BaseTheme):
    colors = {
        "primary": "#5A3D2B",
        "secondary": "#F5E3D9",
        "background": "#DEB887",
        "light_bg": "#EED5B7",  # Slightly lighter for inputs
        "text": "#4A2F22",  # Darker brown for text contrast
        "accent": "#A87D53",
        "highlight": "#7A5237",
        "progress_bg": "#5A3D2B",
        "progress_trough": "#EED5B7",
    }


class HelloKittyTheme(BaseTheme):
    colors = {
        "primary": "#FF69B4",
        "secondary": "#FFFFFF",
        "background": "#FFC0CB",
        "light_bg": "#FFE4E5",  # Lighter background for inputs
        "text": "#880E4F",  # Darker pink for better contrast
        "accent": "#FF69B4",
        "highlight": "#F06292",
        "progress_bg": "#FF69B4",
        "progress_trough": "#FFE4E5",
    }


class PastelTheme(BaseTheme):
    colors = {
        "primary": "#607D8B",  # Muted blue-gray
        "secondary": "#ECEFF1",  # Very light for contrast
        "background": "#CFD8DC",
        "light_bg": "#ECEFF1",  # Light for inputs
        "text": "#37474F",  # Dark text for better readability
        "accent": "#90A4AE",
        "highlight": "#78909C",
        "progress_bg": "#607D8B",
        "progress_trough": "#ECEFF1",
    }


class aiNSPIREDTheme(BaseTheme):
    colors = {
        "primary": "#2D3047",
        "secondary": "#76E4B8",
        "background": "#D5E6F7",
        "light_bg": "#F0F8FF",  # Lighter for input fields
        "text": "#1B2838",  # Darker blue-gray for text
        "accent": "#E0B1CB",
        "highlight": "#76E4B8",
        "progress_bg": "#419D78",
        "progress_trough": "#D5E6F7",
    }

class ThemeManager:
    THEMES = {
        "SHIBA INU": ShibaInuTheme,
        "WIN311": Win311Theme,
        "CLEAR BLUE": ClearBlueTheme,
        "WINAMP": WinampTheme,
        "DEUS EX": DeusExTheme,
        "BLACK AND WHITE": BlackAndWhiteTheme,
        "SEPIA": SepiaTheme,
        "HELLO KITTY": HelloKittyTheme,
        "PASTEL": PastelTheme,
        "AI NSPIRED": aiNSPIREDTheme,
    }

    @classmethod
    def get_theme(cls, theme_name):
        """Retrieve a theme class by name from the available themes."""
        return cls.THEMES.get(theme_name)
