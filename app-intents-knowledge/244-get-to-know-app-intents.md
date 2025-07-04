# Get to know App Intents - WWDC25 Session 244

## Session Overview

**Session:** 244  
**Title:** Get to know App Intents  
**Conference:** WWDC 2025  

Learn about the App Intents framework and its increasingly critical role within Apple's developer platforms. This session provides a ground-up introduction of the core concepts: intents, entities, queries, and much more. You'll learn how these pieces fit together and let you integrate your app through Apple's devices, from software features like Spotlight and Shortcuts to hardware features like the Action button. We'll also walk through how App Intents is your app's gateway to integrating with Apple Intelligence going forward.

## Table of Contents
- [App Intents Ecosystem](#app-intents-ecosystem)
- [Core Concepts](#core-concepts)
- [Creating Your First App Intent](#creating-your-first-app-intent)
- [App Enums and Parameters](#app-enums-and-parameters)
- [App Shortcuts](#app-shortcuts)
- [App Entities](#app-entities)
- [Entity Queries](#entity-queries)
- [Advanced Features](#advanced-features)
- [How It Works](#how-it-works)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)
- [Resources](#resources)
- [Related Sessions](#related-sessions)

## App Intents Ecosystem

App Intents is an ecosystem that enables apps to extend functionality across the system — Spotlight, Action Button, Widgets, Control Center, and Apple Pencil Pro. People can perform app actions from anywhere, even when not in the app. You define app actions as intents, which can take parameters and return values using App Enums for constants, or App Entities for dynamic types. App Shortcuts, built from intents and parameters, enhance accessibility and discoverability through Spotlight, Siri, and the Action Button.

### Key Integration Points:
- **Spotlight**: Make your app content searchable and actionable
- **Siri**: Voice-driven interactions with your app
- **Shortcuts**: Multi-step automations using your app's capabilities
- **Action Button**: Quick access to frequently used features
- **Control Center**: Surface key actions in the system UI
- **Widgets**: Interactive components that can trigger intents
- **Apple Pencil Pro**: Context-aware actions for creative apps
- **Apple Intelligence**: Foundation for AI-powered interactions

## Core Concepts

### Intents
Intents are the fundamental building blocks that represent actions your app can perform. Each intent:
- Adopts the `AppIntent` protocol
- Has a title for user display
- Implements a `perform()` method
- Can return various result types
- Supports different execution modes (foreground/background)

### Entities
App Entities represent dynamic data in your app (like landmarks, notes, or contacts). They:
- Adopt the `AppEntity` protocol
- Have unique identifiers
- Provide display representations
- Support queries for data retrieval

### Queries
Queries enable the system to reason about your entities by:
- Retrieving all entities
- Matching specific strings or properties
- Uniquely referencing entities by ID
- Supporting different query types (string, property, etc.)

### App Shortcuts
App Shortcuts automatically expose intents across the system. They:
- Define phrases users can speak to Siri
- Appear in Spotlight search
- Can be assigned to the Action Button
- Include short titles and system images

## Creating Your First App Intent

### Basic Intent Structure

```swift
struct NavigateIntent: AppIntent {
    static let title: LocalizedStringResource = "Navigate to Landmarks"
    static let supportedModes: IntentModes = .foreground
    
    @MainActor
    func perform() async throws -> some IntentResult {
        Navigator.shared.navigate(to: .landmarks)
        return .result()
    }
}
```

Key components:
- `title`: User-visible name for the intent
- `supportedModes`: Whether the app needs to launch (.foreground) or can run in background
- `perform()`: The actual work done when the intent executes
- `@MainActor`: Ensures UI updates happen on the main thread

## App Enums and Parameters

### Creating an App Enum

App Enums represent a fixed set of options:

```swift
enum NavigationOption: String, AppEnum {
    case landmarks
    case map
    case collections
    
    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Navigation Option"
    
    static let caseDisplayRepresentations: [NavigationOption: DisplayRepresentation] = [
        .landmarks: "Landmarks",
        .map: "Map",
        .collections: "Collections"
    ]
}
```

### Adding Parameters to Intents

Parameters make intents flexible and interactive:

```swift
struct NavigateIntent: AppIntent {
    static let title: LocalizedStringResource = "Navigate to Section"
    static let supportedModes: IntentModes = .foreground
    
    @Parameter
    var navigationOption: NavigationOption
    
    @MainActor
    func perform() async throws -> some IntentResult {
        Navigator.shared.navigate(to: navigationOption)
        return .result()
    }
}
```

### Enhanced Display with Images

```swift
static let caseDisplayRepresentations = [
    NavigationOption.landmarks: DisplayRepresentation(
        title: "Landmarks",
        image: .init(systemName: "building.columns")
    ),
    NavigationOption.map: DisplayRepresentation(
        title: "Map",
        image: .init(systemName: "map")
    ),
    NavigationOption.collections: DisplayRepresentation(
        title: "Collections",
        image: .init(systemName: "book.closed")
    )
]
```

### Parameter Summaries

Provide natural language summaries for better UX:

```swift
struct NavigateIntent: AppIntent {
    static let title: LocalizedStringResource = "Navigate to Section"
    static let supportedModes: IntentModes = .foreground
    
    static var parameterSummary: some ParameterSummary {
        Summary("Navigate to \(\.$navigationOption)")
    }
    
    @Parameter(
        title: "Section",
        requestValueDialog: "Which section?"
    )
    var navigationOption: NavigationOption
    
    @MainActor
    func perform() async throws -> some IntentResult {
        Navigator.shared.navigate(to: navigationOption)
        return .result()
    }
}
```

## App Shortcuts

### Defining App Shortcuts

```swift
struct TravelTrackingAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: NavigateIntent(),
            phrases: [
                "Navigate in \(.applicationName)",
                "Navigate to \(\.$navigationOption) in \(.applicationName)"
            ],
            shortTitle: "Navigate",
            systemImageName: "arrowshape.forward"
        )
    }
}
```

Key features:
- **Phrases**: Natural language triggers for Siri
- **Short Title**: Compact name for UI displays
- **System Image**: Visual representation
- **Parameter Placeholders**: Dynamic parts of phrases using `\(\.$parameterName)`

## App Entities

### Creating an App Entity

```swift
struct LandmarkEntity: AppEntity {
    var id: Int { landmark.id }
    
    @ComputedProperty
    var name: String { landmark.name }
    
    @ComputedProperty
    var description: String { landmark.description }
    
    let landmark: Landmark
    
    static let typeDisplayRepresentation = TypeDisplayRepresentation(name: "Landmark")
    
    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(title: "\(name)")
    }
    
    static let defaultQuery = LandmarkEntityQuery()
}
```

## Entity Queries

### Basic Entity Query

```swift
struct LandmarkEntityQuery: EntityQuery {
    @Dependency
    var modelData: ModelData
    
    func entities(for identifiers: [LandmarkEntity.ID]) async throws -> [LandmarkEntity] {
        modelData
            .landmarks(for: identifiers)
            .map(LandmarkEntity.init)
    }
}
```

### Dependency Injection

Register dependencies early in your app lifecycle:

```swift
@main
struct LandmarksApp: App {
    init() {
        AppDependencyManager.shared.add {
            ModelData()
        }
    }
}
```

### Advanced Query Types

#### Enumerable Entity Query
```swift
extension LandmarkEntityQuery: EnumerableEntityQuery {
    func allEntities() async throws -> [LandmarkEntity] {
        // Return all entities
    }
}
```

#### Entity Property Query
```swift
extension LandmarkEntityQuery: EntityPropertyQuery {
    static var properties = QueryProperties {
        // Define queryable properties
    }
    
    static var sortingOptions = SortingOptions {
        // Define sorting options
    }
    
    func entities(
        matching comparators: [Predicate<LandmarkEntity>],
        mode: ComparatorMode,
        sortedBy: [Sort<LandmarkEntity>],
        limit: Int?
    ) async throws -> [LandmarkEntity] {
        // Implement property-based filtering
    }
}
```

#### Entity String Query
```swift
extension LandmarkEntityQuery: EntityStringQuery {
    func entities(matching: String) async throws -> [LandmarkEntity] {
        modelData.landmarks
            .filter {
                $0.name.contains(matching) ||
                $0.description.contains(matching)
            }
            .map(LandmarkEntity.init)
    }
}
```

## Advanced Features

### Returning Values and Showing UI

```swift
struct ClosestLandmarkIntent: AppIntent {
    static let title: LocalizedStringResource = "Find Closest Landmark"
    
    @Dependency
    var modelData: ModelData
    
    @MainActor
    func perform() async throws -> some ReturnsValue<LandmarkEntity> & ProvidesDialog & ShowsSnippetView {
        let landmark = try await modelData.findClosestLandmark()
        return .result(
            value: landmark,
            dialog: "The closest landmark to you is \(landmark.name)",
            view: ClosestLandmarkView(landmark: landmark)
        )
    }
}
```

### Making Entities Transferable

Enable sharing between apps:

```swift
extension LandmarkEntity: Transferable {
    static var transferRepresentation: some TransferRepresentation {
        DataRepresentation(exportedContentType: .image) {
            return try $0.imageRepresentationData
        }
    }
}
```

### Indexed Entities for Spotlight

Enable semantic search in Spotlight:

```swift
struct LandmarkEntity: IndexedEntity {
    // ...
    
    @Property(indexingKey: \.displayName)
    var name: String
    
    @Property(indexingKey: \.contentDescription)
    var description: String
}
```

### Open Intents for Navigation

```swift
struct OpenLandmarkIntent: OpenIntent, TargetContentProvidingIntent {
    static let title: LocalizedStringResource = "Open Landmark"
    
    @Parameter(title: "Landmark", requestValueDialog: "Which landmark?")
    var target: LandmarkEntity
}

// In your SwiftUI view:
struct LandmarksNavigationStack: View {
    @State var path: [Landmark] = []
    
    var body: some View {
        NavigationStack(path: $path) {
            // ...
        }
        .onAppIntentExecution(OpenLandmarkIntent.self) { intent in
            path.append(intent.target.landmark)
        }
    }
}
```

### Suggested Entities

Provide smart suggestions:

```swift
struct LandmarkEntityQuery: EntityQuery {
    // ...
    
    func suggestedEntities() async throws -> [LandmarkEntity] {
        modelData
            .favoriteLandmarks()
            .map(LandmarkEntity.init)
    }
}
```

### Updating App Shortcut Parameters

Keep shortcuts fresh with current data:

```swift
TravelTrackingAppShortcuts.updateAppShortcutParameters()
```

## How It Works

App Intents uses Swift source code at build time to generate an App Intents representation, which is then stored within the app or framework. This allows the system to understand the app's capabilities without running it.

### Key Technical Details:
- **Build-Time Processing**: Intent metadata is extracted during compilation
- **Static Metadata**: The system can understand your app's capabilities without launching it
- **Unique Identifiers**: Intent names serve as unique IDs
- **Return Types**: The perform method's return signature defines result rendering

### Sharing App Intents Between Targets

Use App Intents Packages for code sharing:

```swift
// TravelTrackingKit
public struct TravelTrackingKitPackage: AppIntentsPackage {}
public struct LandmarkEntity: AppEntity {}

// TravelTracking App
struct TravelTrackingPackage: AppIntentsPackage {
    static var includedPackages: [any AppIntentsPackage.Type] {
        [TravelTrackingKitPackage.self]
    }
}

// App Intents Extension
struct TravelTrackingExtensionPackage: AppIntentsPackage {
    static var includedPackages: [any AppIntentsPackage.Type] {
        [TravelTrackingKitPackage.self]
    }
}
```

## Code Examples

All code examples from this session are included above in their respective sections. Here's a quick reference:

1. **Basic Intent**: NavigateIntent
2. **App Enum**: NavigationOption
3. **Parameterized Intent**: NavigateIntent with parameters
4. **App Shortcuts**: TravelTrackingAppShortcuts
5. **App Entity**: LandmarkEntity
6. **Entity Query**: LandmarkEntityQuery
7. **Advanced Intent**: ClosestLandmarkIntent
8. **Transferable Entity**: LandmarkEntity extension
9. **Indexed Entity**: LandmarkEntity with indexing
10. **Open Intent**: OpenLandmarkIntent
11. **App Intents Package**: Multi-target sharing

## Best Practices

### Intent Design
- Keep intents focused on single actions
- Use clear, descriptive titles
- Choose appropriate execution modes (foreground vs background)
- Provide helpful parameter dialogs

### Entity Design
- Use computed properties for dynamic values
- Implement proper display representations
- Index important properties for search
- Keep entity data lightweight

### Query Implementation
- Register dependencies early in app lifecycle
- Implement appropriate query protocols for your use case
- Optimize queries for performance
- Handle edge cases gracefully

### App Shortcuts
- Create natural, conversational phrases
- Include parameter variations
- Use descriptive short titles
- Choose appropriate system images

### Performance
- Process metadata at build time
- Minimize entity data size
- Cache query results when appropriate
- Use async/await properly

## Resources

### Documentation
- [Accelerating app interactions with App Intents](https://developer.apple.com/documentation/AppIntents/AcceleratingAppInteractionsWithAppIntents)
- [Adopting App Intents to support system experiences](https://developer.apple.com/documentation/AppIntents/adopting-app-intents-to-support-system-experiences)
- [App intent domains](https://developer.apple.com/documentation/AppIntents/app-intent-domains)
- [App Intents Framework](https://developer.apple.com/documentation/AppIntents)
- [App Shortcuts](https://developer.apple.com/documentation/AppIntents/app-shortcuts)
- [Building a workout app for iPhone and iPad](https://developer.apple.com/documentation/HealthKit/building-a-workout-app-for-iphone-and-ipad)
- [Creating your first app intent](https://developer.apple.com/documentation/AppIntents/Creating-your-first-app-intent)
- [Integrating actions with Siri and Apple Intelligence](https://developer.apple.com/documentation/AppIntents/Integrating-actions-with-siri-and-apple-intelligence)
- [Making actions and content discoverable and widely available](https://developer.apple.com/documentation/AppIntents/Making-actions-and-content-discoverable-and-widely-available)

### Downloads
- [HD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/244/5/54cb9dae-53ff-4b7a-9091-2e1d6b3d779e/downloads/wwdc2025-244_hd.mp4?dl=1)
- [SD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/244/5/54cb9dae-53ff-4b7a-9091-2e1d6b3d779e/downloads/wwdc2025-244_sd.mp4?dl=1)

## Related Sessions

### WWDC25
- **Design interactive snippets** - Learn about designing rich, interactive snippets for App Intents
- **Develop for Shortcuts and Spotlight with App Intents** - Deep dive into Shortcuts and Spotlight integration

### WWDC24
- **Bring your app to Siri** - Siri integration fundamentals
- **Bring your app's core features to users with App Intents** - Core features implementation
- **Design App Intents for system experiences** - Design considerations
- **What's new in App Intents** - Latest updates and features

## Summary

App Intents is the foundation for making your app's functionality available throughout the Apple ecosystem. By implementing intents, entities, and queries, you can:

- Enable voice control through Siri
- Surface content in Spotlight search
- Create powerful Shortcuts automations
- Integrate with system features like the Action Button
- Prepare for Apple Intelligence integration

Start with simple intents, then gradually add parameters, entities, and advanced features as your understanding grows. The framework's flexibility allows you to expose as much or as little functionality as makes sense for your app.

Remember: App Intents is not just about Siri anymore—it's your gateway to deep system integration across all of Apple's platforms and the foundation for AI-powered experiences.