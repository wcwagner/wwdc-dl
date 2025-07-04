# WWDC 2025 App Intents Knowledge Base

This comprehensive knowledge base contains all the latest information about App Intents from WWDC 2025. It covers the newest patterns, features, and best practices for integrating your app with Siri, Spotlight, Shortcuts, and Apple Intelligence.

## Sessions Overview

### 1. [Get to Know App Intents](244-get-to-know-app-intents.md)
**The foundational session** - Start here if you're new to App Intents or want a comprehensive overview.
- Introduction to the App Intents ecosystem
- Core concepts: Intents, Entities, Queries, and App Shortcuts
- Step-by-step implementation guide
- Integration with Siri, Spotlight, and Shortcuts

### 2. [Develop for Shortcuts and Spotlight with App Intents](260-develop-for-shortcuts-and-spotlight-with-app-intents.md)
**Advanced features and AI integration** - Learn about the new Use Model action and enhanced Spotlight support.
- **NEW: Use Model action** for Apple Intelligence integration
- Spotlight on Mac with App Intents
- Mac-specific automations (folder actions, external drive triggers)
- Enhanced entity support for AI models

### 3. [Explore New Advances in App Intents](275-explore-new-advances-in-app-intents.md)
**Cutting-edge features** - Discover the latest advances including interactive snippets and Visual Intelligence.
- **NEW: Interactive Snippets** with buttons and state updates
- Visual Intelligence integration
- Undoable intents
- Performance optimizations with @ComputedProperty and @DeferredProperty

### 4. [Design Interactive Snippets](281-design-interactive-snippets.md)
**Design guidance** - Best practices for creating beautiful, functional interactive snippets.
- Appearance guidelines (typography, layout, contrast)
- Interaction patterns (buttons, state updates)
- Result vs Confirmation snippets
- Voice-first considerations

### 5. [Wake up to the AlarmKit API](230-wake-up-to-alarmkit-api.md)
**Specialized integration** - How AlarmKit uses App Intents for custom alarm actions.
- AlarmKit framework overview
- Custom actions with App Intents
- Live Activities integration
- Authorization and lifecycle management

## Key New Features in 2025

### 1. Interactive Snippets
- Rich, interactive views in Siri, Spotlight, and Shortcuts
- Support for buttons and state updates
- Two types: Result and Confirmation snippets
- ShowSnippetView API for custom layouts

### 2. Use Model Action
- Integrate with Apple Intelligence in Shortcuts
- Support for various output types (text, rich text, app entities)
- Structured entity modeling for AI reasoning
- Privacy-preserving on-device processing

### 3. Visual Intelligence
- On-screen awareness and context
- Search provider integration
- Entity extraction from screen content

### 4. Enhanced Mac Support
- Direct execution from Spotlight
- Folder actions and external drive automations
- Improved performance with lazy loading

### 5. Developer Experience Improvements
- Undoable intents with system-provided UI
- Multiple choice resolution
- Supported modes for better UI adaptation
- Swift Package support

## Implementation Guide

### Getting Started
1. Start with [Get to Know App Intents](244-get-to-know-app-intents.md) for foundational concepts
2. Implement basic intents following the step-by-step guide
3. Add App Shortcuts for Siri and Spotlight discovery

### Adding Interactive Features
1. Review [Design Interactive Snippets](281-design-interactive-snippets.md) for design principles
2. Implement ShowSnippetView following examples in [Explore New Advances](275-explore-new-advances-in-app-intents.md)
3. Test in Siri, Spotlight, and Shortcuts

### Integrating with AI
1. Study the Use Model action in [Develop for Shortcuts and Spotlight](260-develop-for-shortcuts-and-spotlight-with-app-intents.md)
2. Structure your entities for AI model compatibility
3. Test with Apple Intelligence in Shortcuts

### Platform-Specific Features
- **Mac**: Focus on Spotlight integration and automations
- **iOS/iPadOS**: Optimize for Interactive Snippets and Visual Intelligence
- **All Platforms**: Ensure proper App Shortcut configuration

## Best Practices Summary

### Entity Design
- Keep entities focused and single-purpose
- Use stable, unique identifiers
- Implement proper display representations
- Consider AI model compatibility

### Performance
- Use @ComputedProperty for expensive computations
- Implement @DeferredProperty for large data sets
- Optimize entity queries for quick responses
- Test with realistic data volumes

### User Experience
- Make intents predictable and discoverable
- Provide clear, concise phrases
- Design for voice-first interactions
- Test across all integration points

### Testing
- Test in Siri, Spotlight, and Shortcuts
- Verify Interactive Snippets appearance
- Check performance with large data sets
- Validate on all target platforms

## Resources

### Documentation
- [App Intents Framework](https://developer.apple.com/documentation/AppIntents)
- [Creating Your First App Intent](https://developer.apple.com/documentation/AppIntents/creating-your-first-app-intent)
- [Spotlight Integration](https://developer.apple.com/documentation/corespotlight/making-content-searchable)

### Sample Code
- Each session file contains extensive code examples
- Focus on Swift implementations
- Includes both basic and advanced patterns

### Related Technologies
- ActivityKit (for Live Activities)
- AlarmKit (for alarm integrations)
- Core Spotlight (for indexing)
- SwiftUI (for snippet views)

## Next Steps

1. **For Beginners**: Start with session 244, implement a basic intent, then add an App Shortcut
2. **For Existing Apps**: Review sessions 260 and 275 for new features to integrate
3. **For Designers**: Focus on session 281 for Interactive Snippet guidelines
4. **For Advanced Users**: Explore AI integration with Use Model action and Visual Intelligence

This knowledge base represents the state of the art for App Intents as of WWDC 2025. Use it as your comprehensive reference for building deeply integrated app experiences across Apple platforms.