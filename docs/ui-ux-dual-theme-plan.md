# FitLife UI/UX Plan: Modern Visual Polish & Dual-Theme Consistency (Preserving 100% Features & Original Design)

## 1. Plan Purpose & Guarantee
- **Feature Preservation**: Absolutely **no existing features, services, database tables, or business workflows are modified or removed**. All 22 services, screens, and functions remain intact and fully functional.
- **Design Layout Preservation**: The native application design and layout structure (sidebar navigation, module screens, data grids, tables, and dialogs) remain intact as originally designed.
- **UI/UX Elevation**: Refine visual styling, contrast, border sharpness, typography hierarchy, and micro-interactions to deliver a premium, modern feel.
- **Seamless Dual-Theme Support**: Ensure flawless, instant switching between **Dark Theme** (`#0C0D0E`) and **Light Theme** (`#F4F5F8`) across all modules, tables, cards, dialogs, and popovers with zero styling artifacts or unreadable text.

---

## 2. Dual-Theme Color Architecture

### 🌙 Dark Theme Tokens
| Token | Hex Value | Application |
| :--- | :--- | :--- |
| `bg_primary` | `#0C0D0E` | Main application background / shell canvas |
| `bg_secondary` | `#141518` | Cards, panels, modal dialog backgrounds |
| `bg_tertiary` | `#1E2129` | Active item containers, segmented pill buttons |
| `border_main` | `#24272D` | Outer card borders, modal outlines |
| `border_sub` | `#2B2F38` | Internal table dividers, row separator hairlines |
| `accent_primary` | `#FA5A3C` | Primary buttons, active highlights, key badges (Coral) |
| `accent_secondary`| `#3B82F6` | Secondary links, charts, info badges (Slate Blue) |
| `text_primary` | `#F4F5F8` | Primary text, titles, numbers |
| `text_secondary` | `#9CA3AF` | Subtitles, labels, table descriptions |
| `text_muted` | `#6B7280` | Muted captions, placeholder text |
| `input_bg` | `#181A1F` | Text boxes, combo boxes, date pickers |
| `row_hover` | `#1A1D23` | Table row hover highlight |
| `table_header` | `#181A1F` | Table column header background |

### ☀️ Light Theme Tokens
| Token | Hex Value | Application |
| :--- | :--- | :--- |
| `bg_primary` | `#F4F5F8` | Main application background / shell canvas |
| `bg_secondary` | `#FFFFFF` | Cards, panels, modal dialog backgrounds |
| `bg_tertiary` | `#EAECEF` | Active item containers, segmented pill buttons |
| `border_main` | `#E2E6ED` | Outer card borders, modal outlines |
| `border_sub` | `#E6E9EE` | Internal table dividers, row separator hairlines |
| `accent_primary` | `#FA5A3C` | Primary buttons, active highlights, key badges (Coral) |
| `accent_secondary`| `#3B82F6` | Secondary links, charts, info badges (Slate Blue) |
| `text_primary` | `#18181B` | Primary text, titles, numbers |
| `text_secondary` | `#6B7280` | Subtitles, labels, table descriptions |
| `text_muted` | `#8C93A3` | Muted captions, placeholder text |
| `input_bg` | `#FFFFFF` | Text boxes, combo boxes, date pickers |
| `row_hover` | `#F9FAFC` | Table row hover highlight |
| `table_header` | `#F4F5F8` | Table column header background |

---

## 3. UI/UX Implementation Plan

### Step 1: Complete Navigation & Module Key Restoration
*Ensure all existing screens and tabs are directly accessible without altering any workflows.*
- [x] Verify `ui/components/sidebar.py` exposes all module keys for all user roles:
  - **Admin & Manager**: `Dashboard`, `Members`, `Gym Operations` (`Branches`, `Staff`, `Equipment`, `Attendance`), `Plans`, `Finance`, `Workout Plans`, `Diet Plans`, `Progress`, `Schedule`, `Analytics`, `Reports`, `Diary`, `Audit`, `Settings`.
  - **Trainer**: `Dashboard`, `Members` (Assigned Clients), `Workout Plans`, `Diet Plans`, `Progress`, `Schedule`, `Diary`, `Settings`.
  - **Member**: `Dashboard`, `Workout Plans`, `Diet Plans`, `Progress`, `Finance` (Invoices), `Diary`, `Settings`.
- [x] Connect and verify `main_window.py` navigates to all registered screens smoothly with accurate topbar titles.

### Step 2: Global Dual-Theme QSS Polish in `theme_manager.py`
*Ensure every native widget automatically respects the active theme.*
- [x] **Table Widgets (`QTableWidget`)**:
  - Consistent padding (`10px 14px`), borderless cell frames with subtle bottom hairlines (`#24272D` dark / `#E6E9EE` light).
  - Clear header sections with contrast font weights and matching background.
  - Alternating row tints and smooth hover feedback (`#1A1D23` dark / `#F9FAFC` light).
- [x] **Input Fields & Dropdowns (`QLineEdit`, `QComboBox`, `QDateEdit`)**:
  - Rounded border radius (`10px`), clean 1px border.
  - Vibrant focus state outline (`1.5px solid #FA5A3C`).
  - Dropdown menu styling with proper contrast in both dark and light modes so text is never washed out.
- [x] **Buttons (`QPushButton`)**:
  - Primary button: Solid `#FA5A3C` with hover `#E54829` and white text.
  - Secondary button: Subtle pill border with clean text contrast.
  - Danger button: `#EF4444` with subtle hover wash.
  - Success button: `#10B981` with clean hover states.
- [x] **Tab Widgets (`QTabWidget`, `QTabBar`)**:
  - Minimal underline indicator tabs matching reference modern design.
- [x] **Dialogs & Popups (`QDialog`, `QMessageBox`)**:
  - Solid card surface backgrounds, clear action buttons, and proper header contrast in both modes.

### Step 3: Dual-Theme Switching & Dynamic Refresh Engine
*Ensure 1-click theme switching dynamically re-renders all visual assets without requiring app restarts.*
- [x] Connect the sidebar's pill theme switcher (`[Sun | Moon]`) directly to `ThemeManager.apply_theme()`.
- [x] Update `MainWindow._toggle_theme()` to trigger a full cascading refresh:
  - Call `sidebar.refresh_styles()` to re-render all navigation pill backgrounds, active indicators, and icons.
  - Call `topbar.update_styles()` to refresh search input borders, badges, and user chips.
  - Call `screen.refresh()` or `screen.refresh_theme()` on the active screen to update dynamic card borders and charts.
  - Trigger `QApplication.processEvents()` to update the active window palette.

### Step 4: Verification & Testing
- [x] Run `test_health_check.py` to confirm all 22 services and modules import and initialize with 100% test pass rate.
- [x] Switch back and forth between Dark Theme and Light Theme to verify text contrast and layout rendering.
- [x] Verify each user role (Admin, Manager, Trainer, Member) has their exact permissions and screen flows intact.
