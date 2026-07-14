# Kold's Tools - Developer Documentation

A feature-rich autoclicker/key presser tool built with PySide6 and pynput. This documentation is for developers looking to understand, modify, or extend the codebase.

Notable changes:
- Added **Quick Hold** preset: quick 1s hold / 0.5s delay and UI grays relevant fields when active.
- Added **Remember settings between sessions** option in Settings to persist or ignore the last session.
- Improved listening behavior: listening no longer shifts focus to input widgets (number keys are captured safely).
- About page and README updated to reflect these changes; a visible copyright/disclaimer has been added.



## Packaging as an EXE

Recommended approach (Windows): use **PyInstaller** to bundle the app into a single executable with an embedded icon. This ensures the taskbar and title bar will show your custom icon and the app can be distributed without requiring a local Python install.

Quick steps:
1. Install PyInstaller: `pip install pyinstaller`
2. Place a multi-size `.ico` file next to `main.py` named `logotipasKoldTools.ico` (recommended) or point to another icon file.
3. Run the included build script on Windows: `build_exe.bat`. It executes:
   `pyinstaller --noconsole --onefile --icon=logotipasKoldTools.ico main.py`

Notes:
- If you need debugging output while packaging, remove `--noconsole` to keep a console.
- For crisp taskbar/title appearance, use a multi-resolution `.ico` (16,32,48,256 px) or a high-resolution PNG converted to `.ico`.
- The app already sets a Windows AppUserModelID at startup which helps Windows associate the running process with a pinned shortcut that has the same ID.

## Architecture Overview

The application follows a three-layer architecture:

1. **UI Layer (PySide6)**: Qt-based GUI with multiple tabs for different functionalities
2. **Threading Layer (QThread)**: Background threads for non-blocking operations
3. **Input Layer (pynput)**: Cross-platform keyboard and mouse input handling

## Core Components

### 1. KeyListenerThread (QThread)

Handles capturing keyboard and mouse input in a non-blocking way.

**Signals:**
- `key_captured`: Emitted when a key/button is captured with the key name as a string
- `finished`: Emitted when listening completes

**Key Detection Logic:**
```python
# Keyboard keys use 'char' (single char) or 'name' (special keys like 'enter')
# Mouse buttons use button.name attribute (automatically handles all button types)
```

**Timeout:** 10 seconds (100 iterations × 0.1s sleep)

### 2. AutoClickerThread (QThread)

The main execution thread that performs the clicking/pressing actions.

**Constructor Parameters:**
- `key`: The key/button to press
- `times`: Number of repetitions
- `hold_duration`: How long to hold the key (in seconds)
- `delay_between`: Delay after each press release (in seconds)
- `abort_key`: Key that stops execution
- `initial_delay`: Delay before countdown starts (in seconds)
- `countdown_duration`: Length of startup countdown (in seconds)
- `show_countdown`: Whether to display countdown
- `randomness_range`: Random delay variance (in seconds)

**Signals:**
- `time_remaining`: Emits remaining repetition count
- `countdown`: Emits countdown seconds (0 = cleared)
- `finished`: Emitted when complete or aborted

**Key Execution Flow:**

1. Start abort key listener
2. Apply initial delay
3. Apply countdown (if enabled)
4. For each repetition:
   - Hold key for `hold_duration` by pressing repeatedly every 0.1s
   - Release key
   - Apply delay: `delay_between + random(0, randomness_range)`
5. Stop listener and emit finished signal

**Abort Key Detection:**
```python
# Converts captured key to string format and compares with self.abort_key
# Supports both keyboard keys ('enter', 'a', etc.) and mouse buttons ('left_click', etc.)
```

### 3. AutoPresserApp (QMainWindow)

Main application window with PySide6 UI.

**Tabs:**
- **Tab 1 - Main**: Key selection, repetitions, hold duration, delay, and status display
- **Tab 2 - Presets**: Save/load/delete preset configurations
- **Tab 3 - Settings**: Advanced settings (abort key, auto-start, countdown options)
- **Tab 4 - About**: Application information

**Key Methods:**

#### Input Listening
- `start_listening_for_key()`: Initiates KeyListenerThread for main action key
- `start_listening_for_abort_key()`: Initiates KeyListenerThread for abort key
- `on_key_captured()`: Callback when main key captured
- `on_abort_key_captured()`: Callback when abort key captured

#### Autoclicker Control
- `start_autoclicker()`: Creates and starts AutoClickerThread with current settings
- `stop_autoclicker()`: Sets global `stop_flag` and thread's `should_stop`
- `on_finished()`: Re-enables UI elements after execution

#### Settings Management
- `on_auto_start_changed()`: Handles auto-start checkbox
- `on_show_countdown_changed()`: Handles countdown visibility checkbox

