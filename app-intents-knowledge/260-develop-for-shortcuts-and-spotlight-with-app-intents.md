# Develop for Shortcuts and Spotlight with App Intents - WWDC25 Session 260

## Session Overview

**Presenter**: Ayaka (Shortcuts team)

**Description**: Learn about how building App Intents that make actions available and work best with the new features in Shortcuts and Spotlight on Mac. We'll show you how your actions combine in powerful ways with the new Apple Intelligence actions available in the Shortcuts app. We'll deep-dive into how the new "Use Model" action works, and how it interacts with your app's entities. And we'll discuss how to use the App Intents APIs to make your actions available in Spotlight.

## Key Concepts and Features

### 1. Use Model Action (New in 2025)

The "Use Model" action is one of the many new Intelligent actions added to Shortcuts this year, alongside actions for Image Playground, Writing Tools, and more.

#### Key Features:
- **Model Options**:
  - Large server-based model on Private Cloud Compute (complex requests with privacy protection)
  - On-device model (simple requests without network connection)
  - ChatGPT (broad world knowledge and expertise)

- **Output Types**:
  - Text (supports Rich Text)
  - Dictionary (structured data)
  - Boolean
  - Content from your apps (App Entities)

- **Follow Up Capability**: Users can refine outputs through conversational follow-ups before passing to the next action

#### Best Practices for App Developers:

##### Supporting Rich Text
- Use `AttributedString` type for text parameters where appropriate
- Enables lossless transfer of formatted content (bold, italic, lists, tables)
- Referenced sessions:
  - "What's New in Foundation"
  - Rich Text "Code-along" session

##### Working with App Entities
When passing App Entities to the model, ensure proper JSON representation:

1. **Entity Properties**: All properties exposed to Shortcuts are converted to strings
2. **Type Display Representation**: Include name to hint what the entity represents
3. **Display Representation**: Title and subtitle are included

Example JSON representation of a Calendar Event:
```json
{
  "type": "Calendar Event",
  "title": "WWDC Keynote",
  "subtitle": "June 10, 2025",
  "eventTitle": "WWDC Keynote",
  "startDate": "2025-06-10T10:00:00",
  "endDate": "2025-06-10T12:00:00"
}
```

### 2. Find Actions for Entities

To make entities available for the Use Model action, implement Find actions through:

#### Option 1: Custom Queries
- Conform to `EnumerableEntityQuery` protocol
- Conform to `EntityPropertyQuery` protocol

#### Option 2: Indexed Entity (New APIs)
If you already adopt `IndexedEntity` protocol:

```swift
struct EventEntity: AppEntity, IndexedEntity {
    static var typeDisplayRepresentation = TypeDisplayRepresentation(name: "Calendar Event")
    
    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(
            title: "\(eventTitle)",
            subtitle: "\(startDate.formatted())"
        )
    }
    
    // Associate properties with Spotlight attributes
    @Property(title: "Event Title", indexingKey: .eventTitle)
    var eventTitle: String
    
    @Property(title: "Start Date")
    var startDate: Date
    
    @Property(title: "End Date")
    var endDate: Date
    
    // Custom indexing key for properties without existing attribute keys
    @Property(title: "Notes", customIndexingKey: "eventNotes")
    var notes: String?
}
```

### 3. Spotlight on Mac (New in 2025)

Your apps can now show actions directly in Spotlight on Mac by adopting App Intents.

#### Requirements for Spotlight:
1. **Parameter Summary**: Must contain all required parameters without default values
2. **Visibility**: Intent must not be hidden from Shortcuts/Spotlight
3. **Perform Method**: Intent must have a perform method

#### Example Intent Configuration:
```swift
struct CreateEventIntent: AppIntent {
    static var title: LocalizedStringResource = "Create Event"
    
    @Parameter(title: "Title")
    var title: String
    
    @Parameter(title: "Start Date")
    var startDate: Date
    
    @Parameter(title: "End Date")
    var endDate: Date
    
    @Parameter(title: "Notes", default: "")
    var notes: String
    
    static var parameterSummary: some ParameterSummary {
        Summary("Create event \(\.$title) from \(\.$startDate) to \(\.$endDate)")
    }
    
    func perform() async throws -> some IntentResult {
        // Implementation
    }
}
```

#### Optimizing for Spotlight:

##### 1. Suggestions
Implement protocols to provide parameter suggestions:
- `suggestedEntities()` in `EntityQuery` protocol - for subset of large lists
- `allEntities()` in `EnumerableEntityQuery` protocol - for small, bounded lists

##### 2. Search Support
- Implement `EntityStringQuery` protocol
- Or use `IndexedEntity` for automatic search

##### 3. Tag On-Screen Content
```swift
// In your view controller or scene
let activity = NSUserActivity(activityType: "com.example.viewEvent")
activity.appEntityIdentifier = eventEntity.id
self.userActivity = activity
```

##### 4. Background vs Foreground Intents
Separate intents for different experiences:
- Background intent: Quick actions without opening app
- Foreground intent: Actions that open the app
- Use `opensIntent` to connect them:

