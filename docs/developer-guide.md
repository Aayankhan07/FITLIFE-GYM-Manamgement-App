# FitLife Developer Guide & Guidelines

This guide details development practices, UI component creation, threading guidelines, and procedures for extending the **FitLife Gym Management System**.

---

## 1. Development Principles & Code Standards

- **Python Specification**: Python 3.10+ strict typing annotations where applicable.
- **UI Framework**: PyQt6 with QSS styling managed via `ThemeManager`.
- **Zero Thread-Blocking**: Never execute heavy DB queries, disk I/O, or network requests on the main GUI loop. Use `QThreadWorker`.
- **SQL Injection Prevention**: Never concatenate raw strings into SQL statements. Always use parameter binding (`?` or `%s`).

---

## 2. UI Development & Component System

### 2.1 ThemeManager & Styling (`ui/theme/theme_manager.py`)
Theme styles are centralized in `ThemeManager`. Apply glassmorphic QSS styling using the global theme helper:

```python
from ui.theme.theme_manager import ThemeManager

# Retrieve current QSS style for a component
button_style = ThemeManager.get_button_style()
card_style = ThemeManager.get_glass_card_style()
```

### 2.2 Reusable UI Components
- **`GlassCard` (`ui/components/glass_card.py`)**: Glassmorphic container with translucent background, rounded corners, subtle border gradient, and shadow.
- **`DataTable` (`ui/components/data_table.py`)**: Customized `QTableWidget` featuring sortable columns, dark header styling, hover highlighting, and pagination controls.
- **`IconEngine` (`ui/components/icons.py`)**: Renders high-resolution vector SVG icons dynamically colored according to the current theme palette.

---

## 3. Asynchronous Worker Pattern (`utils/thread_worker.py`)

When calling services from a PyQt6 screen, wrap the execution inside `QThreadWorker`:

```python
from PyQt6.QtWidgets import QWidget
from utils.thread_worker import QThreadWorker
from services.member_service import MemberService

class MembersScreen(QWidget):
    def load_member_data(self):
        # 1. Instantiate worker with service target function and arguments
        self.worker = QThreadWorker(MemberService.get_all_members, branch_id=self.current_branch_id)
        
        # 2. Connect signals
        self.worker.finished.connect(self._on_data_loaded)
        self.worker.error.connect(self._on_data_error)
        
        # 3. Start thread
        self.worker.start()

    def _on_data_loaded(self, members):
        # Update UI table on main thread
        self.table.populate(members)

    def _on_data_error(self, error_msg):
        # Handle error safely
        self.show_error_dialog(error_msg)
```

---

## 4. How to Add a New Feature Module / Screen

Follow this step-by-step procedure to add a new screen module (e.g. `Equipment Maintenance`):

### Step 1: Create Business Service Method
Add required service methods to `services/` (e.g. `services/equipment_service.py`):
```python
def schedule_maintenance(equipment_id: int, date: str, note: str) -> tuple[bool, str]:
    # Execute parameterized UPDATE query
    ...
```

### Step 2: Create UI Screen Widget
Create a new package under `ui/screens/` (e.g. `ui/screens/equipment/equipment_screen.py`):
```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class EquipmentScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Equipment Maintenance Module"))
```

### Step 3: Register Screen in `MainWindow`
Open `ui/windows/main_window.py`:
1. Import `EquipmentScreen`.
2. Instantiate screen and append to `QStackedWidget` navigation container:
   ```python
   self.equipment_screen = EquipmentScreen()
   self.stacked_widget.addWidget(self.equipment_screen)
   ```

### Step 4: Register Sidebar Item & Permission Gate
In `ui/components/sidebar.py`, register the sidebar item with required module permission key (`Equipment`):
```python
self.add_nav_item("Equipment", icon_name="wrench", screen_index=ENUM_EQUIPMENT_INDEX)
```

---

## 5. Health Checks & Debugging

### Running Diagnostic Health Check
Execute the health check utility directly from command line to test environment integrity:
```bash
python -m utils.health_check
```
*Validates Python package dependencies, MS SQL Server / SQLite database connectivity, log directory permissions, and configuration file validity.*

### Inspecting System Logs
Application logs are written to rotating log files in `logs/fitlife.log`. Use tail or PowerShell to monitor log output:
```powershell
Get-Content logs/fitlife.log -Wait -Tail 30
```
