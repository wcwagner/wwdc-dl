# Session 230: Wake up to the AlarmKit API

## Overview
This session introduces AlarmKit, a new framework in iOS and iPadOS 26 that allows apps to create and manage alarms with countdown timers. Alarms can appear in the Lock Screen, Dynamic Island, and other system experiences. The framework integrates with App Intents to enable custom alert actions.

## Key Concepts

### AlarmKit Framework
- **Purpose**: Create prominent alerts that occur at fixed, pre-determined times
- **Behavior**: Breaks through silent mode and current focus settings
- **Platform**: iOS and iPadOS 26+
- **Integration**: Works with ActivityKit for Live Activities and App Intents for custom actions

### Alarm Components
1. **Countdown Duration**: Pre-alert and post-alert intervals
2. **Schedule**: Fixed date or recurring pattern
3. **Appearance**: Alert presentation with customizable buttons
4. **Actions**: Custom intents via App Intents framework
5. **Sound**: Default or custom alert sounds

## Authorization

### Setup Requirements
```swift
// Add to Info.plist
NSAlarmKitUsageDescription: "Your app uses alarms to notify you when cooking is complete"
```

### Checking Authorization
```swift
import AlarmKit

func checkAuthorization() {
    switch AlarmManager.shared.authorizationState {
    case .notDetermined:
        // Manually request authorization
    case .authorized:
        // Proceed with scheduling
    case .denied:
        // Inform status is not authorized
    }
}
```

## Creating Alarms

### Basic Alarm Configuration
```swift
typealias AlarmConfiguration = AlarmManager.AlarmConfiguration<CookingData>

let id = UUID()
let duration = Alarm.CountdownDuration(
    preAlert: (10 * 60),  // 10 minutes
    postAlert: (5 * 60)   // 5 minutes for snooze
)

let stopButton = AlarmButton(
    text: "Dismiss",
    textColor: .white,
    systemImageName: "stop.circle"
)

let alertPresentation = AlarmPresentation.Alert(
    title: "Food Ready!",
    stopButton: stopButton
)

let attributes = AlarmAttributes<CookingData>(
    presentation: AlarmPresentation(alert: alertPresentation),
    tintColor: Color.green
)

let alarmConfiguration = AlarmConfiguration(
    countdownDuration: duration,
    attributes: attributes
)

try await AlarmManager.shared.schedule(id: id, configuration: alarmConfiguration)
```

### Schedule Types

#### Fixed Schedule
```swift
let keynoteDateComponents = DateComponents(
    calendar: .current,
    year: 2025,
    month: 6,
    day: 9,
    hour: 9,
    minute: 41
)
let keynoteDate = Calendar.current.date(from: keynoteDateComponents)!
let scheduleFixed = Alarm.Schedule.fixed(keynoteDate)
```

#### Relative Schedule
```swift
let time = Alarm.Schedule.Relative.Time(hour: 7, minute: 0)
let recurrence = Alarm.Schedule.Relative.Recurrence.weekly([.monday, .wednesday, .friday])
let schedule = Alarm.Schedule.Relative(time: time, repeats: recurrence)
```

## Live Activities Integration

### Creating a Live Activity for Countdown
```swift
import AlarmKit
import ActivityKit
import WidgetKit

struct AlarmLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: AlarmAttributes<CookingData>.self) { context in
            switch context.state.mode {
            case .countdown:
                countdownView(context)
            case .paused:
                pausedView(context)
            case .alert:
                alertView(context)
            }
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    leadingView(context)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    trailingView(context)
                }
            } compactLeading: {
                compactLeadingView(context)
            } compactTrailing: {
                compactTrailingView(context)
            } minimal: {
                minimalView(context)
            }
        }
    }
}
```

### Custom Metadata
```swift
struct CookingData: AlarmMetadata {
    let method: Method
    
    init(method: Method) {
        self.method = method
    }
    
    enum Method: String, Codable {
        case frying = "frying.pan"
        case grilling = "flame"
    }
}
```

## Custom Actions with App Intents

### Creating a Custom Action Intent
```swift
public struct OpenInApp: LiveActivityIntent {
    public func perform() async throws -> some IntentResult {
        .result()
    }
    
    public static var title: LocalizedStringResource = "Open App"
    public static var description = IntentDescription("Opens the Sample app")
    public static var openAppWhenRun = true
    
    @Parameter(title: "alarmID")
    public var alarmID: String
    
    public init(alarmID: String) {
        self.alarmID = alarmID
    }
    
    public init() {
        self.alarmID = ""
    }
}
```

### Using Custom Actions
```swift
let secondaryIntent = OpenInApp(alarmID: id.uuidString)

let openButton = AlarmButton(
    text: "Open",
    textColor: .white,
    systemImageName: "arrow.right.circle.fill"
)

let alertPresentation = AlarmPresentation.Alert(
    title: "Food Ready!",
    stopButton: stopButton,
    secondaryButton: openButton,
    secondaryButtonBehavior: .custom  // Important: set to .custom
)

let alarmConfiguration = AlarmConfiguration(
    countdownDuration: duration,
    attributes: attributes,
    secondaryIntent: secondaryIntent
)
```

## System Presentations

### Countdown Presentation
```swift
let pauseButton = AlarmButton(
    text: "Pause",
    textColor: .green,
    systemImageName: "pause"
)

let countdownPresentation = AlarmPresentation.Countdown(
    title: "Cooking",
    pauseButton: pauseButton
)
```

### Paused Presentation
```swift
let resumeButton = AlarmButton(
    text: "Resume",
    textColor: .green,
    systemImageName: "play"
)

let pausedPresentation = AlarmPresentation.Paused(
    title: "Paused",
    resumeButton: resumeButton
)
```

## Alarm Lifecycle Management

```swift
// Schedule an alarm
try await AlarmManager.shared.schedule(id: id, configuration: alarmConfiguration)

// Transition to countdown
try await AlarmManager.shared.countdown(id: id)

// Cancel an alarm
try await AlarmManager.shared.cancel(id: id)

// Stop an alarm
try await AlarmManager.shared.stop(id: id)

// Pause an alarm
try await AlarmManager.shared.pause(id: id)

// Resume an alarm
try await AlarmManager.shared.resume(id: id)
```

## Best Practices

1. **Use Cases**: Best for countdowns with specific intervals (cooking timers) or recurring alerts (wake-up alarms)
2. **Not a Replacement**: Don't use for critical alerts or time-sensitive notifications
3. **Clear Presentation**: Make it easy to understand what the alarm is and what actions are available
4. **Countdown Elements**: Include remaining duration, dismiss button, and pause/resume button in Live Activities
5. **Authorization**: Provide clear usage descriptions to help users make informed decisions

## Resources
- [AlarmKit Documentation](https://developer.apple.com/documentation/AlarmKit)
- [ActivityKit Documentation](https://developer.apple.com/documentation/ActivityKit)
- [App Intents Documentation](https://developer.apple.com/documentation/AppIntents)
- [Creating your first app intent](https://developer.apple.com/documentation/AppIntents/Creating-your-first-app-intent)
- [Human Interface Guidelines: Live Activities](https://developer.apple.com/design/human-interface-guidelines/live-activities)
- [Scheduling an alarm with AlarmKit](https://developer.apple.com/documentation/AlarmKit/scheduling-an-alarm-with-alarmkit)

## Related Sessions
- [Get to know App Intents (WWDC25)](https://developer.apple.com/videos/play/wwdc2025/244)
- [Meet ActivityKit (WWDC23)](https://developer.apple.com/videos/play/wwdc2023/10184)