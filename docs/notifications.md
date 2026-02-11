# Setting Up Push Notifications

## What is Ntfy?

[Ntfy](https://ntfy.sh) is a free, open-source push notification service. This project hosts its own ntfy instance to keep your data private and notifications reliable.

Notifications are sent daily (by default at 22:00 UTC) to remind you about credit card payments due the next day.

## Architecture

### System Overview

```mermaid
graph TB
    subgraph Frontend
        UI[NotificationsTab.vue]
        Comp[useNotifications composable]
    end

    subgraph Backend
        API["/api/v1/notifications/trigger"]
        Sched[NotificationScheduler]
        UC[SendDueNotificationsUseCase]
        Client[NtfyClient]
    end

    subgraph Database
        Users[(User)]
        Cards[(CreditCard)]
        Stmts[(CardStatement)]
    end

    subgraph External
        Ntfy[Ntfy Server]
        Phone[Mobile App]
    end

    UI --> Comp
    Comp -->|POST /trigger| API
    Comp -->|GET/PATCH /users/me| Users

    API --> UC
    Sched -->|daily at configured time| UC
    UC --> Users
    UC --> Cards
    UC --> Stmts
    UC --> Client
    Client -->|HTTP POST| Ntfy
    Ntfy -->|push| Phone
```

### Scheduled Notification Flow

```mermaid
sequenceDiagram
    participant App as FastAPI Lifespan
    participant Sched as NotificationScheduler
    participant UC as SendDueNotificationsUseCase
    participant DB as PostgreSQL
    participant Client as NtfyClient
    participant Ntfy as Ntfy Server
    participant Phone as Mobile App

    App->>Sched: start()
    loop Every day at NOTIFICATION_HOUR:NOTIFICATION_MINUTE UTC
        Sched->>Sched: sleep until next run
        Sched->>DB: Open session (context manager)
        Sched->>UC: execute_all()
        UC->>DB: SELECT users WHERE notifications_enabled = true
        DB-->>UC: [User A, User B, ...]

        loop For each enabled user
            UC->>DB: SELECT statements JOIN cards<br/>WHERE due_date = tomorrow AND NOT fully_paid
            DB-->>UC: due statements

            alt No due statements
                UC-->>UC: SendResult(sent=false)
            else Has due statements
                alt User has no ntfy_topic
                    UC->>DB: UPDATE user SET ntfy_topic = "pf-app-{uuid}"
                end
                UC->>UC: Build notification message
                UC->>Client: send(topic, title, message)
                Client->>Ntfy: HTTP POST (JSON payload)
                Ntfy-->>Client: 2xx / error
                Ntfy->>Phone: Push notification
                Client-->>UC: true / false
                UC-->>UC: SendResult(sent=true/false)
            end
        end

        UC-->>Sched: list[SendResult]
        Sched->>Sched: Log summary
        Sched->>DB: Close session
    end

    App->>Sched: stop()
```

### Manual Test Notification Flow

```mermaid
sequenceDiagram
    participant User as Browser
    participant Vue as NotificationsTab
    participant Comp as useNotifications
    participant API as POST /notifications/trigger
    participant UC as SendDueNotificationsUseCase
    participant DB as PostgreSQL
    participant Client as NtfyClient
    participant Ntfy as Ntfy Server

    User->>Vue: Click "Test Notification"
    Vue->>Comp: testNotification()
    Comp->>API: POST /api/v1/notifications/trigger
    API->>UC: execute_for_user(current_user.id)
    UC->>DB: Get user
    UC->>DB: Query due statements (tomorrow, unpaid)

    alt No due statements
        UC-->>API: SendResult(found=0, sent=false)
        API-->>Comp: {statements_found: 0, notification_sent: false}
        Comp-->>Vue: result
        Vue->>User: Toast: "No statements due tomorrow"
    else Has due statements
        UC->>Client: send(topic, title, message)
        Client->>Ntfy: HTTP POST
        Ntfy-->>Client: 200 OK
        UC-->>API: SendResult(found=N, sent=true)
        API-->>Comp: {statements_found: N, notification_sent: true}
        Comp-->>Vue: result
        Vue->>User: Toast: "Test notification sent"
    end
```

### User Onboarding Flow

```mermaid
flowchart TD
    A[User opens Settings > Notifications] --> B[fetchSettings: GET /users/me]
    B --> C{notifications_enabled?}

    C -->|false| D[Show toggle switch OFF]
    D --> E[User toggles ON]
    E --> F[PATCH /users/me<br/>notifications_enabled: true]
    F --> G{ntfy_topic exists?}
    G -->|no| H[Backend auto-generates topic<br/>on first notification trigger]
    G -->|yes| I[Display topic URL]
    H --> I

    C -->|true| I

    I --> J[User copies topic URL]
    J --> K[User opens ntfy mobile app]
    K --> L[User subscribes to topic]
    L --> M[User clicks Test Notification]
    M --> N{Due statements exist?}

    N -->|yes| O[Notification sent to phone]
    N -->|no| P[Info: No statements due tomorrow]

    O --> Q[Setup complete]
```

### Use Case Diagram

```mermaid
flowchart LR
    subgraph Actors
        U((User))
        S((Scheduler))
    end

    subgraph "Notification Use Cases"
        UC1[Enable/Disable<br/>Notifications]
        UC2[View Topic URL]
        UC3[Copy Topic URL]
        UC4[Test Notification]
        UC5[Send Due<br/>Notifications]
        UC6[Auto-generate<br/>Topic]
        UC7[Build Notification<br/>Message]
    end

    U --> UC1
    U --> UC2
    U --> UC3
    U --> UC4
    S --> UC5

    UC4 -.->|includes| UC7
    UC5 -.->|includes| UC7
    UC4 -.->|includes| UC6
    UC5 -.->|includes| UC6
```

## Installation

### iOS

1. Download **ntfy** from the [App Store](https://apps.apple.com/app/ntfy/id1625395874)
2. Open the app
3. Tap **Settings** (gear icon)
4. Under "Users & Appearance", tap **Add another server**
5. Enter your server URL (e.g. `https://ntfy.yourdomain.com`)
6. Tap **Save**

### Android

1. Download **ntfy** from [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy) or [F-Droid](https://f-droid.org/packages/io.heckel.ntfy/)
2. Open the app
3. Tap the **three-dot menu** > **Settings** > **Manage users**
4. Add your server URL (e.g. `https://ntfy.yourdomain.com`)
5. Tap **Save**

## Subscribing to Notifications

1. In the web app, go to **Settings** > **Notifications**
2. Toggle **Enable notifications** on
3. Copy the **topic URL** shown below the toggle (e.g. `https://ntfy.yourdomain.com/pf-app-abc123`)
4. In the ntfy mobile app, tap **+** (Subscribe to topic)
5. Paste the full topic URL
6. Tap **Subscribe**

You will now receive push notifications on your phone.

## Testing Your Setup

After subscribing, click the **Test Notification** button in the Notifications settings tab. If your setup is correct and you have credit card statements due tomorrow, you should receive a notification on your phone within a few seconds.

If there are no statements due tomorrow, the test will report "No statements due tomorrow" -- this is expected behavior.

## Timezone and Scheduling

Notifications are scheduled in **UTC**. The default time is 22:00 UTC. This can be configured by the server administrator via the `NOTIFICATION_HOUR` and `NOTIFICATION_MINUTE` environment variables.

The ntfy container timezone can be configured separately via the `NTFY_TIMEZONE` environment variable (defaults to UTC).

## Troubleshooting

### Not receiving notifications?

- Verify you are subscribed to the correct topic URL in the ntfy app
- Check that your phone allows notifications for the ntfy app (Settings > Notifications > ntfy)
- Make sure the server URL in the ntfy app matches your instance
- Try sending another test notification from the web app

### Topic URL changed?

Your unique topic is generated when you first enable notifications. If you need a new topic:

1. Toggle notifications **off**
2. Toggle notifications **back on**
3. A new topic will be generated
4. Update your subscription in the ntfy mobile app with the new URL

### No notification on test?

The test button triggers the same logic as the daily scheduler. If there are no unpaid statements due tomorrow, no notification will be sent -- the button will show an info message instead.

## Privacy and Security

- Your topic URL is **unique to your account** -- it acts like a private channel
- **Anyone who knows your topic URL** can subscribe to your notifications, so keep it private
- Topic names only contain letters, numbers, dashes, and underscores
- You can regenerate your topic at any time by toggling notifications off and on again
- All notification data stays on your self-hosted ntfy instance
