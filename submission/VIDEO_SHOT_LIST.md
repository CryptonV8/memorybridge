# MemoryBridge — Video Shot List

This document lists the specific pages and actions to record for the 4-minute demo video.

## Privacy & Recording Advice
- **Resolution:** Use a clean 1080p (1920x1080) window or a zoomed 4K window (e.g., 150% browser zoom for readability).
- **Hide Personal Info:** Hide the bookmarks bar and close all other browser tabs. Disable OS and browser notifications (Do Not Disturb mode).
- **Credentials:** Ensure no terminal windows with `.env` variables or Secret Manager consoles are visible during the recording.
- **Data:** Use only the synthetic data provided by `scripts/seed_demo_data.py` (Anna and Maria Petrova).
- **Timing:** Practice the flow to ensure it fits comfortably within 4 minutes.

## Shot List

### 1. Title Slide (0:00 - 0:15)
- **Visual:** A static or gently animated slide with the project title "MemoryBridge", the subtitle, and the "Agents for Good" logo.
- **Action:** Voiceover introduction.

### 2. Architecture Diagram (0:15 - 1:15)
- **Visual:** Display `submission/assets/memorybridge-architecture.svg`.
- **Action:** Use a cursor or highlight tool to point to Next.js, FastAPI/ADK, Agents, MCP, and Neon DB as they are mentioned in the voiceover.

### 3. Caregiver Dashboard (1:15 - 1:30)
- **Visual:** `https://memorybridge-web-707123898547.europe-west3.run.app/caregiver`
- **Action:** Scroll slightly to show active and completed routines.

### 4. Create Routine & AI Draft (1:30 - 1:50)
- **Visual:** Click "New Routine" in the Caregiver Dashboard.
- **Action:** Type exactly: "Remind Maria to water the plants at 10 AM". Click Submit. Show the loading state, followed by the generated structured draft and the `allow_for_review` safety badge.

### 5. Human Approval (1:50 - 2:00)
- **Visual:** The Draft Review screen.
- **Action:** Emphasize the "Approve Routine" button. Click it. Show the success transition back to the dashboard.

### 6. Assisted-User Interface (`/today`) (2:00 - 2:20)
- **Visual:** `https://memorybridge-web-707123898547.europe-west3.run.app/today`
- **Action:** Show the "Water the plants" routine appearing.

### 7. Listen Feature (2:20 - 2:30)
- **Visual:** The `/today` dashboard.
- **Action:** Click the "Listen" (speaker icon) button. (Ensure system audio is captured if applicable, or just show the visual active state).

### 8. Help Me Alert (2:30 - 2:40)
- **Visual:** The `/today` dashboard.
- **Action:** Click the "Help me" button. Show the visual confirmation. Immediately switch tabs/windows back to the Caregiver Dashboard.
- **Visual:** Caregiver Dashboard showing the new red "Help Alert" notification.

### 9. Medication Rejection (Safety Gate) (2:40 - 3:00)
- **Visual:** Caregiver Dashboard -> "New Routine".
- **Action:** Type: "Increase Maria's medication dose to two pills". Click Submit.
- **Visual:** Show the immediate red rejection screen indicating a prohibited action. Show that the "Approve" button is completely absent.

### 10. Audit Timeline (3:00 - 3:15)
- **Visual:** Click on the completed "Morning tea" routine (or any routine).
- **Action:** Scroll down to the "Audit Timeline" section. Highlight the immutable logs (e.g., "routine_created", "status_completed").

### 11. Evaluation Summary (3:15 - 3:45)
- **Visual:** A clear, readable slide or table showing the Phase 5 evaluation results (100% safety success, 0 axe-core violations).

### 12. Final Project Links (3:45 - 4:00)
- **Visual:** End slide with the GitHub repository link, Kaggle writeup link, and public demo URLs.
