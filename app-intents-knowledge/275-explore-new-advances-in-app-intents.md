# Explore new advances in App Intents - WWDC25 Session 275

## Session Overview

**Session**: 275 - WWDC 2025  
**Title**: Explore new advances in App Intents  
**Duration**: ~26 minutes

Explore all the new enhancements available in the App Intents framework in this year's releases. Learn about developer quality-of-life improvements like deferred properties, new capabilities like interactive app intents snippets, entity view annotations, how to integrate Visual Intelligence, and much more. This session covers how App Intents is more expressive than ever, while becoming even easier and smoother to adopt. It also shares exciting new clients of App Intents this year like Spotlight and Visual Intelligence, and teaches how to write app intents that work great in those contexts.

## Key Concepts and Features

### 1. Interactive Snippets

Interactive snippets are the major new feature that allows apps to create dynamic, interactive views that display tailored information based on App Intents. These snippets can include buttons and toggles that trigger other App Intents without leaving the current context.

#### Key Components:
- **SnippetIntent Protocol**: New protocol for creating intents that display snippets
- **ShowsSnippetView**: Protocol for returning snippet views
- **Result Snippets**: Display information after an action
- **Confirmation Snippets**: Request additional information before proceeding

#### How It Works:
1. The system runs the intent and displays the snippet
2. Users can interact with buttons/toggles in the snippet
3. Interactions trigger other App Intents
4. The snippet updates in real-time with smooth animations
5. Data stays fresh by fetching from entity queries on refresh

### 2. System-Wide Integration

#### Visual Intelligence (Image Search)
Apps can now respond to image searches directly from camera captures or screenshots:
- Implement `IntentValueQuery` protocol
- Process `SemanticContentDescriptor` data
- Return arrays of app entities
- Support `OpenIntent` for handling taps on results

#### Spotlight Integration
- Make entities conform to `IndexedEntity`
- Annotate properties with indexing keys
- Support `PredictableIntent` for personalized suggestions

#### On-Screen Entities
- Associate entities with views using `userActivity`
- Support `Transferable` protocol for various data types (PDF, plain text, rich text)
- Enable interactions with Siri and ChatGPT about visible content

### 3. User Experience Refinements

#### UndoableIntent
- New protocol allowing users to reverse actions
- Works with familiar gestures (3-finger swipe, shake)
- Register undo actions with the undo manager
- Provides safety net for user experimentation

#### Multiple Choice API
- Present multiple options instead of binary confirmations
- Customize with dialogs and SwiftUI views
- Support different option styles (default, destructive)

#### Supported Modes
- Greater control over app foregrounding behavior
- Different behaviors based on user interaction mode
- Check current mode with `currentMode` property
- Support background, foreground, and dynamic modes

### 4. Convenience APIs

#### View Control APIs
- New `onAppIntentExecution` view modifier
- Views can respond directly to App Intents
- Remove UI code from intents
- Control scene handling with `handlesExternalEvents`

#### Performance Optimizations
- `@ComputedProperty`: Properties calculated on demand
- `@DeferredProperty`: Properties fetched asynchronously
- Both reduce storage and instantiation costs

#### Swift Package Support
- App Intents can now be packaged in Swift Packages
- Use `AppIntentsPackage` protocol
- Greater flexibility and reusability

## Code Examples with Explanations

### Creating an Interactive Snippet

```swift
// Step 1: Create the main intent that returns a snippet
struct ClosestLandmarkIntent: AppIntent {
    static let title: LocalizedStringResource = "Find Closest Landmark"
    
    @Dependency var modelData: ModelData
    
    func perform() async throws -> some ReturnsValue<LandmarkEntity> & ShowsSnippetIntent & ProvidesDialog {
        let landmark = await self.findClosestLandmark()
        
        return .result(
            value: landmark,
            dialog: IntentDialog(
                full: "The closest landmark is \(landmark.name).",
                supporting: "\(landmark.name) is located in \(landmark.continent)."
            ),
            snippetIntent: LandmarkSnippetIntent(landmark: landmark)
        )
    }
}

// Step 2: Create the SnippetIntent
struct LandmarkSnippetIntent: SnippetIntent {
    static let title: LocalizedStringResource = "Landmark Snippet"
    
    @Parameter var landmark: LandmarkEntity
    @Dependency var modelData: ModelData
    
    func perform() async throws -> some IntentResult & ShowsSnippetView {
        let isFavorite = await modelData.isFavorite(landmark)
        
        return .result(
            view: LandmarkView(landmark: landmark, isFavorite: isFavorite)
        )
    }
}

// Step 3: Create the interactive view with buttons
struct LandmarkView: View {
    let landmark: LandmarkEntity
    let isFavorite: Bool
    
    var body: some View {
        // ... view content ...
        
        // Interactive buttons that trigger other intents
        Button(intent: UpdateFavoritesIntent(landmark: landmark, isFavorite: !isFavorite)) {
            /* Heart button */
        }
        
        Button(intent: FindTicketsIntent(landmark: landmark)) {
            /* Find tickets button */
        }
    }
}
```

### Implementing Visual Intelligence Search

