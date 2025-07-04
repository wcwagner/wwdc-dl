# App Intents Quick Reference - WWDC 2025

## Core Components

### Basic App Intent
```swift
struct OrderCoffeeIntent: AppIntent {
    static let title: LocalizedStringResource = "Order Coffee"
    
    @Parameter(title: "Coffee Type")
    var coffeeType: String
    
    @Parameter(title: "Size", default: .medium)
    var size: CoffeeSize
    
    func perform() async throws -> some IntentResult {
        // Implementation
        return .result()
    }
}
```

### App Enum (New Pattern)
```swift
enum CoffeeSize: String, AppEnum {
    case small, medium, large
    
    static let typeDisplayRepresentation = TypeDisplayRepresentation(name: "Coffee Size")
    
    static var caseDisplayRepresentations: [Self: DisplayRepresentation] = [
        .small: "Small",
        .medium: "Medium", 
        .large: "Large"
    ]
}
```

### App Entity
```swift
struct CoffeeOrder: AppEntity {
    static let typeDisplayRepresentation = TypeDisplayRepresentation(name: "Coffee Order")
    
    var id: UUID
    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(title: "\(coffeeType) - \(size)")
    }
    
    // Properties
    var coffeeType: String
    var size: CoffeeSize
}
```

### Entity Query
```swift
struct CoffeeOrderQuery: EntityQuery {
    func entities(for identifiers: [UUID]) async throws -> [CoffeeOrder] {
        // Return orders matching identifiers
    }
    
    func suggestedEntities() async throws -> [CoffeeOrder] {
        // Return recent or favorite orders
    }
}
```

## New in 2025

### Interactive Snippet
```swift
struct ShowWaterIntake: ShowSnippetView {
    static let title: LocalizedStringResource = "Show Water Intake"
    
    var body: some View {
        WaterIntakeView()
    }
}

// In your view
struct WaterIntakeView: View {
    @AppStorage("waterIntake") var waterIntake = 0
    
    var body: some View {
        VStack {
            Text("\(waterIntake) oz")
                .font(.largeTitle)
            
            Button("Add 8 oz") {
                waterIntake += 8
            }
            .snippetAction(AddWaterIntent.self)
        }
        .containerRelativeFrame([.horizontal, .vertical])
    }
}
```

### Use Model Action Support
```swift
struct Recipe: AppEntity {
    // Required for Use Model
    var id: String
    var displayRepresentation: DisplayRepresentation
    
    // Structured data for AI
    var title: String
    var ingredients: [String]
    var instructions: String
    var cookTime: Int
    
    // Rich text support
    func formattedRecipe() -> AttributedString {
        var result = AttributedString()
        // Format with styling
        return result
    }
}
```

### Visual Intelligence Integration
```swift
struct SearchProductIntent: AppIntent, VisualSearchIntent {
    static let searchScopes: [VisualSearchScope] = [.application]
    
    @Parameter(title: "Search Query", requestValueDialog: "What would you like to search for?")
    var searchQuery: String
    
    func perform() async throws -> some IntentResult & ShowsSnippetView {
        return .result(view: ProductSearchResultsView(query: searchQuery))
    }
}
```

### Undoable Intent
```swift
struct DeleteNoteIntent: AppIntent, UndoableIntent {
    static let title: LocalizedStringResource = "Delete Note"
    
    @Parameter(title: "Note")
    var note: Note
    
    func perform() async throws -> some IntentResult {
        try await DataManager.shared.delete(note)
        return .result()
    }
}
```

## App Shortcuts

```swift
struct MyAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: OrderCoffeeIntent(),
            phrases: [
                "Order coffee from \(.applicationName)",
                "Get my usual from \(.applicationName)"
            ],
            shortTitle: "Order Coffee",
            systemImageName: "cup.and.saucer"
        )
    }
}
```

## Configuration Tips

### Info.plist
```xml
<key>NSUserActivityTypes</key>
<array>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER).OrderCoffeeIntent</string>
</array>
```

### Performance Optimization
```swift
struct OptimizedEntity: AppEntity {
    // Expensive computation cached
    @ComputedProperty(\.$items)
    var itemCount: Int
    
    // Large data loaded on demand
    @DeferredProperty var detailedHistory: [HistoryItem]
    
    @Property var items: [Item]
}
```

### Spotlight Integration (Mac)
```swift
extension MyIntent {
    static var isEligibleForSpotlightSearch: Bool { true }
    
    // Additional indexing
    var isIndexable: Bool {
        // Return true for items that should appear in search
    }
}
```

## Common Patterns

### Multiple Choice Resolution
```swift
func perform() async throws -> some IntentResult {
    if needsDisambiguation {
        throw $parameter.needsDisambiguationError(among: options, dialog: "Which one?")
    }
    // Continue with selected option
}
```

### Entity Transfer
```swift
struct ShareableNote: AppEntity, Transferable {
    static var transferRepresentation: some TransferRepresentation {
        DataRepresentation(exportedContentType: .json) { note in
            try JSONEncoder().encode(note)
        }
    }
}
```

### View Control
```swift
func perform() async throws -> some IntentResult & OpensIntent {
    // Do work
    return .result(opensIntent: OpenSpecificView(viewID: "details"))
}
```

## Testing

### In Shortcuts
1. Build and run your app
2. Open Shortcuts app
3. Create new shortcut
4. Add your app's actions
5. Test with various parameters

### In Siri
1. Add App Shortcut phrases
2. Say phrase to Siri
3. Verify snippet appearance
4. Test voice feedback

### In Spotlight (Mac)
1. Ensure intent is eligible
2. Type action in Spotlight
3. Verify appearance
4. Test execution

## Debugging

```swift
// Add logging
func perform() async throws -> some IntentResult {
    print("Intent started with parameters: \(parameter)")
    // Implementation
    print("Intent completed")
    return .result()
}
```

## Common Issues

1. **Intent not appearing**: Check Info.plist configuration
2. **Snippet not showing**: Verify ShowSnippetView implementation
3. **Entity not found**: Check EntityQuery implementation
4. **Poor performance**: Use @ComputedProperty and @DeferredProperty
5. **Siri not recognizing**: Verify App Shortcut phrases

## Key Takeaways

- Start simple with basic intents
- Add App Shortcuts for discoverability
- Use Interactive Snippets for rich experiences
- Structure entities for AI compatibility
- Test across all integration points
- Optimize for performance with lazy loading
- Design for voice-first interactions