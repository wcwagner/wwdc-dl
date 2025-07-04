---
session: 266
year: 2025
title: Explore concurrency in SwiftUI
presenters: [Daniel]
duration: 25
---

## About

Discover how SwiftUI leverages Swift concurrency to build safe and responsive apps. Explore how SwiftUI uses the main actor by default and offloads work to other actors. Learn how to interpret concurrency annotations and manage async tasks with SwiftUI's event loop for smooth animations and UI updates. You'll leave knowing how to avoid data races and write code fearlessly.

### Chapters
- [00:00] Introduction
- [02:13] Main-actor Meadows
- [07:17] Concurrency Cliffs
- [16:53] Code Camp
- [23:47] Next steps

### Resources

- [Concurrency](https://developer.apple.com/documentation/Swift/concurrency)
- [Mutex](https://developer.apple.com/documentation/Synchronization/Mutex)
- [The Swift Programming Language: Concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/)
- [Updating an App to Use Swift Concurrency](https://developer.apple.com/documentation/swift/updating_an_app_to_use_swift_concurrency)
- HD Video: [https://devstreaming-cdn.apple.com/videos/wwdc/2025/266/7/c7837487-ed14-4560-8c2c-a583596027ca/downloads/wwdc2025-266_hd.mp4?dl=1](https://devstreaming-cdn.apple.com/videos/wwdc/2025/266/7/c7837487-ed14-4560-8c2c-a583596027ca/downloads/wwdc2025-266_hd.mp4?dl=1)
- SD Video: [https://devstreaming-cdn.apple.com/videos/wwdc/2025/266/7/c7837487-ed14-4560-8c2c-a583596027ca/downloads/wwdc2025-266_sd.mp4?dl=1](https://devstreaming-cdn.apple.com/videos/wwdc/2025/266/7/c7837487-ed14-4560-8c2c-a583596027ca/downloads/wwdc2025-266_sd.mp4?dl=1)

### Related Videos

#### WWDC25
- [Code-along: Elevate an app with Swift concurrency](/videos/play/wwdc2025/270)
- [Embracing Swift concurrency](/videos/play/wwdc2025/268)

#### WWDC23
- [Explore SwiftUI animation](/videos/play/wwdc2023/10156)

## Summary

### [00:00] Introduction
SwiftUI leverages Swift Concurrency to help developers build fast and data-race free apps. Swift 6.2 introduces a new language mode, which marks all types in a module with the @MainActor annotation implicitly. SwiftUI runs code concurrently in various ways and provides concurrency annotations in its APIs to help developers identify and manage concurrency. The session focuses on understanding how SwiftUI handles concurrency to avoid data races and improve app performance.

### [02:13] Main-actor Meadows
SwiftUI's View protocol is @MainActor isolated, making it the compile-time default for UI code. This means most UI code implicitly runs on the main thread, simplifying development and ensuring compatibility with UIKit and AppKit. Data models instantiated within a View are also automatically isolated. SwiftUI's @MainActor annotations reflect its runtime behavior and intended semantics, not just compile-time conveniences.

### [07:17] Concurrency Cliffs
SwiftUI uses background threads for computationally intensive tasks like animations and shape calculations (e.g., `Shape` protocol's `path` method, `visualEffect` closure, `Layout` protocol, `onGeometryChange` closure) to prevent UI hitches. The `Sendable` annotation signals potential data-race conditions when sharing data between the main actor and background threads. To avoid data races, minimize data sharing. When sharing is necessary, make copies of data.

### [16:53] Code Camp
SwiftUI's action callbacks are synchronous by design to ensure immediate UI updates, especially for animations and loading states. Long-running tasks should be initiated asynchronously, but UI updates should remain synchronous. Separate UI logic from non-UI (async) logic, using state as a bridge to trigger UI updates after async tasks complete. Keep the async code in the view simple, and focus on informing the model of UI events. Time-sensitive logic requires SwiftUI's input and output to be synchronous.

### [23:47] Next steps
Swift 6.2 comes with a great default actor isolation setting. If you have an existing app, try it out. You’ll be able to delete most of your @MainActor annotations. Mutex is an important tool for making a class sendable. Check out its official documentation to learn how. Challenge yourself to write some unit tests for the async code in your app. See if you can do it without importing SwiftUI.

## Transcript

[00:07] Hi folks, welcome aboard.
[00:09] I’m your tour guide, Daniel, from the SwiftUI team.
[00:14] Together, we’ll explore the landscape of concurrency,
[00:17] and SwiftUI app development.

[00:21] You’re here because you’ve heard the stories about these
[00:24] dangerous creatures called data-race bugs.
[00:28] You might have run into some yourself in the past.
[00:32] I'm talking about unexpected app states,
[00:35] glitchy animations, and even permanent data losses.
[00:40] But don't worry, this tour is 100% safe.
[00:45] Because with Swift and SwiftUI, we’re leaving those data-race animals
[00:49] in the rear-view mirror.
[00:51] SwiftUI runs your code concurrently in various ways.
[00:55] In this tour, you’ll learn how to identify them
[00:59] via the concurrency annotations from SwiftUI APIs.
[01:03] In the end, I hope you come out more confident, and fearless
[01:07] in your own SwiftUI app adventures.

[01:12] Swift 6.2 introduces a new language mode,
[01:17] which marks all types in a module with the @MainActor annotation implicitly.
[01:23] Everything we’ll see in this tour applies with or without this new mode.
[01:29] This tour features three attractions.
[01:32] We’ll start from the beautiful Meadows at the Main Actor,
[01:36] and appreciate how SwiftUI treats the main actor as the compile time
[01:40] and runtime default for applications.

[01:44] Then we’ll visit Concurrency Cliffs and explore how SwiftUI helps apps
[01:50] avoid UI hitches by offloading work from the main thread,
[01:55] and, at the same time, protects us from data-race bugs in the wild.

[02:01] Finally, we’ll arrive at Camp, situate ourselves,
[02:06] and contemplate on the relationship between your concurrent code,
[02:10] and SwiftUI APIs.

[02:13] Let’s go to our very first stop, Main Actor Meadows.
[02:18] During our tour, I want to collect some nature-inspired color schemes,
[02:22] so I built an app for it.
[02:24] After taking a photo, I can pick how many colors I want,
[02:28] and press the Extract button.
[02:30] The app will pick out complimentary colors from the photo,
[02:34] and show them on screen.

[02:37] I can scroll down to see all the color schemes I’ve extracted,
[02:41] and choose my favorite to export.

[02:45] For the extraction UI, I made a struct ColorExtractorView.
[02:50] It conforms to SwiftUI's view protocol, which declares @MainActor isolation.

### [02:45] UI for extracting colors

```swift
// UI for extracting colors

struct ColorScheme: Identifiable, Hashable {
    var id = UUID()
    let imageName: String
    var colors: [Color]
}

@Observable
final class ColorExtractor {
    var imageName: String
    var scheme: ColorScheme?
    var isExtracting: Bool = false
    var colorCount: Float = 5

    func extractColorScheme() async {}
}

struct ColorExtractorView: View {
    @State private var model = ColorExtractor()

    var body: some View {
            ImageView(
                imageName: model.imageName,
                isLoading: model.isExtracting
            )
            EqualWidthVStack {
                ColorSchemeView(
                    isLoading: model.isExtracting,
                    colorScheme: model.scheme,
                    extractCount: Int(model.colorCount)
                )
                .onTapGesture {
                    guard !model.isExtracting else { return }
                    withAnimation { model.isExtracting = true }
                    Task {
                        await model.extractColorScheme()
                        withAnimation { model.isExtracting = false }
                    }
                }
                Slider(value: $model.colorCount, in: 3...10, step: 1)
                    .disabled(model.isExtracting)
            }
        }
    }
}
```

[02:57] Swift uses data isolation to understand and verify
[03:01] the safety of all mutable states.
[03:04] Throughout the tour, we’ll encounter many concurrency concepts like that.
[03:09] If you’re new to Swift Concurrency or just need a refresher, watch the session
[03:14] “Embracing Swift Concurrency”.
[03:17] In SwiftUI, View is isolated on the @MainActor,
[03:22] and I conform my struct to View.
[03:26] Therefore, the ColorExtractorView becomes @MainActor isolated.
[03:31] This dotted line indicates inferred isolation,
[03:35] meaning, this annotation is implied at compile time,
[03:39] but it’s not actually part of the code I wrote.
[03:42] The overall type being isolated on the @MainActor
[03:45] means all of its members are implicitly isolated as well.

[03:51] This includes the body property that implements the requirement from View,
[03:56] as well as other members I declare, such as this @State variable.

[04:04] Closing up on the body of the view, I'm referring to other member properties,
[04:09] such as model’s scheme, or a binding to model’s colorCount.
[04:16] This is allowed by the compiler because the shared @MainActor isolation
[04:20] guarantees that these accesses are safe.
[04:24] This also feels intuitive.

[04:28] @MainActor is SwiftUI’s compile-time default.
[04:32] This means most of the time, I can just focus on building my app features,
[04:37] and I don’t have to think much about concurrency.
[04:41] I don’t need to annotate the code for concurrency purposes.
[04:45] It's safe automatically.

[04:48] To make some room for more code,
[04:50] I’m just gonna to hide these inferred isolations.

[04:55] This compile time default with @MainActor,
[04:58] extends beyond the synchronous code in my view.

[05:03] My data model’s types don’t need any @MainActor annotations.

[05:08] Because I instantiate the model inside the view’s declaration,
[05:12] Swift will make sure that the model instance is properly isolated.

[05:18] This SchemeContentView has a tap gesture
[05:20] that kicks off the work for color extraction.
[05:24] The color extraction function is asynchronous,
[05:27] so I’m using a Task to switch to an async context, in order to call it.

[05:33] Because the view body is @MainActor isolated,
[05:36] it makes the closure I gave to this task also run on the main thread,
[05:41] which is really convenient.
[05:44] @MainActor isolation is SwiftUI’s compile time default.
[05:48] It makes writing views convenient, and approachable.
[05:52] But, there’s another very practical reason for it.
[05:55] APIs from AppKit and UIKit, are exclusively @MainActor isolated.

### [05:55] AppKit and UIKit require @MainActor: an example

```swift
// AppKit and UIKit require @MainActor
// Example: UIViewRepresentable

struct FancyUILabel: UIViewRepresentable {
    func makeUIView(context: Context) -> UILabel {
        let label = UILabel()
        // customize the label...
        return label
    }
}
```

[06:01] SwiftUI seamlessly interoperates with these frameworks.
[06:05] For example, the protocol UIViewRepresentable
[06:09] refines the View protocol.
[06:12] Similar to a struct, this isolates UIViewRepresentable on @MainActor.

[06:18] So a type that conforms to UIViewRepresentable is also a View.
[06:23] Therefore, it's @MainActor isolated.
[06:26] UILabel’s initializer requires @MainActor isolation.
[06:30] And that works in my makeUIView, because makeUIView
[06:34] is a member of my @MainActor isolated representable type.

[06:39] There’s no need to annotate it with @MainActor.
[06:42] SwiftUI annotates its APIs with @MainActor,
[06:45] because that reflects the default runtime behavior it implements.

### [06:42] UI for extracting colors

```swift
// UI for extracting colors

struct ColorScheme: Identifiable, Hashable {
    var id = UUID()
    let imageName: String
    var colors: [Color]
}

@Observable
final class ColorExtractor {
    var imageName: String
    var scheme: ColorScheme?
    var isExtracting: Bool = false
    var colorCount: Float = 5

    func extractColorScheme() async {}
}

struct ColorExtractorView: View {
    @State private var model = ColorExtractorModel()

    var body: some View {
            ImageView(
                imageName: model.imageName,
                isLoading: model.isExtracting
            )
            EqualWidthVStack(spacing: 30) {
                ColorSchemeView(
                    isLoading: model.isExtracting,
                    colorScheme: model.scheme,
                    extractCount: Int(model.colorCount)
                )
                .onTapGesture {
                    guard !model.isExtracting else { return }
                    withAnimation { model.isExtracting = true }
                    Task {
                        await model.extractColorScheme()
                        withAnimation { model.isExtracting = false }
                    }
                }
                Slider(value: $model.colorCount, in: 3...10, step: 1)
                    .disabled(model.isExtracting)
            }
        }
    }
}
```

[06:51] These annotations are downstream
[06:53] of the framework’s intended semantics at runtime.
[06:58] SwiftUI’s concurrency annotations express its runtime semantics.
[07:04] This may seem like a subtle distinction
[07:06] from the compile time conveniences we saw earlier,
[07:09] but it is fundamental.
[07:12] We’ll see another example that reinforces this idea coming right up.

[07:21] Allright folks, this next stop is gonna be exciting.
[07:25] Make sure your seat belt is snug, and your electronic devices are secured.

[07:32] As you introduce more app features during app development,
[07:36] if the main thread has too much work to do,
[07:39] the app may start to have frame drops or hitches.
[07:43] You can use tasks and structured concurrency
[07:46] to offload your compute from the main thread.
[07:49] Our session, “Elevate an app with Swift Concurrency,”
[07:53] provides a series of practical techniques for improving your app's performance.
[07:58] Make sure you catch that one.

[08:01] The focus of this tour is how SwiftUI
[08:04] leverages Swift concurrency, to give your apps better performance.

[08:10] In the past, the SwiftUI team has revealed
[08:13] that built-in animations use a background thread
[08:16] to calculate their intermediary states.

[08:21] Let’s review that by investigating this circle inside my SchemeContentView.

### [08:26] Animated circle, part of color scheme view

```swift
// Part of color scheme view

struct SchemeContentView: View {
    let isLoading: Bool
    @State private var pulse: Bool = false

    var body: some View {
        ZStack {
            // Color wheel …

            Circle()
                .scaleEffect(isLoading ? 1.5 : 1)

            VStack {
                Text(isLoading ? "Please wait" : "Extract")

                if !isLoading {
                    Text("^[\\(extractCount) color](inflect: true)")
                }
            }
            .visualEffect { [pulse] content, _ in
                content
                    .blur(radius: pulse ? 2 : 0)
            }
            .onChange(of: isLoading) { _, newValue in
                withAnimation(newValue ? kPulseAnimation : nil) {
                    pulse = newValue
                }
            }
        }
    }
}
```

[08:27] As the color extraction job begins and ends,
[08:30] the circle grows larger, and shrinks back down
[08:33] to its original size with animation.

[08:37] For that, I’m using a scaleEffect that reacts to the property isLoading.

[08:45] Every frame of this animation requires a different scale value between 1 and 1.5.

[08:52] Animated values such as this scale involve complex maths.
[08:57] Calculating a lot of these, frame by frame can be expensive.
[09:01] Therefore, SwiftUI performs this calculation on a background thread,
[09:06] so that the main thread has more capacity for other stuff.

[09:11] This optimization applies to APIs you implement as well.

[09:16] That's right.
[09:18] Sometimes, SwiftUI runs your code off the main thread.
[09:22] But don’t worry, it’s not that complicated.
[09:26] SwiftUI is declarative.
[09:28] Unlike an UIView, the struct that conforms to the View protocol,
[09:32] is not an object that has to occupy a fixed location in memory.

[09:38] At runtime, SwiftUI creates a separate representation for the View.

[09:44] This representation provides opportunities for many types of optimizations.
[09:49] An important one is to evaluate parts of the view representation
[09:53] on a background thread.

[09:56] SwiftUI reserves this technique for occasions
[09:59] where a lot of compute is done on your behalf.
[10:02] For example, most of the time,
[10:05] it involves some high-frequency geometry calculations.
[10:09] The Shape protocol is an example of that.

[10:14] The Shape protocol requires a method that returns a path.
[10:19] I made a custom wedge shape to represent an extracted color in my wheel.
[10:24] It implements that path method.

[10:28] Each wedge has a distinct orientation.
[10:32] While this wedge shape is animating,
[10:34] the path method I wrote gets calls from a background thread.

[10:39] Another kind of custom logic SwiftUI runs on your behalf is a closure argument.

[10:46] In the middle of the circle are these blurred texts.
[10:50] To implement that, I’m using a visualEffect on a SwiftUI Text.

[10:57] It alters the blur radius between two values
[10:59] as the pulse value flips between true and false.
[11:04] The view modifier visualEffect,
[11:06] takes in a closure for defining effects on the subject view, aka the text.
[11:12] Visual effects can get fancy, and expensive to render.
[11:17] So SwiftUI can choose to call this closure from a background thread.

[11:22] So that’s two APIs that could call your code from a background thread.
[11:27] Let's quickly visit a few more.

[11:31] The Layout protocol may call its requirement methods off the main thread.
[11:36] And similar to visualEffect, the first argument of onGeometryChange
[11:41] is a closure that may get called from the background thread as well.

[11:47] This runtime optimization with a background thread
[11:50] has been part of SwiftUI for a long time.
[11:54] SwiftUI can express this runtime behavior, or semantics,
[11:59] to the compiler, and you, with the Sendable annotation.
[12:04] Here again, SwiftUI’s concurrency annotations express its runtime semantics.

[12:13] Running your code on a separate thread
[12:15] frees up the main thread, so that your app is more responsive.
[12:20] And the Sendable keyword
[12:21] is here to remind you about potential data-race conditions
[12:25] when you need to share data from the @MainActor.

[12:30] Think of Sendable like a warning sign on a cliffside trail that reads
[12:34] “Danger! Don’t race here!”
[12:37] Hmm, that description is maybe a little too dramatic.
[12:41] In practice, Swift will reliably find any potential race conditions in code,
[12:47] and remind you of them with compiler errors.
[12:50] The best strategy to avoid data-race conditions,
[12:53] is to not share data between concurrent tasks at all.

[12:58] When a SwiftUI API requires you to write a sendable function,
[13:02] the framework will provide most of the variables you need as function arguments.
[13:07] Here's a quick example.

### [13:10] UI for extracting colors

```swift
// UI for extracting colors

struct ColorScheme: Identifiable, Hashable {
    var id = UUID()
    let imageName: String
    var colors: [Color]
}

@Observable
final class ColorExtractor {
    var imageName: String
    var scheme: ColorScheme?
    var isExtracting: Bool = false
    var colorCount: Float = 5

    func extractColorScheme() async {}
}

struct ColorExtractorView: View {
    @State private var model = ColorExtractor()

    var body: some View {
            ImageView(
                imageName: model.imageName,
                isLoading: model.isExtracting
            )
            EqualWidthVStack {
                ColorSchemeView(
                    isLoading: model.isExtracting,
                    colorScheme: model.scheme,
                    extractCount: Int(model.colorCount)
                )
                .onTapGesture {
                    guard !model.isExtracting else { return }
                    withAnimation { model.isExtracting = true }
                    Task {
                        await model.extractColorScheme()
                        withAnimation { model.isExtracting = false }
                    }
                }
                Slider(value: $model.colorCount, in: 3...10, step: 1)
                    .disabled(model.isExtracting)
            }
        }
    }
}
```

[13:10] Earlier, there’s a detail in ColorExtactorView that I didn’t show.
[13:15] The color wheel and the slider have the same width,
[13:19] thanks to this EqualWidthVStack type.

[13:23] EqualWidthVStack is a custom layout.
[13:27] How it does the layout isn't our focus.
[13:30] The point here is, I’m able to do all these sophisticated calculations
[13:34] with the argument SwiftUI passes in, without touching any external variables.

[13:41] But, what if I really need to access some variables external to a sendable function?
[13:47] In SchemeContentView, I need the state pulse in this visualEffect.
[13:53] But, Swift says there’s a potential data-race condition.

### [13:47] Part of color scheme view

```swift
// Part of color scheme view

struct SchemeContentView: View {
    let isLoading: Bool
    @State private var pulse: Bool = false

    var body: some View {
        ZStack {
            // Color wheel …

            Circle()
                .scaleEffect(isLoading ? 1.5 : 1)

            VStack {
                Text(isLoading ? "Please wait" : "Extract")

                if !isLoading {
                    Text("^[\\(extractCount) color](inflect: true)")
                }
            }
            .visualEffect { [pulse] content, _ in
                content
                    .blur(radius: pulse ? 2 : 0)
            }
            .onChange(of: isLoading) { _, newValue in
                withAnimation(newValue ? kPulseAnimation : nil) {
                    pulse = newValue
                }
            }
        }
    }
}
```

[13:58] Let’s take out our binoculars, and zoom in on what the compiler error is telling us.

[14:04] The pulse variable is short for self.pulse.
[14:09] This is a common scenario when sharing a @MainActor isolated variable
[14:13] in sendable closures.

[14:16] Self is a view.
[14:17] It’s isolated on the main actor.
[14:19] This is our starting point.
[14:22] From there, our end goal is to access the pulse variable
[14:26] in a sendable closure.
[14:28] To achieve that, two things must happen.
[14:32] First, the value self must cross the boundary
[14:35] from main actor to the background threads code region.

[14:40] In Swift, we refer to this as sending the variable self
[14:44] into the background thread.
[14:47] This requires the type of self to be Sendable.

[14:52] Now that self appears in the right place, we want to read its property pulse
[14:56] in this nonisolated region.
[14:59] The compiler will not allow that unless the property pulse
[15:03] is not isolated to any actor.

[15:08] Looking at the code again,
[15:10] because self is a View, it’s protected by the @MainActor.

[15:15] So the compiler considers it Sendable.

[15:18] Because of that, Swift is fine with the fact
[15:21] that this reference to self crosses from its @MainActor isolation
[15:25] into the Sendable closure.

[15:29] So really, Swift is warning us about the attempt to access the pulse property.
[15:35] Of course, we know that as a member of the View,
[15:39] pulse is @MainActor isolated.

[15:42] So the compiler is telling me, even though I can send self in here,
[15:46] accessing is @MainActor isolated property pulse is unsafe.

[15:52] To fix this compile error,
[15:54] I can avoid reading the property through a reference to the View.
[15:59] The visual effect I’m writing, doesn’t need the whole value of this view.
[16:03] It just wants to know if pulse is true or false.
[16:07] I can make a copy of the pulse variable in the closure’s capture list,
[16:11] and refer to the copy instead.
[16:14] This way, I’m no longer sending self into this closure.

[16:19] I’m sending a copy of pulse,
[16:21] which is sendable because Bool is a simple value type.

[16:27] This copy exists only within the scope of this function,
[16:31] so accessing it here does not cause any data-race problems.

[16:37] In that example, we couldn’t access that pulse variable in a sendable closure,
[16:42] because it's protected by a global actor.
[16:45] Another strategy to make this work
[16:47] is to make everything we’re reading nonisolated.

[16:53] All right, folks, you’ve made it to Camp.
[16:56] Let’s sit down and talk about organizing your concurrent code.

[17:01] Experienced SwiftUI developers might have noticed that most SwiftUI's APIs,
[17:07] such as button’s action callback, are synchronous.
[17:11] To call your concurrent code,
[17:13] you first need to switch to an async context with a Task.

### [17:42] UI for extracting colors

```swift
// UI for extracting colors

struct ColorScheme: Identifiable, Hashable {
    var id = UUID()
    let imageName: String
    var colors: [Color]
}

@Observable
final class ColorExtractor {
    var imageName: String
    var scheme: ColorScheme?
    var isExtracting: Bool = false
    var colorCount: Float = 5

    func extractColorScheme() async {}
}

struct ColorExtractorView: View {
    @State private var model = ColorExtractor()

    var body: some View {
            ImageView(
                imageName: model.imageName,
                isLoading: model.isExtracting
            )
            EqualWidthVStack {
                ColorSchemeView(
                    isLoading: model.isExtracting,
                    colorScheme: model.scheme,
                    extractCount: Int(model.colorCount)
                )
                .onTapGesture {
                    guard !model.isExtracting else { return }
                    withAnimation { model.isExtracting = true }
                    Task {
                        await model.extractColorScheme()
                        withAnimation { model.isExtracting = false }
                    }
                }
                Slider(value: $model.colorCount, in: 3...10, step: 1)
                    .disabled(model.isExtracting)
            }
        }
    }
}
```

[17:18] But why doesn’t Button accept an async closure instead?
[17:23] Synchronous updates are important for a good user experience.
[17:28] It’s extra important if your app has long-running tasks,
[17:31] and people have to wait for the results.

[17:36] Before kicking off a long-running task with an async function,
[17:40] it’s important to update your UI to indicate the task is in progress.
[17:45] This update should be synchronous,
[17:48] especially if it needs to trigger some time-sensitive animation.

[17:54] Imagine if I ask a language model to help me extract the colors.
[17:58] That extraction process will take a while.
[18:02] So in my app, I'm using withAnimation
[18:05] to synchronously trigger various loading states.
[18:09] When the task is done, I then reverse these loading states,
[18:13] by another synchronous state change.

[18:16] SwiftUI’s action callbacks accept synchronous closures,
[18:20] which are necessary to set up UI updates, like my loading states.
[18:25] Async functions, on the other hand, require extra consideration,
[18:30] especially if you’re working with animations.
[18:33] Let's explore that now.

[18:37] In my app, I can scroll up
[18:39] to reveal a history of the color schemes from earlier.
[18:42] As each scheme appears on screen,
[18:45] I want its colors to reveal themselves with some animation.
[18:50] The view modifier onScrollVisibilityChange
[18:53] gives me the event when the color scheme appears on screen.
[18:57] As soon as this happens, I’m setting a state variable to true
[19:01] to trigger the animation,
[19:03] which causes each color’s Y offset to update with animation.

### [18:55] Animate colors as they appear by scrolling

```swift
// Animate colors as they appear by scrolling

struct SchemeHistoryItemView: View {
    let scheme: ColorScheme
    @State private var isShown: Bool = false

    var body: some View {
        HStack(spacing: 0) {
            ForEach(scheme.colors) { color in
                color
                    .offset(x: 0, y: isShown ? 0 : 60)
            }
        }
        .onScrollVisibilityChange(threshold: 0.9) {
            guard !isShown else { return }
            withAnimation {
                isShown = $0
            }
        }
    }
}
```

[19:09] As an UI framework, in order to create buttery smooth interactions every frame,
[19:15] SwiftUI needs to confront the reality
[19:18] that devices demand a certain screen refresh rate.

[19:23] That’s some important context when I want my code to react
[19:26] to a continuous gesture like scrolling.
[19:29] Let's put this code on the timeline.

[19:33] I’m going to use this green triangle
[19:35] to mark the moment SwiftUI calls onScrollVisibilityChange.
[19:40] And the blue circle marks the moment
[19:42] I trigger my animation with a state mutation.

[19:47] With this setup,
[19:48] whether such mutation occurs on the same frame with the gesture callback
[19:52] can make a big difference visually.

[19:58] Suppose I want to add some async work prior to my animated mutation.
[20:03] I’ll mark the moment the async work starts with an orange line and await on it.
[20:09] In Swift, awaiting on an async function creates a suspension point.

[20:16] A Task accepts an async function as an argument.

[20:21] When the compiler sees an await, it splits the async function into two parts.

[20:28] After executing part one,
[20:31] the Swift runtime can pause this function and do some other work on the CPU.
[20:37] This can go on for an arbitrary amount of time.
[20:40] Then the runtime resumes on the original async function
[20:44] and execute its second half.

[20:48] This process can repeat for each occurrence of await in the function.

[20:56] Going back to our timeline,
[20:58] this suspension could mean my task closure doesn’t resume until much later,
[21:05] passing the refresh deadline dictated by the device.

[21:09] To the user, that means my animation looks laggy and out of step.
[21:14] So a mutation in an async function may not help achieving your goal.

[21:20] SwiftUI provides synchronous callbacks by default.
[21:24] This helps avoid unintentional suspension of async code.
[21:28] Updating UI within synchronous action closures is easy to do correctly.
[21:33] You always have the option to use a Task to opt in into an asynchronous context.

[21:41] Time-sensitive logic like animation
[21:43] requires SwiftUI’s input and output to be synchronous.
[21:48] Synchronous mutations of observable properties,
[21:51] and synchronous callbacks,
[21:52] are the most natural types of interaction with the framework.
[21:57] A great user experience doesn’t have to involve a lot of custom concurrent logic.
[22:02] Synchronous code is a great starting point and endpoint for lots of apps.

[22:09] On the other hand, if your app does a lot of concurrent work,
[22:13] try and find the boundaries between your UI code and non-UI code.
[22:18] It’s best to separate the logic for async work from your view logic.

[22:24] You can use a piece of state as a bridge.
[22:27] The state decouples the UI code from the async code.

[22:32] It can initiate the async tasks.

[22:37] As some async work finishes up, perform a synchronous mutation on the state,
[22:43] so that your UI can update as reactions to this change.
[22:47] This way, the UI logic is mostly synchronous.

[22:52] As a bonus, you’ll find it easier to write tests for your async code,
[22:57] because it’s now independent from the UI logic.

[23:02] Your view can still use a Task to switch to an async context.

[23:07] But try to keep the code in this async context simple.
[23:11] It’s there to inform the model about a UI event.
[23:15] Finding the boundaries between UI code
[23:18] that requires a lot of time-sensitive changes,
[23:21] and long-running async logic is a great way to improve the structure of an app.
[23:27] It can help you keep the views synchronous and responsive.
[23:31] It’s also important to organize the non-UI code well.
[23:35] You’ll have greater freedom to do so with the tips I showed you in this basecamp.

[23:42] Swift 6.2 comes with a great default actor isolation setting.
[23:47] If you have an existing app, try it out.
[23:50] You’ll be able to delete most of your @MainActor annotations.

[23:55] Mutex is an important tool for making a class sendable.
[23:59] Check out its official documentation to learn how.

[24:04] Challenge yourself to write some unit tests for the async code in your app.
[24:09] See if you can do it without importing SwiftUI.

[24:13] Alright, folks.
[24:15] So that’s how SwiftUI leverages Swift concurrency
[24:19] to help you build fast and data-race free apps.
[24:23] As we wrap up this tour,
[24:25] I hope you’ve gained a solid mental model for concurrency in SwiftUI.

[24:37] Thanks for touring, I wish you many epic adventures.