#### Preset Management
- `save_preset()`: Saves current settings to `autoclicker_presets.json`
- `load_selected_preset()`: Loads preset and switches to Main tab
- `delete_selected_preset()`: Removes preset with confirmation
- `load_presets()`: Reads from JSON file
- `save_presets_to_file()`: Writes presets to JSON file
- `refresh_presets_list()`: Updates UI list widget

#### Status Display
- `update_time_remaining()`: Updates repetitions left label
- `update_countdown()`: Updates countdown display label

## Data Flow

### Starting Execution
```
[Start Button Click]
    ↓
[validate key → create AutoClickerThread]
    ↓
[disable UI controls]
    ↓
[emit countdown signal every 1s]
    ↓
[emit time_remaining after each press]
    ↓
[on finished signal → re-enable UI]
```

### Key Capture
```
[Listen Button Click]
    ↓
[create KeyListenerThread]
    ↓
[wait for key/mouse input (10s timeout)]
    ↓
[emit key_captured signal]
    ↓
[update UI field]
```

## Global Variables

- `keyboard`: pynput.keyboard.Controller instance (global singleton)
- `stop_flag`: Boolean flag for graceful shutdown across threads
- `listener`: Current Listener instance (can be None)
- `PRESETS_FILE`: Path to "autoclicker_presets.json"

## Configuration Files

### autoclicker_presets.json
JSON file storing user presets. Structure:
```json
{
  "preset_name": {
    "key": "e",
    "repetitions": 10,
    "hold_duration": 1.0,
    "delay_between": 0.5
  }
}
```

## Key Implementation Details

### Hold Duration Implementation
```python
press_count = int(self.hold_duration / 0.1)  # 0.1s steps
for _ in range(press_count):
    keyboard.press(self.key)
    time.sleep(0.1)
keyboard.release(self.key)
```

### Randomness
```python
delay = self.delay_between
if self.randomness_range > 0:
    delay += random.uniform(0, self.randomness_range)
time.sleep(delay)
```

### Abort Key Matching
The abort key is stored as a string and compared directly against captured key strings:
- Single chars: 'a', 'e', '1'
- Special keys: 'enter', 'space', 'tab'
- Mouse buttons: 'left_click', 'right_click', 'x1_click'

## Threading Considerations

### Thread Safety
- UI updates only happen via signals connected to main thread slots
- Global `stop_flag` is checked in loops, not protected by locks (acceptable for boolean)
- Each thread has its own listener instances

### Signal-Slot Pattern
All thread-to-UI communication uses Qt signals to ensure thread safety:
```python
self.clicker_thread.time_remaining.connect(self.update_time_remaining)
```

## Extension Points

### Adding New Settings
1. Add UI control in `setup_tab1()` or `setup_tab3()`
2. Add class variable in `__init__()`
3. Pass to `AutoClickerThread.__init__()`
4. Use in `AutoClickerThread.run()`
5. Add to preset saving/loading if applicable

### Adding New Input Types
1. Create new listener type (e.g., scroll listener)
2. Add to `KeyListenerThread._listen_for_input()`
3. Format key name consistently with existing types
4. Update `AutoClickerThread.on_press()` to handle new type

### Adding New Tabs
1. Create `self.tabX` in `__init__()`
2. Create `setup_tabX()` method
3. Add to `self.tabs.addTab()`
4. Add signal/slot connections as needed

## Dependencies

- **pynput**: Cross-platform keyboard/mouse input
- **PySide6**: Qt bindings for UI
- **random**: Randomness for delay variance
- **json**: Preset serialization
- **threading**: Background thread management
- **time**: Sleep operations
- **sys**: Application exit
- **os**: File existence checking

## Common Modifications

### Change Default Abort Key
```python
# In __init__
self.abort_key = "escape"  # Instead of "num_lock"
```

### Change Countdown Duration
```python
# In setup_tab3
self.countdown_duration_spinbox.setValue(10)  # Default 10 seconds
```

### Add Minimum Hold Duration
```python
# In AutoClickerThread.run()
actual_hold = max(self.hold_duration, MINIMUM_HOLD)
```

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Starting autoclicker with {self.times} repetitions")
```

## Testing Recommendations

1. **Unit Tests**: Test KeyListenerThread key detection
2. **Integration Tests**: Test AutoClickerThread with different parameters
3. **UI Tests**: Test preset loading/saving
4. **Cross-platform Tests**: Verify pynput works on target OS
5. **Edge Cases**:
   - Hold duration = 0
   - Randomness > delay_between
   - Very high repetition counts
   - Rapid button clicks

## Known Limitations

1. **Key Capture**: Some system-reserved keys may not be capturable
2. **Windows Only**: While pynput is cross-platform, VK code checking is Windows-specific (currently removed)
3. **Performance**: Very short delays (<0.1s) may not be reliable
4. **Mouse Clicks**: Only detects clicks, not movement or scroll