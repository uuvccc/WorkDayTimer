from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication

from workday_timer.config import config
from workday_timer.utils.system import is_run_on_startup, toggle_run_on_startup


def create_tray_icon(app):
    """Create system tray icon"""
    tray_icon = QSystemTrayIcon()
    # Ensure the icon file exists
    if os.path.exists(config.icon_file):
        tray_icon.setIcon(QIcon(config.icon_file))
    else:
        # Use a default icon if the custom one doesn't exist
        tray_icon.setIcon(QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation))
        import logging
        logging.warning(f"Icon file not found: {config.icon_file}")
    
    # Create menu for open and exit
    menu = create_tray_menu(app)
    # Set menu to system tray icon
    tray_icon.setContextMenu(menu)
    # Show system tray icon
    tray_icon.show()
    
    return tray_icon


def create_tray_menu(app):
    """Create tray menu"""
    import os
    from PyQt5.QtWidgets import QStyle
    
    menu = QMenu()
    # Create action to open window
    open_action = QAction("Open", app)
    open_action.triggered.connect(app.moveAvatar)
    menu.addAction(open_action)

    # Create action to toggle flexible mode
    flexible_action = QAction(f"Flexible Mode: {'On' if config.is_flexible else 'Off'}", app)
    flexible_action.setCheckable(True)
    flexible_action.setChecked(config.is_flexible)
    flexible_action.triggered.connect(lambda: app.toggle_flexible_mode(flexible_action))
    menu.addAction(flexible_action)

    # Create action for custom timer
    custom_timer_action = QAction("Custom Timer", app)
    custom_timer_action.triggered.connect(app.show_custom_timer_dialog)
    menu.addAction(custom_timer_action)

    # Add update-related actions to the tray menu
    update_menu = QMenu("Update", app)
    
    # Check for updates action
    check_update_action = QAction("Check for Updates", app)
    from workday_timer.updater.updater import update_application
    check_update_action.triggered.connect(lambda: update_application(app))
    update_menu.addAction(check_update_action)
    
    # Update settings action
    settings_action = QAction("Update Settings", app)
    def show_update_settings():
        from workday_timer.updater.updater import Updater
        updater = Updater(app)
        updater.show_config_ui()
    settings_action.triggered.connect(show_update_settings)
    update_menu.addAction(settings_action)
    
    # Update history action
    history_action = QAction("Update History", app)
    def show_update_history():
        from workday_timer.updater.updater import Updater
        updater = Updater(app)
        updater.show_history_ui()
    history_action.triggered.connect(show_update_history)
    update_menu.addAction(history_action)
    
    menu.addMenu(update_menu)

    # Add a startup action to the tray menu
    startup_action = QAction(f"Run on Startup: {'On' if is_run_on_startup() else 'Off'}", app)
    startup_action.setCheckable(True)
    startup_action.setChecked(is_run_on_startup())
    startup_action.triggered.connect(toggle_run_on_startup)
    menu.addAction(startup_action)

    # Create action to exit program
    exit_action = QAction("Exit", app)
    exit_action.triggered.connect(app.exit_app)
    menu.addAction(exit_action)
    
    return menu


def create_error_tray(app, error_message):
    """Create a simple tray icon for error reporting"""
    import os
    from PyQt5.QtWidgets import QStyle
    
    tray_icon = QSystemTrayIcon()
    if os.path.exists(config.icon_file):
        tray_icon.setIcon(QIcon(config.icon_file))
    else:
        tray_icon.setIcon(QApplication.style().standardIcon(QStyle.SP_MessageBoxCritical))
    
    menu = QMenu()
    exit_action = QAction("Exit", None)
    exit_action.triggered.connect(app.quit)
    menu.addAction(exit_action)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()
    tray_icon.showMessage("WorkDayTimer Error", f"An error occurred: {error_message}", QSystemTrayIcon.Critical, 5000)
    
    return tray_icon

# Add missing imports
import os
from PyQt5.QtWidgets import QStyle
