# Autocliicker/autopresser script using pynput for all keys
from pynput.keyboard import Controller, Listener, KeyCode
from pynput.mouse import Listener as MouseListener, Button, Controller as MouseController
import time
import random
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon, QPixmap
import sys
import ctypes
import json
import os

keyboard = Controller()
mouse = MouseController()
stop_flag = False
listener = None
PRESETS_FILE = "autoclicker_presets.json"
SETTINGS_FILE = "autoclicker_settings.json"

class KeyListenerThread(QThread):
    key_captured = Signal(str)
    finished = Signal()
    
    def __init__(self):
        super().__init__()
        self.captured_key = None
    
    def run(self):
        # Small delay to let the button click event fully process
        time.sleep(0.2)
        
        def on_key_press(key):
            try:
                if hasattr(key, 'char') and key.char:
                    self.captured_key = key.char
                elif hasattr(key, 'name'):
                    self.captured_key = key.name
                else:
                    self.captured_key = str(key)
            except:
                self.captured_key = str(key)
            return False  # Stop listener
        
        def on_mouse_click(x, y, button, pressed):
            if pressed:
                self.captured_key = f"{button.name}_click"
                return False  # Stop listener
        
        keyboard_listener = None
        mouse_listener = None
        
        try:
            # Create listeners
            keyboard_listener = Listener(on_press=on_key_press)
            mouse_listener = MouseListener(on_click=on_mouse_click)
            
            keyboard_listener.start()
            mouse_listener.start()
            
            # Wait for input (with timeout)
            for _ in range(100):  # 10 second timeout
                if self.captured_key:
                    break
                time.sleep(0.1)
        finally:
            # Ensure listeners are stopped
            if keyboard_listener:
                keyboard_listener.stop()
            if mouse_listener:
                mouse_listener.stop()
            
            # Emit signal with captured key
            if self.captured_key:
                self.key_captured.emit(self.captured_key)
            
            self.finished.emit()

class AutoClickerThread(QThread):
    time_remaining = Signal(int)
    countdown = Signal(int)
    finished = Signal()
    
    def __init__(self, key, times, hold_duration, delay_between, abort_key, initial_delay, countdown_duration, show_countdown, randomness_range, endless_mode=False):
        super().__init__()
        self.key = key
        self.times = times
        self.hold_duration = hold_duration
        self.delay_between = delay_between
        self.abort_key = abort_key
        self.initial_delay = initial_delay
        self.countdown_duration = countdown_duration
        self.show_countdown = show_countdown
        self.randomness_range = randomness_range
        self.endless_mode = endless_mode
        self.should_stop = False
    
    def run(self):
        global stop_flag, listener, keyboard
        stop_flag = False
        
        def on_press(key):
            global stop_flag
            try:
                key_str = None
                if hasattr(key, 'char') and key.char:
                    key_str = key.char
                elif hasattr(key, 'name'):
                    key_str = key.name
                else:
                    key_str = str(key)
                
                # Check if this is the abort key
                if key_str == self.abort_key:
                    print(f"\n{self.abort_key} pressed - Aborting!")
                    stop_flag = True
                    self.should_stop = True
                    return False
            except:
                pass
                pass
        
        listener = Listener(on_press=on_press)
        listener.start()
        
        # Initial delay
        for i in range(int(self.initial_delay * 10)):
            if stop_flag or self.should_stop:
                if listener:
                    listener.stop()
                self.finished.emit()
                return
            time.sleep(0.1)
        
        # Countdown before starting (only if show_countdown is True)
        if self.show_countdown:
            for i in range(self.countdown_duration, 0, -1):
                if stop_flag or self.should_stop:
                    if listener:
                        listener.stop()
                    self.finished.emit()
                    return
                self.countdown.emit(i)
                time.sleep(1)
            
            self.countdown.emit(0)  # Clear countdown
        else:
            self.countdown.emit(0)  # Clear countdown immediately
        
        # Use while loop for endless mode, for loop for normal mode
        if self.endless_mode:
            iteration = 0
            while not (stop_flag or self.should_stop):
                iteration += 1
                self.time_remaining.emit(iteration)  # Show iteration count
                
                # Check if this is a mouse button
                is_mouse_button = self.key.endswith("_click")
                
                if is_mouse_button:
                    # Handle mouse button
                    button_name = self.key.replace("_click", "")
                    try:
                        button = Button[button_name]
                    except KeyError:
                        # Fallback to left if button not recognized
                        button = Button.left
                    
                    # Simulate holding by pressing repeatedly
                    press_count = int(self.hold_duration / 0.1)
                    for _ in range(press_count):
                        if stop_flag or self.should_stop:
                            break
                        mouse.press(button)
                        time.sleep(0.1)
                    
                    if not (stop_flag or self.should_stop):
                        mouse.release(button)
                else:
                    # Handle keyboard key
                    # Simulate holding by pressing repeatedly
                    press_count = int(self.hold_duration / 0.1)
                    for _ in range(press_count):
                        if stop_flag or self.should_stop:
                            break
                        keyboard.press(self.key)
                        time.sleep(0.1)
                    
                    if not (stop_flag or self.should_stop):
                        keyboard.release(self.key)
                
                # Calculate delay with randomness
                if not (stop_flag or self.should_stop):
                    delay = self.delay_between
                    if self.randomness_range > 0:
                        delay += random.uniform(0, self.randomness_range)
                    time.sleep(delay)
        else:
            for i in range(self.times):
                if stop_flag or self.should_stop:
                    break
                
                remaining = self.times - i
                self.time_remaining.emit(remaining)
                
                # Check if this is a mouse button
                is_mouse_button = self.key.endswith("_click")
                
                if is_mouse_button:
                    # Handle mouse button
                    button_name = self.key.replace("_click", "")
                    try:
                        button = Button[button_name]
                    except KeyError:
                        # Fallback to left if button not recognized
                        button = Button.left
                    
                    # Simulate holding by pressing repeatedly
                    press_count = int(self.hold_duration / 0.1)
                    for _ in range(press_count):
                        if stop_flag or self.should_stop:
                            break
                        mouse.press(button)
                        time.sleep(0.1)
                    
                    if not (stop_flag or self.should_stop):
                        mouse.release(button)
                else:
                    # Handle keyboard key
                    # Simulate holding by pressing repeatedly
                    press_count = int(self.hold_duration / 0.1)
                    for _ in range(press_count):
                        if stop_flag or self.should_stop:
                            break
                        keyboard.press(self.key)
                        time.sleep(0.1)
                    
                    if not (stop_flag or self.should_stop):
                        keyboard.release(self.key)
                
                # Calculate delay with randomness
                if not (stop_flag or self.should_stop):
                    delay = self.delay_between
                    if self.randomness_range > 0:
                        delay += random.uniform(0, self.randomness_range)
                    time.sleep(delay)
        
        if listener:
            listener.stop()
        self.finished.emit()


class AutoPresserApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kold's Tools")
        self.setGeometry(100, 100, 500, 400)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
        self.clicker_thread = None
        self.presets = self.load_presets()
        self.abort_key = "num_lock"  # Default abort key
        self.auto_start = True  # Auto start after countdown
        self.show_countdown = True  # Show countdown before starting
        # Internal flag to prevent reload recursion when re-applying settings
        self._suppress_tab_reload = False
        # Icon paths (empty string = default)
        self.window_icon_path = ""
        self.app_icon_path = ""
        
        # Load settings from file
        self.load_settings()
        
        # Create tab widget
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tab 1: Settings
        self.tab1 = QtWidgets.QWidget()
        self.setup_tab1()
        self.tabs.addTab(self.tab1, "Main")
        
        # Tab 2: Presets
        self.tab2 = QtWidgets.QWidget()
        self.setup_tab2()
        self.tabs.addTab(self.tab2, "Presets")
        
        # Tab 3: Settings
        self.tab3 = QtWidgets.QWidget()
        self.setup_tab3()
        self.tabs.addTab(self.tab3, "Settings")
        
        # Tab 4: About
        self.tab4 = QtWidgets.QWidget()
        self.setup_tab4()
        self.tabs.addTab(self.tab4, "About")
        
        # Apply loaded settings to UI
        self.apply_settings()
    
    def setup_tab1(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Key selection
        key_layout = QtWidgets.QHBoxLayout()
        key_layout.addWidget(QtWidgets.QLabel("Key/Button to repeat:"))
        self.key_display = QtWidgets.QLineEdit()
        self.key_display.setText("e")
        self.key_display.setReadOnly(True)
        key_layout.addWidget(self.key_display)
        
        self.listen_button = QtWidgets.QPushButton("Listen")
        self.listen_button.clicked.connect(self.start_listening_for_key)
        key_layout.addWidget(self.listen_button)
        layout.addLayout(key_layout)
        
        # Endless mode checkbox
        self.endless_mode_checkbox = QtWidgets.QCheckBox("Endless Mode (until abort key pressed)")
        self.endless_mode_checkbox.stateChanged.connect(self.on_endless_mode_changed)
        layout.addWidget(self.endless_mode_checkbox)
        
        # Repetitions
        reps_layout = QtWidgets.QHBoxLayout()
        reps_layout.addWidget(QtWidgets.QLabel("Repetitions:"))
        self.reps_spinbox = QtWidgets.QSpinBox()
        self.reps_spinbox.setMinimum(1)
        self.reps_spinbox.setMaximum(10000)
        self.reps_spinbox.setValue(10)
        reps_layout.addWidget(self.reps_spinbox)
        layout.addLayout(reps_layout)
        
        # Hold duration
        hold_layout = QtWidgets.QHBoxLayout()
        self.hold_label = QtWidgets.QLabel("Hold duration (seconds):")
        hold_layout.addWidget(self.hold_label)
        self.hold_spinbox = QtWidgets.QDoubleSpinBox()
        self.hold_spinbox.setMinimum(0.1)
        self.hold_spinbox.setMaximum(10.0)
        self.hold_spinbox.setValue(1.0)
        self.hold_spinbox.setSingleStep(0.1)
        hold_layout.addWidget(self.hold_spinbox)
        layout.addLayout(hold_layout)
        
        # Delay between presses
        delay_layout = QtWidgets.QHBoxLayout()
        self.delay_label = QtWidgets.QLabel("Delay between (seconds):")
        delay_layout.addWidget(self.delay_label)
        self.delay_spinbox = QtWidgets.QDoubleSpinBox()
        self.delay_spinbox.setMinimum(0.1)
        self.delay_spinbox.setMaximum(10.0)
        self.delay_spinbox.setValue(0.5)
        self.delay_spinbox.setSingleStep(0.1)
        delay_layout.addWidget(self.delay_spinbox)
        layout.addLayout(delay_layout)
        
        # Randomness range
        randomness_layout = QtWidgets.QHBoxLayout()
        randomness_layout.addWidget(QtWidgets.QLabel("Randomness range (seconds):"))
        self.randomness_spinbox = QtWidgets.QDoubleSpinBox()
        self.randomness_spinbox.setMinimum(0.0)
        self.randomness_spinbox.setMaximum(10.0)
        self.randomness_spinbox.setValue(0.0)
        self.randomness_spinbox.setSingleStep(0.1)
        randomness_layout.addWidget(self.randomness_spinbox)
        layout.addLayout(randomness_layout)
        
        # Hold preset checkbox
        self.hold_preset_checkbox = QtWidgets.QCheckBox("Quick hold (1s hold, 0.5s delay)")
        self.hold_preset_checkbox.stateChanged.connect(self.on_hold_preset_changed)
        layout.addWidget(self.hold_preset_checkbox)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.start_autoclicker)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_autoclicker)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Status section
        layout.addWidget(QtWidgets.QLabel("\nStatus:"))
        
        self.status_text = QtWidgets.QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setText("Not running")
        self.status_text.setMaximumHeight(100)
        layout.addWidget(self.status_text)
        
        time_label = QtWidgets.QLabel("Time Remaining:")
        layout.addWidget(time_label)
        
        self.time_remaining_label = QtWidgets.QLabel("0 repetitions left")
        self.time_remaining_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.time_remaining_label)
        
        countdown_label = QtWidgets.QLabel("Starting In:")
        layout.addWidget(countdown_label)
        
        self.countdown_label = QtWidgets.QLabel("")
        self.countdown_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
        layout.addWidget(self.countdown_label)
        
        layout.addStretch()
        
        self.tab1.setLayout(layout)
    
    def setup_tab2(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Preset name input
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("Preset name:"))
        self.preset_name_input = QtWidgets.QLineEdit()
        name_layout.addWidget(self.preset_name_input)
        layout.addLayout(name_layout)
        
        # Save button
        save_preset_button = QtWidgets.QPushButton("Save Current Settings as Preset")
        save_preset_button.clicked.connect(self.save_preset)
        layout.addWidget(save_preset_button)
        
        # Presets list
        list_label = QtWidgets.QLabel("Saved Presets:")
        layout.addWidget(list_label)
        
        self.presets_list = QtWidgets.QListWidget()
        self.presets_list.itemDoubleClicked.connect(self.load_selected_preset)
        layout.addWidget(self.presets_list)
        
        # Buttons layout
        button_layout = QtWidgets.QHBoxLayout()
        
        load_button = QtWidgets.QPushButton("Load Selected")
        load_button.clicked.connect(self.load_selected_preset)
        button_layout.addWidget(load_button)
        
        delete_button = QtWidgets.QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_selected_preset)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
        
        self.tab2.setLayout(layout)
        self.refresh_presets_list()
    
    def setup_tab3(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Abort key selection
        abort_key_layout = QtWidgets.QHBoxLayout()
        abort_key_layout.addWidget(QtWidgets.QLabel("Abort Key:"))
        self.abort_key_display = QtWidgets.QLineEdit()
        self.abort_key_display.setText(self.abort_key)
        self.abort_key_display.setReadOnly(True)
        abort_key_layout.addWidget(self.abort_key_display)
        
        self.abort_listen_button = QtWidgets.QPushButton("Listen")
        self.abort_listen_button.clicked.connect(self.start_listening_for_abort_key)
        abort_key_layout.addWidget(self.abort_listen_button)
        layout.addLayout(abort_key_layout)
        
        # Auto-start checkbox
        self.auto_start_checkbox = QtWidgets.QCheckBox("Auto-start after countdown")
        self.auto_start_checkbox.setChecked(self.auto_start)
        self.auto_start_checkbox.stateChanged.connect(self.on_auto_start_changed)
        layout.addWidget(self.auto_start_checkbox)
        
        # Show countdown checkbox
        self.show_countdown_checkbox = QtWidgets.QCheckBox("Show countdown before starting")
        self.show_countdown_checkbox.setChecked(self.show_countdown)
        self.show_countdown_checkbox.stateChanged.connect(self.on_show_countdown_changed)
        layout.addWidget(self.show_countdown_checkbox)

        # Remember settings between sessions
        self.remember_settings_checkbox = QtWidgets.QCheckBox("Remember settings between sessions")
        # Default to True if not present
        self.remember_settings_checkbox.setChecked(getattr(self, 'remember_settings', True))
        self.remember_settings_checkbox.stateChanged.connect(self.on_remember_settings_changed)
        layout.addWidget(self.remember_settings_checkbox)

        # Window icon selector
        window_icon_layout = QtWidgets.QHBoxLayout()
        window_icon_layout.addWidget(QtWidgets.QLabel("Window Icon:"))
        self.window_icon_path_input = QtWidgets.QLineEdit()
        self.window_icon_path_input.setReadOnly(True)
        self.window_icon_path_input.setText(getattr(self, 'window_icon_path', ""))
        window_icon_layout.addWidget(self.window_icon_path_input)
        self.window_icon_browse = QtWidgets.QPushButton("Browse")
        self.window_icon_browse.clicked.connect(self.browse_window_icon)
        window_icon_layout.addWidget(self.window_icon_browse)
        self.window_icon_clear = QtWidgets.QPushButton("Clear")
        self.window_icon_clear.clicked.connect(self.clear_window_icon)
        window_icon_layout.addWidget(self.window_icon_clear)
        self.window_icon_preview = QtWidgets.QLabel()
        self.window_icon_preview.setFixedSize(32, 32)
        window_icon_layout.addWidget(self.window_icon_preview)
        layout.addLayout(window_icon_layout)

        # Application icon selector
        app_icon_layout = QtWidgets.QHBoxLayout()
        app_icon_layout.addWidget(QtWidgets.QLabel("Application Icon:"))
        self.app_icon_path_input = QtWidgets.QLineEdit()
        self.app_icon_path_input.setReadOnly(True)
        self.app_icon_path_input.setText(getattr(self, 'app_icon_path', ""))
        app_icon_layout.addWidget(self.app_icon_path_input)
        self.app_icon_browse = QtWidgets.QPushButton("Browse")
        self.app_icon_browse.clicked.connect(self.browse_app_icon)
        app_icon_layout.addWidget(self.app_icon_browse)
        self.app_icon_clear = QtWidgets.QPushButton("Clear")
        self.app_icon_clear.clicked.connect(self.clear_app_icon)
        app_icon_layout.addWidget(self.app_icon_clear)
        self.app_icon_preview = QtWidgets.QLabel()
        self.app_icon_preview.setFixedSize(32, 32)
        app_icon_layout.addWidget(self.app_icon_preview)
        layout.addLayout(app_icon_layout)

        # Initial delay
        delay_layout = QtWidgets.QHBoxLayout()
        delay_layout.addWidget(QtWidgets.QLabel("Initial delay before countdown (seconds):"))
        self.initial_delay_spinbox = QtWidgets.QDoubleSpinBox()
        self.initial_delay_spinbox.setMinimum(0.0)
        self.initial_delay_spinbox.setMaximum(60.0)
        self.initial_delay_spinbox.setValue(0.0)
        self.initial_delay_spinbox.setSingleStep(0.5)
        delay_layout.addWidget(self.initial_delay_spinbox)
        layout.addLayout(delay_layout)
        
        # Countdown duration
        countdown_layout = QtWidgets.QHBoxLayout()
        countdown_layout.addWidget(QtWidgets.QLabel("Countdown duration (seconds):"))
        self.countdown_duration_spinbox = QtWidgets.QSpinBox()
        self.countdown_duration_spinbox.setMinimum(0)
        self.countdown_duration_spinbox.setMaximum(60)
        self.countdown_duration_spinbox.setValue(5)
        countdown_layout.addWidget(self.countdown_duration_spinbox)
        layout.addLayout(countdown_layout)
        
        layout.addStretch()
        self.tab3.setLayout(layout)
    
    def setup_tab4(self):
        layout = QtWidgets.QVBoxLayout()
        
        info_text = QtWidgets.QLabel(
            "Kold's Tools v2.0\n\n"
            "A simple auto clicker/presser tool.\n\n"
            "Key Features:\n"
            "• Customizable key/button selection\n"
            "• Adjustable hold duration, delay, and randomness\n"
            "• Quick Hold preset (1s hold, 0.5s delay) — grays and disables Hold/Delay when active\n"
            "• Remember settings between sessions (toggle in Settings)\n"
            "• Listening improvements: number keys no longer change input widgets while listening\n"
            "• Save and load presets\n\n"
            "Abort Key: Press your configured abort key (default: Num Lock) to stop execution.\n\n"
            "Tips:\n"
            "• Double-click a preset to load it\n"
            "• Use the Quick Hold checkbox to quickly set common timings"
        )
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        # Copyright / disclaimer - always visible
        copyright_label = QtWidgets.QLabel("© 2026 Kold's Tools — Use at your own risk.")
        copyright_label.setStyleSheet("font-size: 10px; color: #606060;")
        copyright_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(copyright_label)
        layout.addStretch()
        
        self.tab4.setLayout(layout)
    
    def _set_inputs_focus_enabled(self, enabled: bool):
        """Enable or disable keyboard focus for input widgets to avoid stealing keystrokes while listening."""
        policy = QtCore.Qt.StrongFocus if enabled else QtCore.Qt.NoFocus
        for w in (
            self.reps_spinbox,
            self.hold_spinbox,
            self.delay_spinbox,
            self.randomness_spinbox,
            self.initial_delay_spinbox,
            self.countdown_duration_spinbox,
        ):
            try:
                w.setFocusPolicy(policy)
            except Exception:
                pass

    def start_listening_for_key(self):
        """Start listening for keyboard or mouse input"""
        self.listen_button.setText("Listening... Press any key or click")
        self.listen_button.setEnabled(False)
        # Prevent other input widgets from stealing key events while we listen
        self._set_inputs_focus_enabled(False)
        # Keep focus on the listen button so the UI doesn't move focus elsewhere
        try:
            self.listen_button.setFocus()
        except Exception:
            pass

        # Start listening in a separate thread
        self.listener_thread = KeyListenerThread()
        self.listener_thread.key_captured.connect(self.on_key_captured)
        self.listener_thread.finished.connect(self._reset_listen_button)
        self.listener_thread.start()
    
    def on_key_captured(self, key):
        """Handle captured key from listener thread"""
        self.key_display.setText(key)
    
    def start_listening_for_abort_key(self):
        """Start listening for abort key"""
        self.abort_listen_button.setText("Listening... Press any key or click")
        self.abort_listen_button.setEnabled(False)
        # Prevent other input widgets from stealing key events while we listen for abort key
        self._set_inputs_focus_enabled(False)
        try:
            self.abort_listen_button.setFocus()
        except Exception:
            pass
        
        # Start listening in a separate thread
        self.abort_listener_thread = KeyListenerThread()
        self.abort_listener_thread.key_captured.connect(self.on_abort_key_captured)
        self.abort_listener_thread.finished.connect(self._reset_abort_listen_button)
        self.abort_listener_thread.start()
    
    def on_abort_key_captured(self, key):
        """Handle captured abort key"""
        self.abort_key_display.setText(key)
        self.abort_key = key
        self.save_settings()
    
    def _reset_abort_listen_button(self):
        """Reset the abort listen button"""
        # Restore input focus policies
        self._set_inputs_focus_enabled(True)
        self.abort_listen_button.setText("Listen")
        self.abort_listen_button.setEnabled(True)
    
    def on_auto_start_changed(self, state):
        """Handle auto-start checkbox change"""
        self.auto_start = state == QtCore.Qt.Checked
        self.save_settings()
    
    def on_show_countdown_changed(self, state):
        """Handle show countdown checkbox change"""
        self.show_countdown = state == QtCore.Qt.Checked
        self.save_settings()

    def on_endless_mode_changed(self, state):
        """Handle endless mode checkbox change"""
        is_checked = state == QtCore.Qt.Checked
        # Disable/enable repetitions spinbox based on endless mode
        self.reps_spinbox.setEnabled(not is_checked)
        self.save_settings()

    def on_remember_settings_changed(self, state):
        """Handle remember-settings checkbox change"""
        self.remember_settings = state == QtCore.Qt.Checked
        self.save_settings()

    def browse_window_icon(self):
        """Open a file dialog to select a window icon"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Window Icon", "", "Images (*.png *.ico *.jpg *.bmp)")
        if path:
            self.window_icon_path = path
            self.window_icon_path_input.setText(path)
            self.apply_icons()
            self.save_settings()

    def clear_window_icon(self):
        """Clear the selected window icon (use default)"""
        self.window_icon_path = ""
        try:
            self.window_icon_path_input.setText("")
        except Exception:
            pass
        self.apply_icons()
        self.save_settings()

    def browse_app_icon(self):
        """Open a file dialog to select an application icon"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Application Icon", "", "Images (*.png *.ico *.jpg *.bmp)")
        if path:
            self.app_icon_path = path
            self.app_icon_path_input.setText(path)
            self.apply_icons()
            self.save_settings()

    def clear_app_icon(self):
        """Clear the selected application icon (use default)"""
        self.app_icon_path = ""
        try:
            self.app_icon_path_input.setText("")
        except Exception:
            pass
        self.apply_icons()
        self.save_settings()

    def apply_icons(self):
        """Apply the selected icons to the window and application and update previews.

        Behavior:
        - If user selected external icon paths exist, use them.
        - Otherwise, when running as a packaged EXE, fall back to the EXE's embedded icon
          (QIcon(sys.executable)) so Windows taskbar/titlebar shows the proper icon.
        """
        app = QtWidgets.QApplication.instance()
        # Window icon
        try:
            if getattr(self, 'window_icon_path', "") and os.path.exists(self.window_icon_path):
                icon = QIcon(self.window_icon_path)
                self.setWindowIcon(icon)
                if app:
                    app.setWindowIcon(icon)
                # update preview
                pix = QPixmap(self.window_icon_path)
                if not pix.isNull():
                    self.window_icon_preview.setPixmap(pix.scaled(32, 32, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                else:
                    self.window_icon_preview.clear()
            else:
                # No external window icon: try to use packaged exe icon as fallback
                if getattr(sys, 'frozen', False) and os.path.exists(sys.executable):
                    try:
                        exe_icon = QIcon(sys.executable)
                        self.setWindowIcon(exe_icon)
                        if app:
                            app.setWindowIcon(exe_icon)
                        pix = exe_icon.pixmap(32, 32)
                        if not pix.isNull():
                            self.window_icon_preview.setPixmap(pix)
                        else:
                            self.window_icon_preview.clear()
                    except Exception:
                        self.window_icon_preview.clear()
                else:
                    self.window_icon_preview.clear()
        except Exception:
            pass

        # Application icon (separate, if provided)
        try:
            if getattr(self, 'app_icon_path', "") and os.path.exists(self.app_icon_path):
                icon = QIcon(self.app_icon_path)
                if app:
                    app.setWindowIcon(icon)
                # update preview
                pix = QPixmap(self.app_icon_path)
                if not pix.isNull():
                    self.app_icon_preview.setPixmap(pix.scaled(32, 32, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                else:
                    self.app_icon_preview.clear()
            else:
                # No external app icon: try packaged exe icon as fallback
                if getattr(sys, 'frozen', False) and os.path.exists(sys.executable):
                    try:
                        exe_icon = QIcon(sys.executable)
                        if app:
                            app.setWindowIcon(exe_icon)
                        pix = exe_icon.pixmap(32, 32)
                        if not pix.isNull():
                            self.app_icon_preview.setPixmap(pix)
                        else:
                            self.app_icon_preview.clear()
                    except Exception:
                        self.app_icon_preview.clear()
                else:
                    self.app_icon_preview.clear()
        except Exception:
            pass
    
    def on_hold_preset_changed(self, state):
        """Handle hold preset checkbox change"""
        is_checked = state == QtCore.Qt.Checked

        # Save the preference immediately
        self.save_settings()

        if self._suppress_tab_reload:
            # Just apply UI changes without reloading the tab
            self.apply_hold_preset_ui(is_checked)
            return

        # User triggered action -> reload the tab and re-apply settings
        # Reload will rebuild widgets and apply the saved settings
        self._suppress_tab_reload = True
        try:
            self.load_settings()
            self.reload_tab1()
        finally:
            self._suppress_tab_reload = False

    def apply_hold_preset_ui(self, is_checked: bool):
        """Apply hold preset styling and enabled state without triggering reloads."""
        if is_checked:
            # Apply quick preset values and disable inputs
            self.hold_spinbox.setValue(1.0)
            self.delay_spinbox.setValue(0.5)
            self.hold_spinbox.setEnabled(False)
            self.delay_spinbox.setEnabled(False)
            # Gray out labels and spinboxes
            gray_label_style = "color: #808080;"
            gray_spinbox_style = "background-color: #e0e0e0; color: #808080;"
            self.hold_label.setStyleSheet(gray_label_style)
            self.delay_label.setStyleSheet(gray_label_style)
            self.hold_spinbox.setStyleSheet(gray_spinbox_style)
            self.delay_spinbox.setStyleSheet(gray_spinbox_style)
        else:
            # Restore normal styles and enable inputs
            self.hold_spinbox.setEnabled(True)
            self.delay_spinbox.setEnabled(True)
            self.hold_label.setStyleSheet("")
            self.delay_label.setStyleSheet("")
            self.hold_spinbox.setStyleSheet("")
            self.delay_spinbox.setStyleSheet("")

    def reload_tab1(self):
        """Rebuild the Main tab to ensure control state matches saved settings."""
        # Save current settings first
        self.save_settings()

        # Find index of existing tab1 and remove it
        index = None
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) is self.tab1:
                index = i
                break
        if index is None:
            index = 0

        self.tabs.removeTab(index)

        # Recreate tab1
        self.tab1 = QtWidgets.QWidget()
        self.setup_tab1()
        self.tabs.insertTab(index, self.tab1, "Main")
        self.tabs.setCurrentIndex(index)

        # Reload settings and apply them without triggering reload recursion
        self.load_settings()
        self._suppress_tab_reload = True
        try:
            self.apply_settings()
        finally:
            self._suppress_tab_reload = False

    def showEvent(self, event):
        """Ensure icons are applied when the window is shown (helps Windows taskbar/window icon)."""
        try:
            # Re-apply icons after the native window has been created
            self.apply_icons()
        except Exception:
            pass
        return super().showEvent(event)
    
    def _reset_listen_button(self):
        """Reset the listen button"""
        # Restore input focus policies so widgets accept keyboard input again
        self._set_inputs_focus_enabled(True)
        self.listen_button.setText("Listen")
        self.listen_button.setEnabled(True)
    
    def load_presets(self):
        """Load presets from JSON file"""
        if os.path.exists(PRESETS_FILE):
            try:
                with open(PRESETS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def load_settings(self):
        """Load settings from JSON file"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.abort_key = settings.get("abort_key", "num_lock")
                    self.auto_start = settings.get("auto_start", True)
                    self.show_countdown = settings.get("show_countdown", True)
                    self.key_value = settings.get("key", "e")
                    self.reps_value = settings.get("repetitions", 10)
                    self.hold_duration_value = settings.get("hold_duration", 1.0)
                    self.delay_between_value = settings.get("delay_between", 0.5)
                    self.randomness_range_value = settings.get("randomness_range", 0.0)
                    self.initial_delay_value = settings.get("initial_delay", 0.0)
                    self.countdown_duration_value = settings.get("countdown_duration", 5)
                    self.hold_preset_checked = settings.get("hold_preset", False)
                    self.endless_mode_checked = settings.get("endless_mode", False)
                    # Whether to apply saved settings on startup
                    self.remember_settings = settings.get("remember_settings", True)
                    # Icon paths
                    self.window_icon_path = settings.get("window_icon", "")
                    self.app_icon_path = settings.get("app_icon", "")
            except:
                pass
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            settings = {
                "abort_key": self.abort_key,
                "auto_start": self.auto_start,
                "show_countdown": self.show_countdown,
                "key": self.key_display.text(),
                "repetitions": self.reps_spinbox.value(),
                "hold_duration": self.hold_spinbox.value(),
                "delay_between": self.delay_spinbox.value(),
                "randomness_range": self.randomness_spinbox.value(),
                "initial_delay": self.initial_delay_spinbox.value(),
                "countdown_duration": self.countdown_duration_spinbox.value(),
                "hold_preset": self.hold_preset_checkbox.isChecked(),
                "endless_mode": self.endless_mode_checkbox.isChecked(),
                "remember_settings": getattr(self, 'remember_settings', True),
                "window_icon": getattr(self, 'window_icon_path', ""),
                "app_icon": getattr(self, 'app_icon_path', "")
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {str(e)}")
    
    def apply_settings(self):
        """Apply loaded settings to UI"""
        if hasattr(self, 'key_value'):
            self.key_display.setText(self.key_value)
        if hasattr(self, 'reps_value'):
            self.reps_spinbox.setValue(self.reps_value)
        if hasattr(self, 'hold_duration_value'):
            self.hold_spinbox.setValue(self.hold_duration_value)
        if hasattr(self, 'delay_between_value'):
            self.delay_spinbox.setValue(self.delay_between_value)
        if hasattr(self, 'randomness_range_value'):
            self.randomness_spinbox.setValue(self.randomness_range_value)
        if hasattr(self, 'initial_delay_value'):
            self.initial_delay_spinbox.setValue(self.initial_delay_value)
        if hasattr(self, 'countdown_duration_value'):
            self.countdown_duration_spinbox.setValue(self.countdown_duration_value)
        # Apply saved session settings only if remembering between sessions is enabled
        if getattr(self, 'remember_settings', True):
            if hasattr(self, 'key_value'):
                self.key_display.setText(self.key_value)
            if hasattr(self, 'reps_value'):
                self.reps_spinbox.setValue(self.reps_value)
            if hasattr(self, 'hold_duration_value'):
                self.hold_spinbox.setValue(self.hold_duration_value)
            if hasattr(self, 'delay_between_value'):
                self.delay_spinbox.setValue(self.delay_between_value)
            if hasattr(self, 'randomness_range_value'):
                self.randomness_spinbox.setValue(self.randomness_range_value)
            if hasattr(self, 'initial_delay_value'):
                self.initial_delay_spinbox.setValue(self.initial_delay_value)
            if hasattr(self, 'countdown_duration_value'):
                self.countdown_duration_spinbox.setValue(self.countdown_duration_value)
            if hasattr(self, 'hold_preset_checked'):
                # Set checkbox without emitting its signal and apply UI state directly
                self.hold_preset_checkbox.blockSignals(True)
                self.hold_preset_checkbox.setChecked(self.hold_preset_checked)
                self.hold_preset_checkbox.blockSignals(False)
                self.apply_hold_preset_ui(self.hold_preset_checked)
            if hasattr(self, 'endless_mode_checked'):
                # Set checkbox and disable reps spinbox if endless mode is on
                self.endless_mode_checkbox.blockSignals(True)
                self.endless_mode_checkbox.setChecked(self.endless_mode_checked)
                self.endless_mode_checkbox.blockSignals(False)
                self.reps_spinbox.setEnabled(not self.endless_mode_checked)

        # Ensure the remember checkbox reflects the saved preference
        if hasattr(self, 'remember_settings'):
            self.remember_settings_checkbox.blockSignals(True)
            self.remember_settings_checkbox.setChecked(self.remember_settings)
            self.remember_settings_checkbox.blockSignals(False)

        self.abort_key_display.setText(self.abort_key)
        self.auto_start_checkbox.setChecked(self.auto_start)
        self.show_countdown_checkbox.setChecked(self.show_countdown)

        # Set icon path inputs if set and apply icons (icons are independent of remember_settings)
        try:
            if getattr(self, 'window_icon_path', ""):
                self.window_icon_path_input.setText(self.window_icon_path)
            if getattr(self, 'app_icon_path', ""):
                self.app_icon_path_input.setText(self.app_icon_path)
        except Exception:
            pass

        # If no icons configured explicitly, look for bundled default 'logotipasKoldTools.png' next to main.py
        try:
            if not getattr(self, 'window_icon_path', "") and not getattr(self, 'app_icon_path', ""):
                bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logotipasKoldTools.png')
                if os.path.exists(bundled):
                    # Use bundled image as default icons (do not auto-save; user can Clear or Browse)
                    self.window_icon_path = bundled
                    self.app_icon_path = bundled
                    try:
                        self.window_icon_path_input.setText(bundled)
                        self.app_icon_path_input.setText(bundled)
                    except Exception:
                        pass
        except Exception:
            pass

        # Apply icons to window and app (if provided)
        try:
            self.apply_icons()
        except Exception:
            pass
    
    def save_presets_to_file(self):
        """Save presets to JSON file"""
        try:
            with open(PRESETS_FILE, 'w') as f:
                json.dump(self.presets, f, indent=2)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to save presets: {str(e)}")
    
    def refresh_presets_list(self):
        """Refresh the presets list widget"""
        self.presets_list.clear()
        for preset_name in self.presets.keys():
            self.presets_list.addItem(preset_name)
    
    def save_preset(self):
        """Save current settings as a preset"""
        preset_name = self.preset_name_input.text().strip()
        
        if not preset_name:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter a preset name")
            return
        
        # Save current settings
        self.presets[preset_name] = {
            "key": self.key_display.text(),
            "repetitions": self.reps_spinbox.value(),
            "hold_duration": self.hold_spinbox.value(),
            "delay_between": self.delay_spinbox.value()
        }
        
        self.save_presets_to_file()
        self.refresh_presets_list()
        self.preset_name_input.clear()
        QtWidgets.QMessageBox.information(self, "Success", f"Preset '{preset_name}' saved!")
    
    def load_selected_preset(self):
        """Load the selected preset"""
        selected_items = self.presets_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a preset")
            return
        
        preset_name = selected_items[0].text()
        preset = self.presets[preset_name]
        
        # Load preset values
        self.key_display.setText(preset["key"])
        self.reps_spinbox.setValue(preset["repetitions"])
        self.hold_spinbox.setValue(preset["hold_duration"])
        self.delay_spinbox.setValue(preset["delay_between"])
        
        # Switch to Settings tab
        self.tabs.setCurrentIndex(0)
    
    def delete_selected_preset(self):
        """Delete the selected preset"""
        selected_items = self.presets_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a preset")
            return
        
        preset_name = selected_items[0].text()
        
        # Confirm deletion
        reply = QtWidgets.QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete '{preset_name}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            del self.presets[preset_name]
            self.save_presets_to_file()
            self.refresh_presets_list()
            QtWidgets.QMessageBox.information(self, "Success", f"Preset '{preset_name}' deleted!")
    
    def start_autoclicker(self):
        key = self.key_display.text()
        if not key:
            QtWidgets.QMessageBox.warning(self, "Error", "Please set a key/button")
            return
        
        times = self.reps_spinbox.value()
        hold_duration = self.hold_spinbox.value()
        delay_between = self.delay_spinbox.value()
        endless_mode = self.endless_mode_checkbox.isChecked()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.listen_button.setEnabled(False)
        self.reps_spinbox.setEnabled(False)
        self.hold_spinbox.setEnabled(False)
        self.delay_spinbox.setEnabled(False)
        self.randomness_spinbox.setEnabled(False)
        self.endless_mode_checkbox.setEnabled(False)
        
        if endless_mode:
            self.status_text.setText(f"Running (Endless Mode)...\nKey: {key}\nPress {self.abort_key} to stop")
        else:
            self.status_text.setText(f"Running...\nKey: {key}\nRepetitions: {times}")
        
        self.clicker_thread = AutoClickerThread(
            key, times, hold_duration, delay_between,
            self.abort_key, 
            self.initial_delay_spinbox.value(),
            self.countdown_duration_spinbox.value(),
            self.show_countdown,
            self.randomness_spinbox.value(),
            endless_mode
        )
        self.clicker_thread.time_remaining.connect(self.update_time_remaining)
        self.clicker_thread.countdown.connect(self.update_countdown)
        self.clicker_thread.finished.connect(self.on_finished)
        self.clicker_thread.start()
    
    def stop_autoclicker(self):
        global stop_flag
        stop_flag = True
        if self.clicker_thread:
            self.clicker_thread.should_stop = True
    
    def update_time_remaining(self, remaining):
        self.time_remaining_label.setText(f"{remaining} repetitions left")
    
    def update_countdown(self, seconds):
        if seconds > 0:
            self.countdown_label.setText(f"{seconds} seconds")
        else:
            self.countdown_label.setText("")
    
    def on_finished(self):
        self.status_text.setText("Finished!")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.listen_button.setEnabled(True)
        self.reps_spinbox.setEnabled(not self.endless_mode_checkbox.isChecked())
        self.randomness_spinbox.setEnabled(True)
        self.endless_mode_checkbox.setEnabled(True)
        # Restore hold/delay UI according to quick-hold
        self.apply_hold_preset_ui(self.hold_preset_checkbox.isChecked())
        self.time_remaining_label.setText("0 repetitions left")
        self.save_settings()
        QtWidgets.QMessageBox.information(self, "Done", "Kold's Tools finished!")


# On Windows, set AppUserModelID so Windows can associate the running process with a pinned shortcut/icon
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.koldstools.KoldsTools")
    except Exception:
        pass

# Initialize Qt Application
app = QtWidgets.QApplication(sys.argv)
window = AutoPresserApp()
window.show()
sys.exit(app.exec())