```swift
struct CreateEventIntent: AppIntent {
    func perform() async throws -> some IntentResult & OpensIntent {
        let event = // create event
        return .result(opensIntent: OpenEventIntent(event: event))
    }
}
```

### 4. Automations on Mac (New in 2025)

Personal automations now available on Mac with new automation types:
- Folder automations
- External drive automations
- Time of Day (from iOS)
- Bluetooth (from iOS)

All intents available on macOS (including iOS apps installable on macOS) are automatically available for automations.

## Code Examples

### Example 1: Supporting Rich Text in App Intents

```swift
struct CreateNoteIntent: AppIntent {
    static var title: LocalizedStringResource = "Create Note"
    
    @Parameter(title: "Title")
    var title: String
    
    @Parameter(title: "Content")
    var content: AttributedString  // Support rich text from Use Model action
    
    func perform() async throws -> some IntentResult {
        // Create note with rich text content
        let note = Note(title: title, content: content)
        try await noteManager.save(note)
        return .result()
    }
}
```

### Example 2: Making Entities Work with Use Model

```swift
struct RecipeEntity: AppEntity {
    static var typeDisplayRepresentation = TypeDisplayRepresentation(name: "Recipe")
    
    var id: String
    var name: String
    var ingredients: [String]
    var instructions: String
    
    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(
            title: "\(name)",
            subtitle: "\(ingredients.count) ingredients"
        )
    }
    
    // Expose all properties you want the model to reason over
    static var defaultQuery = RecipeQuery()
}

struct RecipeQuery: EntityQuery {
    func entities(for identifiers: [String]) async throws -> [RecipeEntity] {
        // Return recipes matching identifiers
    }
    
    func suggestedEntities() async throws -> [RecipeEntity] {
        // Return recently used or favorite recipes
    }
}
```

### Example 3: Predictable Intent for Spotlight

```swift
struct SendMessageIntent: AppIntent, PredictableIntent {
    static var title: LocalizedStringResource = "Send Message"
    
    static var prediction: IntentPrediction {
        IntentPrediction(
            intent: SendMessageIntent(),
            intentPredictionConfiguration: IntentPredictionConfiguration(
                suggestedInvocationPhrase: "Send a message"
            )
        )
    }
    
    @Parameter(title: "Recipient")
    var recipient: ContactEntity
    
    @Parameter(title: "Message")
    var message: String
    
    func perform() async throws -> some IntentResult {
        // Send message implementation
    }
}
```

## Best Practices

### 1. Entity Design
- Expose all properties you want models to reason over
- Provide clear type display representations
- Include meaningful titles and subtitles in display representations

### 2. Parameter Design
- Make parameters optional when possible for Spotlight
- Provide default values for required parameters
- Write clear, natural parameter summaries

### 3. Performance
- Implement suggestions for quick parameter filling
- Support background execution where appropriate
- Provide foreground alternatives with `opensIntent`

### 4. Rich Content Support
- Use `AttributedString` for text that may contain formatting
- Support tables, lists, and other rich content from AI models

## Resources and Links

### Documentation
- [App Intents](https://developer.apple.com/documentation/AppIntents)
- [App Shortcuts](https://developer.apple.com/documentation/AppIntents/app-shortcuts)
- [Donating Shortcuts](https://developer.apple.com/documentation/SiriKit/donating-shortcuts)

### Design Guidelines
- [Human Interface Guidelines: App Shortcuts](https://developer.apple.com/design/human-interface-guidelines/app-shortcuts)

### Sample Code
- [Soup Chef: Accelerating App Interactions with Shortcuts](https://developer.apple.com/documentation/SiriKit/soup-chef-accelerating-app-interactions-with-shortcuts)
- App Intents Sample Code app (mentioned for EntityStringQuery example)
- App Intents Travel Tracking App (mentioned for IndexedEntity example)

### Downloads
- [HD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/260/8/8d3b0b9e-3bdb-4661-b333-069c3612b565/downloads/wwdc2025-260_hd.mp4?dl=1)
- [SD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/260/8/8d3b0b9e-3bdb-4661-b333-069c3612b565/downloads/wwdc2025-260_sd.mp4?dl=1)

## Related Sessions

### WWDC23
- [Design Shortcuts for Spotlight](https://developer.apple.com/videos/play/wwdc2023/10193)
- [Spotlight your app with App Shortcuts](https://developer.apple.com/videos/play/wwdc2023/10102)

### Referenced in This Session
- "What's New in Foundation" (for AttributedString support)
- Rich Text "Code-along" session
- "Design App Intents for system experiences"
- "Exploring New Advances in App Intents"
- "Dive into App Intents"
- "What's new in App Intents" (2024)

## Summary of New App Intents Features in 2025

1. **Use Model Action**: Integrate Apple Intelligence models directly into shortcuts
2. **Rich Text Support**: Handle formatted content from AI models with AttributedString
3. **Spotlight Integration on Mac**: Run app intents directly from Spotlight
4. **Mac Automations**: New automation triggers including folder and external drive events
5. **Enhanced Entity Indexing**: New APIs for associating entity properties with Spotlight attributes

These features enable developers to create more powerful, AI-enhanced integrations that work seamlessly across Apple's platforms, making app functionality more accessible and intelligent than ever before.