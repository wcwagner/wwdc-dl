# Session 281: Design Interactive Snippets

## Overview
This session focuses on designing interactive snippets for App Intents. Snippets are compact views that display information from your app and now support buttons and stateful information for additional interactivity. They appear in Siri, Spotlight, and the Shortcuts app.

## Key Concepts

### What are Interactive Snippets?
- **Compact views** displayed by App Intents
- Show **updated information** and offer **quick actions** directly from your app
- Appear **overlaying other content** at the top of the screen
- Remain visible until confirmed, canceled, or swiped away
- Support **rich visual layouts** that reflect your app's identity
- Now include **buttons** and **stateful information** for interactivity

### Where Snippets Appear
- Spotlight
- Siri
- Shortcuts app
- Any place App Intents are supported

## Design Principles

### Appearance

#### Typography
- **Larger text sizes** than system defaults
- Draws attention to most important information
- Makes content **glanceable** for quick, in-the-moment experiences

#### Layout
- **Consistent margins** around content for clarity
- Use `ContainerRelativeShape` API for responsive margins across platforms
- **Avoid content past 340 points in height** (prevents scrolling)
- Keep content **concise** with only essential information
- Link to full app view for additional details if needed

#### Contrast and Readability
- **Vibrant backgrounds** can help snippets stand out
- Check contrast when viewed from a distance
- Go **beyond standard contrast ratios** for better readability
- Increase contrast between content and background if needed

### Interaction

#### Interactive Elements
- **Buttons** for simple, relevant actions
- **Updated data** reflecting latest app information
- Visual feedback (scale and blur) when data updates
- Multiple buttons and updated content can coexist

#### Example: Water Tracking
```
[Water tracking snippet with "Add Water" button]
- Simple button for quick action
- Data updates with visual feedback
- Builds trust in App Intent for routines
```

#### Example: Equalizer
```
[Equalizer snippet with preset buttons]
- Shows updated audio settings
- Multiple preset options available
- Clear, relevant actions supplement main task
```

## Snippet Types

### Result Snippets
- Present information as **outcome of a confirmation**
- No follow-up tasks or decisions needed
- Only includes **"Done" button** at bottom
- Example: Checking order status

### Confirmation Snippets
- Used when intent needs **action before showing result**
- Clear action verb in button (e.g., "Order", "Send", "Start")
- Customizable action verbs:
  - Pre-written options available
  - Custom verbs if pre-written don't fit
- Example: Coffee ordering with customization options

### Flow Pattern
1. **Confirmation snippet** → User takes action
2. **Result snippet** → Shows outcome of choice
3. Helps users understand intent started and completed

## Dialog Considerations

### When to Use Dialog
- **Essential for voice-first interactions**
- Important when using AirPods without screen
- Provides spoken feedback for results or confirmations

### Design Without Dialog Dependency
- Make snippets **understandable on their own**
- Clearly communicate intent purpose visually
- Removes redundancy
- Makes snippets more intuitive

## Best Practices

### Content Design
1. **Keep it glanceable** - Use larger type and clear hierarchy
2. **Be concise** - Only include essential information
3. **Maintain clarity** - Consistent margins and spacing
4. **Ensure readability** - High contrast, especially with vibrant backgrounds

### Interaction Design
1. **Simple actions** - Buttons for routine, relevant tasks
2. **Clear feedback** - Visual updates when actions occur
3. **Build trust** - Show successful action completion
4. **Supplement, don't replace** - Actions should enhance main intent

### Technical Guidelines
- Maximum height: **340 points**
- Use **ContainerRelativeShape** for responsive design
- Provide **adequate spacing** between elements
- Test contrast from various viewing distances

## Resources
- [Displaying static and interactive snippets](https://developer.apple.com/documentation/AppIntents/displaying-static-and-interactive-snippets)

## Related Sessions
- "Develop for shortcuts and spotlight with app intents"
- "Explore advances in app intents"