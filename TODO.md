# TODO: feat/notify Branch Improvements

This document tracks improvements needed for the notification feature before merging to main.

---

## 🔴 Critical (Block Merge)

### [x] Fix session management in scheduler
**Priority:** Critical  
**Effort:** 15 minutes  
**Files:** `backend/app/domains/notifications/service/notification_scheduler.py`

**Task:**
Replace manual session creation/cleanup with context manager pattern in the `_execute()` method.

**Current Code:**
```python
async def _execute(self) -> None:
    session = self.session_factory()
    try:
        # ... code ...
    finally:
        session.close()
```

**Should Become:**
```python
async def _execute(self) -> None:
    with self.session_factory() as session:
        try:
            # ... code ...
        except Exception:
            logger.exception("Scheduled notification check failed")
```

**Note:** May need to update `get_db_session()` in `app.pkgs.database` to support context manager if it doesn't already.

**Acceptance Criteria:**
- [x] Session is managed via `with` statement
- [x] No manual `session.close()` calls
- [x] All tests still pass
- [x] No resource leaks in exception paths

---

### [x] Add environment variable validation
**Priority:** Critical
**Effort:** 10 minutes
**Files:** `backend/app/core/config.py`

**Task:**
Add Pydantic field validators for `NOTIFICATION_HOUR` and `NOTIFICATION_MINUTE` to ensure they're within valid ranges.

**Code to Add:**
```python
from pydantic import field_validator

class Settings(BaseSettings):
    # ... existing code ...

    NTFY_INTERNAL_URL: str = "http://ntfy:80"
    NTFY_PUBLIC_URL: str = "https://ntfy.localhost"
    NOTIFICATION_HOUR: int = 22
    NOTIFICATION_MINUTE: int = 0

    @field_validator('NOTIFICATION_HOUR')
    @classmethod
    def validate_hour(cls, v: int) -> int:
        if not 0 <= v <= 23:
            raise ValueError('NOTIFICATION_HOUR must be between 0 and 23')
        return v

    @field_validator('NOTIFICATION_MINUTE')
    @classmethod
    def validate_minute(cls, v: int) -> int:
        if not 0 <= v <= 59:
            raise ValueError('NOTIFICATION_MINUTE must be between 0 and 59')
        return v
```

**Acceptance Criteria:**
- [x] Hour validation rejects values < 0 or > 23
- [x] Minute validation rejects values < 0 or > 59
- [x] Test cases added for validation
- [x] Invalid env values cause clear error on startup

---

## 🟡 High Priority (Fix Soon After Merge)

### [x] Add integration tests for notification flow
**Priority:** High
**Effort:** 2-3 hours
**Files:** `backend/tests/api/routes/notifications/test_trigger.py`, `backend/tests/domains/notifications/test_notification_flow_integration.py`

**Task:**
Create integration tests that verify the complete notification flow works end-to-end.

**Test File Structure:**
```
backend/tests/integrations/
└── test_notification_flow.py
```

**Required Tests:**

1. **Full Notification Flow**
   - Create user with enabled notifications
   - Create card with statement due tomorrow
   - Trigger notification
   - Verify ntfy client receives correct data
   - Verify SendResult is correct

2. **Scheduler Lifecycle**
   - Create scheduler
   - Start it
   - Verify it's running
   - Stop it
   - Verify it stopped cleanly
   - Verify task is cancelled

3. **Migration Test**
   - Run migration upgrade
   - Verify new columns exist
   - Verify default values
   - Run migration downgrade
   - Verify columns are removed

