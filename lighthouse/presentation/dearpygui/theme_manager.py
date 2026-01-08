"""
Theme manager for DearPyGui.

Handles visual theming for the Lighthouse application.
"""

from typing import Tuple


class ThemeManager:
    """
    Manages visual themes for the DearPyGui interface.

    Provides centralized theme configuration including:
    - Global application theme
    - Button themes (delete, execute, context)
    - Font configuration
    """

    # Color constants
    WINDOW_BG = (20, 23, 28, 255)
    CHILD_BG = (25, 28, 35, 255)
    FRAME_BG = (35, 40, 50, 255)
    FRAME_BG_HOVERED = (45, 50, 65, 255)
    FRAME_BG_ACTIVE = (55, 60, 75, 255)
    TITLE_BG = (25, 28, 35, 255)
    TITLE_BG_ACTIVE = (30, 35, 45, 255)

    # Accent colors
    HEADER = (60, 100, 180, 80)
    HEADER_HOVERED = (70, 110, 200, 120)
    HEADER_ACTIVE = (80, 120, 220, 150)

    # Button colors
    DELETE_BUTTON = (180, 50, 50, 120)
    DELETE_BUTTON_HOVERED = (200, 60, 60, 180)
    DELETE_BUTTON_ACTIVE = (220, 70, 70, 220)

    EXECUTE_BUTTON = (50, 150, 80, 200)
    EXECUTE_BUTTON_HOVERED = (60, 170, 95, 230)
    EXECUTE_BUTTON_ACTIVE = (70, 190, 110, 255)

    CONTEXT_BUTTON = (55, 95, 170, 150)
    CONTEXT_BUTTON_HOVERED = (65, 105, 190, 200)
    CONTEXT_BUTTON_ACTIVE = (75, 115, 210, 255)

    def __init__(self):
        """Initialize theme manager."""
        self._themes_created = False

    def setup_themes(self) -> None:
        """
        Create and register all application themes.

        Must be called after dpg.create_context().
        """
        import dearpygui.dearpygui as dpg

        if self._themes_created:
            return

        self._create_global_theme(dpg)
        self._create_button_themes(dpg)

        dpg.bind_theme("global_theme")
        self._themes_created = True

    def _create_global_theme(self, dpg) -> None:
        """Create the global application theme."""
        with dpg.theme(tag="global_theme"):
            with dpg.theme_component(dpg.mvAll):
                # Rounded corners
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 8)

                # Padding and spacing
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)

                # Colors
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, self.WINDOW_BG)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, self.CHILD_BG)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, self.FRAME_BG)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, self.FRAME_BG_HOVERED)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, self.FRAME_BG_ACTIVE)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, self.TITLE_BG)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, self.TITLE_BG_ACTIVE)
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, self.CHILD_BG)
                dpg.add_theme_color(dpg.mvThemeCol_Header, self.HEADER)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, self.HEADER_HOVERED)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, self.HEADER_ACTIVE)
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (40, 45, 55, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (60, 100, 180, 200))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (55, 95, 170, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, self.CHILD_BG)
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (60, 65, 75, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (70, 75, 90, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (80, 85, 100, 255))

    def _create_button_themes(self, dpg) -> None:
        """Create button-specific themes."""
        # Delete button theme
        with dpg.theme(tag="delete_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.DELETE_BUTTON)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, self.DELETE_BUTTON_HOVERED)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, self.DELETE_BUTTON_ACTIVE)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

        # Execute button theme
        with dpg.theme(tag="execute_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 4)
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.EXECUTE_BUTTON)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, self.EXECUTE_BUTTON_HOVERED)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, self.EXECUTE_BUTTON_ACTIVE)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

        # Context menu button theme
        with dpg.theme(tag="context_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.CONTEXT_BUTTON)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, self.CONTEXT_BUTTON_HOVERED)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, self.CONTEXT_BUTTON_ACTIVE)

    def setup_fonts(self, font_path: str, size: int = 17) -> None:
        """
        Setup application fonts.

        Args:
            font_path: Path to the font file (.ttf or .otf)
            size: Font size in pixels
        """
        import dearpygui.dearpygui as dpg

        with dpg.font_registry():
            default_font = dpg.add_font(font_path, size)

        dpg.bind_font(default_font)