```swift
struct LandmarkIntentValueQuery: IntentValueQuery {
    @Dependency var modelData: ModelData
    
    func values(for input: SemanticContentDescriptor) async throws -> [LandmarkEntity] {
        guard let pixelBuffer: CVReadOnlyPixelBuffer = input.pixelBuffer else {
            return []
        }
        
        let landmarks = try await modelData.searchLandmarks(matching: pixelBuffer)
        return landmarks
    }
}

// Support opening entities from search results
struct OpenLandmarkIntent: OpenIntent {
    static var title: LocalizedStringResource = "Open Landmark"
    
    @Parameter(title: "Landmark")
    var target: LandmarkEntity
    
    func perform() async throws -> some IntentResult {
        // Navigate to the landmark
    }
}
```

### Implementing Undoable Actions

```swift
struct DeleteCollectionIntent: UndoableIntent {
    func perform() async throws -> some IntentResult {
        // Confirm deletion...
        
        await undoManager?.registerUndo(withTarget: modelData) { modelData in
            // Restore collection...
        }
        
        await undoManager?.setActionName("Delete \(collection.name)")
        
        // Delete collection...
    }
}
```

### Using View Control APIs

```swift
// Mark the intent as providing target content
extension OpenLandmarkIntent: TargetContentProvidingIntent {}

// Handle the intent in your view
struct LandmarksNavigationStack: View {
    @State var path: [Landmark] = []
    
    var body: some View {
        NavigationStack(path: $path) {
            /* ... */
        }
        .onAppIntentExecution(OpenLandmarkIntent.self) { intent in
            self.path.append(intent.landmark)
        }
    }
}
```

### Performance Optimizations

```swift
// Computed properties - calculated on demand
struct SettingsEntity: UniqueAppEntity {
    @ComputedProperty
    var defaultPlace: PlaceDescriptor {
        UserDefaults.standard.defaultPlace
    }
    
    init() { }
}

// Deferred properties - fetched asynchronously
struct LandmarkEntity: IndexedEntity {
    @DeferredProperty
    var crowdStatus: Int {
        get async throws {
            await modelData.getCrowdStatus(self)
        }
    }
}
```

## Best Practices

### 1. Interactive Snippets
- Keep snippets focused and contextual
- Use buttons for quick actions
- Implement confirmation snippets for complex operations
- Ensure data freshness with proper entity queries
- Provide smooth animations and transitions

### 2. Visual Intelligence Integration
- Return relevant results quickly
- Optimize search performance
- Support pagination for large result sets
- Allow continuing search within the app
- Handle multiple entity types with `@UnionValue`

### 3. User Experience
- Always provide undo for destructive actions
- Use multiple choice for non-binary decisions
- Respect supported modes for appropriate behavior
- Keep intents focused on logic, not UI

### 4. Performance
- Use `@ComputedProperty` for derived values
- Use `@DeferredProperty` for expensive operations
- Avoid storing unnecessary data in entities
- Leverage Swift Packages for code reuse

## Resources and Links

### Official Documentation
- [Accelerating app interactions with App Intents](https://developer.apple.com/documentation/AppIntents/AcceleratingAppInteractionsWithAppIntents)
- [Adopting App Intents to support system experiences](https://developer.apple.com/documentation/AppIntents/adopting-app-intents-to-support-system-experiences)
- [App intent domains](https://developer.apple.com/documentation/AppIntents/app-intent-domains)
- [App Intents Framework](https://developer.apple.com/documentation/AppIntents)
- [App Shortcuts](https://developer.apple.com/documentation/AppIntents/app-shortcuts)
- [Creating your first app intent](https://developer.apple.com/documentation/AppIntents/Creating-your-first-app-intent)
- [Integrating actions with Siri and Apple Intelligence](https://developer.apple.com/documentation/AppIntents/Integrating-actions-with-siri-and-apple-intelligence)
- [Making actions and content discoverable and widely available](https://developer.apple.com/documentation/AppIntents/Making-actions-and-content-discoverable-and-widely-available)

### Video Downloads
- [HD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/275/5/354f4cf3-69e7-40de-b8ac-a7a5ce248c11/downloads/wwdc2025-275_hd.mp4?dl=1)
- [SD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/275/5/354f4cf3-69e7-40de-b8ac-a7a5ce248c11/downloads/wwdc2025-275_sd.mp4?dl=1)

## Related Sessions

### WWDC25
- [Design interactive snippets](https://developer.apple.com/videos/play/wwdc2025/281) - Session 281
- [Develop for Shortcuts and Spotlight with App Intents](https://developer.apple.com/videos/play/wwdc2025/260) - Session 260
- [Get to know App Intents](https://developer.apple.com/videos/play/wwdc2025/244) - Session 244

### WWDC24
- [Bring your app to Siri](https://developer.apple.com/videos/play/wwdc2024/10133)
- [Bring your app's core features to users with App Intents](https://developer.apple.com/videos/play/wwdc2024/10210)
- [Design App Intents for system experiences](https://developer.apple.com/videos/play/wwdc2024/10176)
- [What's new in App Intents](https://developer.apple.com/videos/play/wwdc2024/10134)

## Summary

This session introduced significant enhancements to the App Intents framework, with interactive snippets being the flagship feature. The new capabilities enable apps to provide rich, interactive experiences directly within system interfaces without requiring users to open the app. The integration with Visual Intelligence and improved Spotlight support opens new discovery pathways for app content.

Key takeaways:
- Interactive snippets transform how users interact with app intents
- Visual Intelligence enables powerful image-based searches
- User experience refinements like undo and multiple choice improve usability
- Performance optimizations make entities more efficient
- Swift Package support increases code reusability

These advances make App Intents more powerful and easier to adopt, positioning them as a critical framework for modern iOS app development.