**Example Test:**
```python
# tests/integrations/test_notification_flow.py
import pytest
from decimal import Decimal
from datetime import date, timedelta

from app.domains.notifications.usecases.send_due_notifications.usecase import SendDueNotificationsUseCase
from app.domains.notifications.service.ntfy_client import NtfyClient

@pytest.mark.asyncio
async def test_full_notification_flow(db: Session):
    # Setup
    user = create_test_user(db, notifications_enabled=True, ntfy_topic="test-topic")
    card = create_test_card(db, user)
    stmt = create_test_statement(
        db,
        card,
        due_date=date.today() + timedelta(days=1),
        current_balance=Decimal("100.00")
    )
    
    # Mock ntfy client to capture calls
    class MockNtfyClient:
        def __init__(self, url):
            self.calls = []
        async def send(self, topic, title, message, priority=4, tags=None):
            self.calls.append({
                'topic': topic,
                'title': title,
                'message': message,
                'priority': priority,
                'tags': tags
            })
            return True
    
    # Execute
    mock_client = MockNtfyClient("http://test")
    usecase = SendDueNotificationsUseCase(
        session=db,
        ntfy_client=mock_client,
        ntfy_public_url="https://ntfy.example.com"
    )
    result = await usecase.execute_for_user(user.id)
    
    # Verify
    assert result.notification_sent is True
    assert len(mock_client.calls) == 1
    assert mock_client.calls[0]['topic'] == 'test-topic'
    assert "100.00" in mock_client.calls[0]['message']
```

**Acceptance Criteria:**
- [x] Full flow test passes with real database
- [x] Scheduler lifecycle tests pass
- [ ] Migration test passes
- [x] All integration tests run in CI/CD (covered by existing `backend-tests.yml` workflow)

---

### [x] Create documentation for ntfy setup
**Priority:** High  
**Effort:** 1 hour  
**Files:** `docs/notifications.md` (new file)

**Task:**
Write comprehensive user-facing documentation for setting up ntfy notifications.

**Required Sections:**

1. **Introduction**
   - What is ntfy?
   - Why we use it (privacy, reliability)
   - How notifications work

2. **Installation Instructions**
   - iOS app store link
   - Google Play store link
   - Step-by-step screenshots

3. **Setup Guide**
   - Adding server URL
   - Subscribing to topic
   - Finding your topic URL in the app

4. **Testing**
   - How to use "Test Notification" button
   - What to expect

5. **Troubleshooting**
   - Not receiving notifications
   - Topic URL changed
   - App permissions

6. **Privacy Note**
   - Topic names are unique per user
   - Keep your topic URL private
   - Security considerations

**Template:**
```markdown
# Setting Up Push Notifications

## What is Ntfy?

Ntfy is a free, open-source push notification service. We host our own instance at `https://ntfy.yourdomain.com` to ensure your data stays private and notifications are reliable.

## Installation

### iOS
1. Download Ntfy from the [App Store](https://apps.apple.com/app/ntfy/id1625395874)
2. Open the app
3. Tap the "+" button to add a server
4. Enter: `https://ntfy.yourdomain.com`
5. Tap "Connect"

### Android
1. Download Ntfy from [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
2. Open the app
3. Tap the "+" button
4. Enter: `https://ntfy.yourdomain.com`
5. Tap "Connect"

## Subscribing to Notifications

1. Go to **Settings** → **Notifications** in the web app
2. Toggle **Enable notifications** on
3. Copy your unique topic URL shown below the toggle
4. In the Ntfy app, tap "Subscribe to topic"
5. Paste the full URL (e.g., `https://ntfy.yourdomain.com/pf-app-abc123`)
6. Tap "Subscribe"

## Testing Your Setup

After subscribing, click the **Test Notification** button in Settings. You should receive a test message on your phone within a few seconds.

## Troubleshooting

### Not receiving notifications?
- Make sure you're subscribed to the correct topic URL
- Check that your phone allows notifications for the Ntfy app
- Try sending another test notification

### Topic URL changed?
Your unique topic is generated when you enable notifications. If you need a new topic:
1. Toggle notifications off
2. Toggle notifications back on
3. A new topic will be generated
4. Update your subscription in the Ntfy app

## Privacy & Security

- Your topic URL is unique to your account
- Anyone who knows your topic URL could subscribe to your notifications
- Keep your topic URL private, like a password
- You can generate a new topic at any time by re-enabling notifications
```

**Acceptance Criteria:**
- [x] Documentation is clear and beginner-friendly
- [x] Includes platform-specific instructions (iOS, Android)
- [x] Has troubleshooting section
- [ ] Link is added to the Settings UI
- [ ] Screenshots or diagrams included (optional but recommended)

---

### [x] Add ntfy topic validation
**Priority:** High  
**Effort:** 20 minutes  
**Files:** `backend/app/domains/users/domain/models.py`

**Task:**
Add Pydantic validator to ensure `ntfy_topic` only contains valid characters (alphanumeric, dash, underscore).

**Code to Add:**
```python
import re
from pydantic import field_validator

class UserBase(SQLModel):
    # ... existing fields ...
    
    notifications_enabled: bool = Field(default=False)
    ntfy_topic: str | None = Field(
        default=None, 
        max_length=100,
        description="Ntfy topic name (alphanumeric, dash, underscore only)"
    )

    @field_validator('ntfy_topic')
    @classmethod
    def validate_ntfy_topic(cls, v: str | None) -> str | None:
        if v and not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError(
                'ntfy_topic must contain only letters, numbers, dashes, and underscores'
            )
        return v
```

**Tests to Add:**
```python
# tests/domains/users/test_user_validation.py

import pytest
from pydantic import ValidationError

def test_ntfy_topic_valid():
    user_data = {
        'email': 'test@example.com',
        'password': 'test123',
        'ntfy_topic': 'my-topic-123'
    }
    user = UserCreate(**user_data)
    assert user.ntfy_topic == 'my-topic-123'

def test_ntfy_topic_invalid_spaces():
    with pytest.raises(ValidationError) as exc:
        UserCreate(
            email='test@example.com',
            password='test123',
            ntfy_topic='my topic'
        )
    assert 'ntfy_topic' in str(exc.value)

def test_ntfy_topic_invalid_special_chars():
    with pytest.raises(ValidationError) as exc:
        UserCreate(
            email='test@example.com',
            password='test123',
            ntfy_topic='my@topic#123'
        )
    assert 'ntfy_topic' in str(exc.value)
```

**Acceptance Criteria:**
- [x] Validator rejects invalid topics (spaces, special chars)
- [x] Validator accepts valid topics
- [x] Error message is clear
- [x] Tests cover valid and invalid cases

---

### [x] Decide on `ntfy_public_url` parameter
**Priority:** High  
**Effort:** 15 minutes (decision) + 30 minutes (implementation if used)

**Task:**
Decide whether to use or remove the `ntfy_public_url` parameter.

**Options:**

**Option A - Remove it** (Recommended for now)
- Remove from usecase `__init__`
- Remove from `provide()` function
- Remove from all call sites
- Simplifies the code

**Option B - Use it for links**
- Add statement URLs to notification messages
- Allow users to tap notification to view statement
- Enhances UX but increases complexity

**Implementation (Option A - Remove):**

Files to update:
1. `backend/app/domains/notifications/usecases/send_due_notifications/usecase.py`
2. `backend/app/api/routes/notifications/trigger.py`
3. `backend/app/main.py`
4. `backend/app/domains/notifications/service/notification_scheduler.py`

**Acceptance Criteria:**
- [x] Decision documented in code or issue
- [x] Either parameter is used for links OR removed cleanly
- [x] All call sites updated
- [x] Tests pass

---

### [x] Fix hardcoded timezone in docker-compose
**Priority:** High  
**Effort:** 5 minutes  
**Files:** `docker-compose.yml`

**Task:**
Replace hardcoded `TZ=America/Argentina/Buenos_Aires` with UTC or make it configurable.

**Option A - Use UTC (Recommended):**
```yaml
services:
  ntfy:
    image: binwiederhier/ntfy
    environment:
      - TZ=UTC
```

**Option B - Make Configurable:**
```yaml
services:
  ntfy:
    image: binwiederhier/ntfy
    environment:
      - TZ=${NTFY_TIMEZONE:-UTC}
```

Add to `.env`:
```bash
# Ntfy timezone for display (notifications are scheduled in UTC)
NTFY_TIMEZONE=UTC
```

**Acceptance Criteria:**
- [x] Timezone is set to UTC or configurable
- [x] Documentation explains timezone behavior
- [x] Users understand notifications are scheduled in UTC

---

### [x] Add error display in frontend
**Priority:** High  
**Effort:** 30 minutes  
**Files:** `frontend/src/components/settings/NotificationsTab.vue`, `frontend/src/composables/useNotifications.ts`

**Task:**
The `useNotifications` composable sets error state but doesn't expose it. Add error display in the UI.

**Changes Needed:**

1. **Update composables to expose errors:**
```typescript
// frontend/src/composables/useNotifications.ts
export function useNotifications() {
  const error = ref<Error | null>(null)

  // ... existing code ...

  return {
    isEnabled,
    ntfyTopic,
    ntfyTopicUrl,
    isLoading,
    error,  // ✅ Already exposed
    fetchSettings,
    toggleNotifications,
    testNotification,
  }
}
```

2. **Add error display to component:**
```vue
<!-- frontend/src/components/settings/NotificationsTab.vue -->
<template>
  <div class="notifications-tab">
    <div class="notifications-card">
      <!-- Error display -->
      <Message
        v-if="error"
        severity="error"
        :closable="true"
        @close="error = null"
      >
        {{ error.message }}
      </Message>

      <h3 class="card-title">Push Notifications</h3>

      <!-- ... rest of template ... -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { useNotifications } from '@/composables/useNotifications'
// ... other imports ...
import Message from 'primevue/message'

const { isEnabled, ntfyTopicUrl, isLoading, error, fetchSettings, toggleNotifications, testNotification } =
  useNotifications()
// ... rest of code ...
</script>
```

**Acceptance Criteria:**
- [x] Errors from API calls are displayed to users
- [x] Error messages are dismissible
- [ ] No console errors on fetch/update/test failures

---

## 🟢 Medium Priority (Future Enhancements)

### [ ] Implement concurrent notification processing
**Priority:** Medium  
**Effort:** 1 hour  
**Files:** `backend/app/domains/notifications/usecases/send_due_notifications/usecase.py`

**Task:**
Replace sequential user processing in `execute_all()` with concurrent processing using `asyncio.gather()`.

**Current Code:**
```python
async def execute_all(self) -> list[SendResult]:
    users = self.session.exec(
        select(User).where(User.notifications_enabled == True)
    ).all()

    results = []
    for user in users:  # ❌ Sequential processing
        result = await self.execute_for_user(user.id)
        results.append(result)
        logger.info(...)
    return results
```

**Should Become:**
```python
import asyncio

async def execute_all(self) -> list[SendResult]:
    users = self.session.exec(
        select(User).where(User.notifications_enabled.is_(True))
    ).all()

    # ✅ Concurrent processing
    tasks = [self.execute_for_user(user.id) for user in users]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and log them
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(
                "Notification failed for user %s: %s",
                users[i].id,
                str(result)
            )
        else:
            final_results.append(result)

    return final_results
```

**Tests to Update:**
- Mock `execute_for_user` to verify it's called concurrently
- Test exception handling in `execute_all`

**Acceptance Criteria:**
- [ ] Notifications are sent concurrently
- [ ] Individual user failures don't stop processing
- [ ] Tests verify concurrent behavior
- [ ] Performance improvement measurable (if possible)

---

### [ ] Add notification history/log
**Priority:** Medium  
**Effort:** 3-4 hours  
**Files:** New model, migration, API, frontend

**Task:**
Create a notification log model to track all sent notifications and their status.

**Implementation Steps:**

1. **Create model:**
```python
# backend/app/domains/notifications/domain/models.py
from datetime import datetime
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4

class NotificationLogBase(SQLModel):
    user_id: UUID = Field(foreign_key="user.id")
    ntfy_topic: str
    notification_type: str = Field(default="due_date")  # due_date, test, etc.
    statements_found: int
    notification_sent: bool
    error_message: str | None = None
    sent_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationLog(NotificationLogBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
```

2. **Create migration:** Add `NotificationLog` table

3. **Update usecase to log:**
```python
async def execute_for_user(self, user_id: uuid.UUID) -> SendResult:
    # ... existing code ...
    
    result = SendResult(
        user_id=user_id,
        statements_found=len(results),
        notification_sent=sent,
    )
    
    # ✅ Log the result
    log = NotificationLog(
        user_id=user_id,
        ntfy_topic=user.ntfy_topic,
        statements_found=result.statements_found,
        notification_sent=result.notification_sent,
        error_message=None if sent else "Failed to send",
    )
    self.session.add(log)
    self.session.commit()
    
    return result
```

4. **Add API endpoints:**
- `GET /notifications/history` - list user's notification history
- `GET /notifications/history/{id}` - get specific log entry

5. **Add frontend UI:** Show notification history in Settings

**Acceptance Criteria:**
- [ ] NotificationLog model created with migration
- [ ] All notifications are logged
- [ ] API endpoints for history work
- [ ] Frontend shows notification history
- [ ] Users can see success/failure status

---

### [ ] Add user-customizable notification times
**Priority:** Medium  
**Effort:** 4-5 hours  
**Files:** User model, migration, API, frontend

**Task:**
Allow users to set their preferred notification time instead of using a global schedule.

**Implementation Steps:**

1. **Update User model:**
```python
# backend/app/domains/users/domain/models.py
class UserBase(SQLModel):
    # ... existing fields ...
    notifications_enabled: bool = Field(default=False)
    ntfy_topic: str | None = Field(default=None, max_length=100)
    notification_hour: int = Field(default=22, ge=0, le=23)
    notification_minute: int = Field(default=0, ge=0, le=59)
```

2. **Create migration:** Add `notification_hour` and `notification_minute` to user table

3. **Update scheduler:** Process users individually at their preferred times
```python
async def _run_loop(self) -> None:
    while self._running:
        # Check every minute instead of once per day
        await asyncio.sleep(60)
        
        now = datetime.now(UTC)
        current_time = time(now.hour, now.minute)
        
        # Find users who want notifications now
        users_to_notify = self.session.exec(
            select(User).where(
                User.notifications_enabled.is_(True),
                User.notification_hour == now.hour,
                User.notification_minute == now.minute
            )
        ).all()
        
        # Send notifications
        for user in users_to_notify:
            await self.execute_for_user(user.id)
```

4. **Update API:** Allow users to update their preferred time
5. **Update frontend:** Add time picker in Settings

**Acceptance Criteria:**
- [ ] Users can set custom notification time
- [ ] Scheduler checks each minute for due notifications
- [ ] Frontend UI for time selection
- [ ] Default times in migration

---

### [ ] Add topic regeneration endpoint
**Priority:** Medium  
**Effort:** 1-2 hours  
**Files:** API route, frontend

**Task:**
Add an endpoint to allow users to regenerate their ntfy topic.

**Implementation:**

1. **Add API endpoint:**
```python
# backend/app/api/routes/notifications/manage.py
@router.post("/regenerate-topic")
async def regenerate_topic(
    session: SessionDep,
    current_user: CurrentUser,
) -> UserPublic:
    """Regenerate the user's ntfy topic."""
    user = session.get(User, current_user.id)
    user.ntfy_topic = f"pf-app-{uuid.uuid4()}"
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
```

2. **Update frontend:** Add button in Notifications tab
```vue
<Button
  label="Regenerate Topic"
  icon="pi pi-refresh"
  @click="handleRegenerate"
  severity="secondary"
  outlined
/>
```

**Acceptance Criteria:**
- [ ] Endpoint generates new unique topic
- [ ] Old topic is no longer used
- [ ] Frontend has regenerate button
- [ ] Users are warned about subscription update

---

## 🔵 Low Priority (Nice to Have)

### [ ] Add separate test notification endpoint
**Priority:** Low  
**Effort:** 1 hour  
**Files:** New API endpoint, frontend

**Task:**
Create a dedicated endpoint that sends a test notification regardless of due statements.

**Implementation:**
```python
@router.post("/test")
async def send_test_notification(
    session: SessionDep,
    current_user: CurrentUser,
) -> TriggerResponse:
    """Send a test notification to verify setup."""
    ntfy_client = NtfyClient(settings.NTFY_INTERNAL_URL)
    
    success = await ntfy_client.send(
        topic=current_user.ntfy_topic,
        title="Test Notification",
        message="If you see this, your notifications are working! 🎉",
        priority=4,
        tags=["test", "checkmark"],
    )
    
    return TriggerResponse(
        statements_found=0,
        notification_sent=success,
    )
```

**Acceptance Criteria:**
- [ ] Test notification works without due statements
- [ ] Clear success/failure feedback
- [ ] Button in UI

---

### [ ] Fix type annotations and LSP errors
**Priority:** Low  
**Effort:** 30 minutes  
**Files:** Multiple files

**Task:**
Fix type annotations flagged by LSP:
- `dict` type should be `dict[str, str]` or similar
- Boolean comparisons with SQLModel columns
- List type annotations

**Files to Fix:**
1. `backend/app/domains/notifications/service/ntfy_client.py`
2. `backend/app/domains/notifications/usecases/send_due_notifications/usecase.py`
3. `backend/tests/domains/notifications/service/test_notification_scheduler.py`

**Acceptance Criteria:**
- [ ] No LSP errors
- [ ] Type checking passes with `mypy`
- [ ] All imports correct

---

### [ ] Add frontend tests for useNotifications composable
**Priority:** Low  
**Effort:** 2-3 hours  
**Files:** `frontend/tests/composables/test-useNotifications.ts` (new)

**Task:**
Write Vitest tests for the `useNotifications` composable.

**Test Cases:**
1. `fetchSettings` - loads user data correctly
2. `toggleNotifications` - updates notifications_enabled
3. `testNotification` - calls API and returns result
4. Error handling - sets error state on failure
5. Loading states - sets isLoading during API calls

**Acceptance Criteria:**
- [ ] All functions are tested
- [ ] Error paths are tested
- [ ] Loading states are verified
- [ ] Tests pass in CI

---

### [ ] Review and separate unrelated API changes
**Priority:** Low  
**Effort:** 30 minutes  
**Files:** `frontend/src/api/core/request.ts`, `frontend/src/api/core/ApiRequestOptions.ts`

**Task:**
Review changes to these files and determine if they're related to notifications or accidental.

**Action:**
1. Check if changes are intentional or formatting
2. If unrelated, move to separate branch
3. If intentional, add comments explaining why

**Acceptance Criteria:**
- [ ] Each change is justified
- [ ] Unrelated changes separated
- [ ] PR review feedback incorporated

---

## 📋 Summary

### Effort Estimation

| Priority | Items | Total Effort |
|-----------|--------|--------------|
| Critical | 3 | ~30 minutes |
| High | 6 | ~6-7 hours |
| Medium | 5 | ~12-14 hours |
| Low | 5 | ~5-6 hours |

**Total Estimated Effort:** ~24-28 hours

### Recommended Order

1. **Before Merge** (Critical)
   - Fix migration `down_revision`
   - Fix session management
   - Add env validation

2. **Week 1 After Merge** (High Priority)
   - Fix timezone
   - Decide on `ntfy_public_url`
   - Add topic validation
   - Add error display
   - Create documentation

3. **Week 2-3** (Medium Priority)
   - Add integration tests
   - Implement concurrent processing
   - Add notification history

4. **Week 4+** (Low Priority / Future)
   - User-customizable times
   - Topic regeneration
   - Separate test endpoint
   - Type annotations cleanup

---

## 📝 Notes

### Dependencies
- Integration tests require real database fixtures
- Notification history depends on database migration
- User times feature requires scheduler rewrite

### Risks
- Scheduler concurrency changes may introduce race conditions
- Topic regeneration requires user to update their phone app
- User times feature is complex (needs minute-level scheduler)

### Considerations
- Some items (like user times) significantly change the architecture
- Consider if notification history is actually needed for MVP
- Documentation could be created in parallel with other tasks
