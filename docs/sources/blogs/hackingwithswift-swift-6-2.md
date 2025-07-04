---
title: What's new in Swift 6.2?
source: https://www.hackingwithswift.com/articles/277/whats-new-in-swift-6-2
date_crawled: '2025-07-03'
type: article
topics:
- actors
- async-await
- concurrency
- data-race-safety
- sendable
- swift6
- tasks
---

```markdown
# What's new in Swift 6.2?

Raw identifiers, backtraces, task naming, and more.

Paul Hudson · May 10th 2025 · @twostraws

Brace yourselves, folks: Swift 6.2 contains another gigantic collection of additions and improvements to the language, while also adding some important refinements to Swift concurrency that ought to make it much easier to adopt everywhere.

Many changes are small, such as the addition of raw identifiers, default values in string interpolation, or `enumerated()` conforming to `Collection`, but these are all likely to spread quickly across projects because they are just so darned *useful*.

It's also great to see Swift Testing going from strength to strength, with three major improvements coming in Swift 6.2, including exit tests and attachments.

In short, it feels like Swift 6.2 is delivering what many imagined Swift 6.0 would be – increasingly rounded support for concurrency, backed up by a number of pragmatic choices that help smooth out the language's learning curve.

**Note:** At the time of writing, Swift 6.2 is available only as a test release from [Swift.org](https://www.swift.org/install/macos/). The list below represents my best guess for what's coming up – don't be surprised if something slips to a later or release or something else arrives by surprise!

### Control default actor isolation inference

[SE-0466](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md) introduces the ability for code to opt into running on a single actor by default – to effectively go back to being a single-threaded program, where most code runs on the main actor until you say otherwise.

**Yes, this is exactly as good as you're thinking:** with one single change many app developers can more or less avoid thinking about Swift concurrency until they are ready to do so, because unless they say otherwise all their types and functions will behave as if it were annotated with `@MainActor`.

To enable this new feature, add `-default-isolation MainActor` to your compiler flags, and code like this becomes valid:

```swift
@MainActor
class DataController {
    func load() { }
    func save() { }
}

struct App {
    let controller = DataController()

    init() {
        controller.load()
    }
}
```

As you can see, the `App` struct creates and uses a main actor-isolated type without itself being marked `@MainActor`, but that's okay because it's automatically applied for us – we could even remove the lone `@MainActor` annotation and it would still apply.

Before you start panicking that this is going to cause all sorts of concurrency problems, there are five important things you know.

First, this new configuration option is applied on a *per-module basis*, so if you bring in external modules they can still run on other actors. This ought to allow UI-focused modules to switch to running on the main actor by default, while letting background-focused modules operate with concurrency as before.

Second, you can still use things like networking in your apps just fine – code such as `URLSession.shared.data(from:)` will run on its own task rather than blocking your code.

Third, a single CPU core in a modern iPhone runs at over 4GHz, so a huge number of iOS apps can get all their work done serially without a second thought.

Fourth, a lot of developers were already using "make it all @MainActor" as their default approach to concurrency, changing only when needed.

Fifth and perhaps most importantly, this change along with others form part of a larger [Improving the approachability of data-race safety](https://github.com/swiftlang/swift-evolution/blob/main/visions/approachable-concurrency.md) vision document published by the Swift team – it's not just one change in isolation, but instead part of a cohesive package of improvements to reduce the learning curve for concurrency.

So, although this change might seem antithetical to all the Swift concurrency work that has taken place from Swift 5.5 and on, ultimately it solves a significant problem that was only growing: Swift concurrency is not easy to learn, and many apps simply don't need it.

Of course, the real question is whether Apple will enable this feature by default for new app projects in Xcode. I sincerely hope so, because it would also allow Xcode to default to the Swift 6 language version without introducing errors and warnings that many developers just don't need to think about.

**Note:** Another Swift Evolution proposal, [SE-0478](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0478-default-isolation-typealias.md), is currently being discussed, and if it is approved would allow us to declare the default actor isolation on a per-file basis using syntax like `private typealias DefaultIsolation = MainActor`. The feedback so far has been broadly negative, so it might be returned for revision.

### Raw identifiers

[SE-0451](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0451-escaped-identifiers.md) dramatically expands the range of characters we can use to create identifiers – the names of variables, functions, enum cases and similar – so we can name them pretty much however we want when placed inside backticks.

So, this kind of code is legal in Swift 6.2 and later:

```swift
func `function name with spaces`() {
    print("Hello, world!")
}

`function name with spaces`()
```

If you're wondering why such naming might be useful, consider this:

```swift
enum HTTPError: String {
    case `401` = "Unauthorized"
    case `404` = "Not Found"
    case `500` = "Internal Server Error"
    case `502` = "Bad Gateway"
}
```

That makes each HTTP error code a case in our enum, which would previously need to be written as something else such as `case _401` or `case error401`.

If you're using numbers like this, you either need to qualify the type each time you use it, to avoid Swift getting confused, or you need to place the backticks carefully.

For example, in the code below we use `HTTPError` each time, to avoid Swift thinking `401` refers to a malformed floating-point literal:

```swift
let error = HTTPError.401

switch error {
case HTTPError.401, HTTPError.404:
    print("Client error: \(error.rawValue)")
default:
    print("Server error: \(error.rawValue)")
}
```

The alternative is to wrap the numbers themselves in the backticks – *not* including the dot beforehand – like this:

```swift
switch error {
case .`401`, .`404`:
    print("Client error: \(error.rawValue)")
default:
    print("Server error: \(error.rawValue)")
}
```

The biggest benefactor of this change is likely to be Swift Testing, where test names can now directly be written in a human-readable form rather than using camel case and adding an extra string description above.

So, rather than writing this:

```swift
import Testing

@Test("Strip HTML tags from string")
func stripHTMLTagsFromString() {
    // test code
}
```

We can instead write this:

```swift
@Test
func `Strip HTML tags from string`() {
    // test code
}
```

It's less duplication, which is always welcome.

One small detail that might catch you out is this: "A raw identifier may start with, contain, or end with operator characters, but it may not contain only operator characters." So, you can put operators such as `+` and `-` into your identifier names, but only if they aren't the only things in there.

### Default Value in String Interpolations

[SE-0477](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0477-default-interpolation-values.md) makes a small but beautiful change to string interpolation with optionals, allowing us to provide an additional `default` value to use if the optional is nil.

In its simplest form this means we would write the following code:

```swift
var name: String? = nil
print("Hello, \(name, default: "Anonymous")!")
```

Instead of this:

```swift
print("Hello, \(name ?? "Anonymous")!")
```

At first glance this might not seem like a great improvement, but the kicker is that nil coalescing doesn't work with different types. So, this kind of code is allowed:

```swift
var age: Int? = nil
print("Age: \(age ?? 0)")
```

But this kind of code will not compile when uncommented:

```swift
// print("Age: \(age ?? "Unknown")")
```

That attempts to mix an optional integer with a string default value, which isn't allowed. Fortunately this *is* possible from Swift 6.2 onwards:

```swift
print("Age: \(age, default: "Unknown")")
```

### Add Collection conformances for enumerated()

[SE-0459](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0459-enumerated-collection.md) makes the type returned by `enumerated()` conform to `Collection`.

The most immediate benefit of this is that it's now much easier to use `enumerated()` with a SwiftUI `List` or `ForEach` like this:

```swift
import SwiftUI

struct ContentView: View {
    var names = ["Bernard", "Laverne", "Hoagie"]

    var body: some View {
        List(names.enumerated(), id: \.offset) { values in
            Text("User \(values.offset + 1): \(values.element)")
        }
    }
}
```

The [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0459-enumerated-collection.md) also mentions various performance benefits, including making `(1000..<2000).enumerated().dropFirst(500)` a constant-time operation.

### Method and Initializer Key Paths

[SE-0479](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0479-method-and-initializer-keypaths.md) extends Swift's key paths to support methods alongside the existing support for properties and subscripts, which, along with [SE-0438](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0438-metatype-keypath.md) introduced in Swift 6.1, promises to round out what key paths can do.

Code to access properties has always worked just fine with key paths:

```swift
let strings = ["Hello", "world"]
let capitalized = strings.map(\.capitalized)
print(capitalized)
```

With this change we can now access methods too, but be sure to actually *invoke* the method like this:

```swift
let uppercased = strings.map(\.uppercased())
print(uppercased)
```

If you *don't* invoke the method then you get back an uninvoked function that you can call later on like this:

```swift
let functions = strings.map(\.uppercased)
print(functions)

for function in functions {
    print(function())
}
```

In that code, the `functions` constant contains an array of calls to `uppercased()` on each string we passed in – `functions[0]` would be a reference to `"HELLO".uppercased()`, which we could call directly using `functions[0]()`.

If two methods have the same name, you can add their argument labels to clarify which overload you mean, like this:

```swift
let prefixUpTo = \Array<String>.prefix(upTo:)
let prefixThrough = \Array<String>.prefix(through:)
```

However, you *can't* make key paths to methods that are marked either `async` or `throws`; it's just not supported.

### Opt-in Strict Memory Safety Checking

[SE-0458](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0458-strict-memory-safety.md) introduces opt-in support for flagging unsafe Swift code as warnings unless specifically desired, which will make it significantly easier to audit unsafe code usage.

**Note:** To be clear, *unsafe* code is not the same as *crashing* code – things like force unwraps or reading index -1 in an array will both crash your code but are considered safe because that's expected behavior. *Unsafe* code is code where you bypass Swift's guardrails to poke around in memory in such a way to cause undefined behavior, and usually if not always includes the word "unsafe" somewhere in the name, e.g. `UnsafeRawPointer` or `unsafelyUnwrapped`.

Strict memory safety checking introduces new `@safe` and `@unsafe` attributes that mark code as safe or unsafe to use respectively, with `@safe` being the default – it's only required when you need to override `@unsafe` in specific circumstances.

When strict memory safety is enabled, and code marked `@unsafe` must be called with a new `unsafe` keyword, like this:

```swift
let name: String?
unsafe print(name.unsafelyUnwrapped)
```

Failing to use `unsafe` will throw up a warning, so you can either adjust the code to use a safe variant or add the `unsafe` key to acknowledge that the code is unsafe.

This is very similar to the way both `try` and `await` work – the compiler knows that certain code will throw, that certain other code is asynchronous, or that certain other code is marked `@unsafe`, so really these keywords are acknowledgements for other people to see.

### Swift Backtrace API

[SE-0419](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0419-backtrace-api.md) introduces a new `Backtrace` struct, which is capable of capturing data about the call stack of our app at any given moment – the exact sequence of function calls leading up to the current point.

By default backtraces are not symbolicated, which means they won't include the names of each function in the call stack, but you can use `symbolicated()` to get that extra data.

So, as an example we could write a small chain of functions where the last one prints a backtrace:

```swift
import Runtime

func functionA() {
    functionB()
}

func functionB() {
    functionC()
}

func functionC() {
    if let frames = try? Backtrace.capture().symbolicated()?.frames {
        print(frames)
    } else {
        print("Failed to get backtrace.")
    }
}

functionA()
```

That will print exactly which functions were on the call stack – `functionC()`, `functionB()`, and `functionA()` – along with the files and line numbers of each call, which is really helpful for debugging.

### weak let

[SE-0481](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0481-weak-let.md) introduces the ability to use `weak let` when declaring properties of a type, complementing the existing support for `weak var`.

**Important:** `weak let` means that a property cannot be changed after creation, but it can still be *destroyed*, so you need to use it carefully.

As an example, we could create two classes like this:

```swift
final class User: Sendable {
    let id = UUID()
}

final class Session: Sendable {
    weak let user: User?

    init(user: User?) {
        self.user = user
    }
}
```

We could then make and use them like so:

```swift
var user: User? = User()
let session = Session(user: user)
print(session.user?.id ?? "No ID")
```

Because the `user` property has a `weak` reference to a class, we can destroy the original and have the property be destroyed too. So, this will print "No ID":

```swift
user = nil
print(session.user?.id ?? "No ID")
```

What we *can't* do is *reassign* the `user` property, which means both of these two would fail to compile if uncommented:

```swift
// session.user? = User()
// session.user = nil
```

Another big advantage of `weak let` can also be seen in the code above: we can mark both those classes as conforming to `Sendable`, which would not have been possible using `weak var`.

### Transactional Observation of Values

[SE-0475](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0475-observed.md) creates a new `Observations` struct that is created with a closure, and provides an `AsyncSequence` that emits new values whenever any any `@Observable` data changes – it effectively gives us the same power to monitor changes that SwiftUI gets, just in a free-form way.

As an example, we could make a trivial `@Observable` class for a player with a score:

```swift
@Observable
class Player {
    var score = 0
}

let player1 = Player()
```

We can ask to be notified when that score changes using `Observations` like this:

```swift
let playerScores = Observations { player1.score }
```

In that code, `playerScores` is an instance of `Observations<Int, Never>`, meaning that it emits integers and will never throw errors.

We can then queue up a bunch of example changes, and watch for those happening with a `for await` loop:

```swift
for i in 1...5 {
    Task {
        try? await Task.sleep(for: .seconds(i))
        player1.score += 1
    }
}

for await score in playerScores {
    print(score)
}
```

That will print six values in total: the initial score, plus increments through 5.

There are a handful of important usage notes you should be aware of when using `Observations`:

1.  It will emit the initial value as well as all future values.
2.  If multiple changes come in at the same time, they might be coalesced into a single value being emitted. For example, if our `Task` code incremented `score` twice, the values emitted would go up in 2s.
3.  The `AsyncSequence` of values being emitted can potentially run forever, so you should put it on a separate task or otherwise handle it carefully.
4.  If you want iteration to stop – to end the loop – you should make the value being observed optional, then set it to nil.

### Global-actor isolated conformances

[SE-0470](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0470-isolated-conformances.md) resolves a small but important concurrency problem by making it possible to restrict a protocol conformance to a specific global actor.

For example, we can now say "this `@MainActor`-restricted type conforms to `Equatable` only when it's being used on the main actor, like this:

```swift
@MainActor
class User: @MainActor Equatable {
    var id: UUID
    var name: String

    init(name: String) {
        self.id = UUID()
        self.name = name
    }

    static func ==(lhs: User, rhs: User) -> Bool {
        lhs.id == rhs.id
    }
}
```

Notice the use of `@MainActor Equatable` – if we had tried to conform without using `@MainActor` on the protocol, Swift would be free to run the `==` method on any task, including in the background, which is explicitly disallowed thanks to the whole type being marked `@MainActor`. As a result, our code would not build.

### Starting tasks synchronously from caller context

[SE-0472](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0472-task-start-synchronously-on-caller-context.md) introduces a new way to create tasks so they start immediately if possible, rather than the existing behavior that only allows tasks to be queued to run at the next opportunity.

You can see the difference with code like this:

```swift
print("Starting")

Task {
    print("In Task")
}

Task.immediate {
    print("In Immediate Task")
}

print("Done")
try await Task.sleep(for: .seconds(0.1))
```

That creates two unstructured tasks: a regular unstructured task followed by an immediate unstructured task. When it runs, it will print Starting, In Immediate Task, Done, and then finally In Task.

To really understand the distinction between immediate tasks and regular tasks, remember that all potential suspension points in Swift must be marked with `await`. Creating a regular, non-immediate task doesn't use `await` because it doesn't mark a suspension point, but it *doesn't* run immediately because it gets queued up to run at the next available opportunity.

The new ability to create *immediate* tasks unlocks important new functionality: the code in an immediate task starts executing immediately if it's already on the target executor, perhaps providing important data that a UI control is waiting for, but after that initial immediate response the task can then use `await` like a regular task and potentially trigger suspension as normal. So, everything in an immediate tasks runs straight away until the first suspension point is reached.

Both `Task` and `Task.immediate` are *unstructured* tasks, however task groups have also been upgraded to support immediate child tasks with `addImmediateTask()` and `addImmediateTaskUnlessCancelled()`.

### Run nonisolated async functions on the caller's actor by default

[SE-0461](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0461-async-function-isolation.md) adjusts the way nonisolated async functions are called so that they run on the same actor as their caller. This sounds like a really abstract change, but it is important so I would recommend you spend the time to understand what's changing and why.

As an example, here's a simple struct that knows how to download and decode an array of `Double` values that represents various temperatures:

```swift
struct Measurements {
    func fetchLatest() async throws -> [Double] {
        let url = URL(string: "https://hws.dev/readings.json")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode([Double].self, from: data)
    }
}
```

That isn't isolated to any particular actor, so it can run its code anywhere.

Next, we could use that with another struct called `WeatherStation`, which will download all the readings and return their mean average. This time, though we'll mark the struct as being isolated to the main actor:

```swift
@MainActor
struct WeatherStation {
    let measurements = Measurements()

    func getAverageTemperature() async throws -> Double {
        let readings = try await measurements.fetchLatest()
        let average = readings.reduce(0, +) / Double(readings.count)
        return average
    }
}

let station = WeatherStation()
try await print(station.getAverageTemperature())
```

So, we have one struct that is nonisolated, and another that *is* isolated, and this demonstrates the change perfectly: before Swift 6.2 the call to `measurements.fetchLatest()` will not run on the main actor, but from Swift 6.2 and later it *will*.

The old behavior caused some confusion, not least because `measurements` is a main actor-isolated property in `WeatherStation`, and the call to `measurements.fetchLatest()` takes place in the main actor-isolated `getAverageTemperature()` method.

That old behavior wasn't an accident – [SE-0338](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0338-clarify-execution-non-actor-async.md) from Swift 5.7 specifically states that async functions that aren't isolated to a particular actor "do not run on any actor's executor."

The new behavior introduced by SE-0461 means that nonisolated async functions will now run on the same actor as their caller unless you say otherwise. In the code above, that means the call to `measurements.fetchLatest()` will run on the main actor because `getAverageTemperature()` does.

If you want the old behavior to return – if you wanted `fetchLatest()` to switch away from the caller's actor automatically – you would need to mark it with the new `@concurrent` attribute, like this: `@concurrent func fetchLatest()…`.

### Isolated synchronous deinit

[SE-0371](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0371-isolated-synchronous-deinit.md) introduces the ability to mark the deinitializers of actor-isolated classes as being isolated, which allows them to safely access data elsewhere in the class.

For example, this class is isolated to the main actor, and I've marked its `deinit` as being isolated so that it can safely call `cleanUp()`:

```swift
@MainActor
class DataController {
    func cleanUp() {
        // free up memory
    }

    isolated deinit {
        cleanUp()
    }
}
```

Without that `isolated` keyword in there, the deinitializer wouldn't be isolated to the main actor – that's just not how global actors work. *With* it there, your code will move to the actor's executor before running the code, so it's all safe.

This will be particularly useful for times when your deinitializer needs to access non-`Sendable` state belonging to a class. For example, we might have a `User` class like this one:

```swift
class User {
    var isLoggedIn = false
}
```

We can then wrap that in a `Session` class that runs on the main actor, which automatically marks the user being logged in or out as the session is created and destroyed:

```swift
@MainActor
class Session {
    let user: User

    init(user: User) {
        self.user = user
        user.isLoggedIn = true
    }

    isolated deinit {
        user.isLoggedIn = false
    }
}
```

Again, that `isolated` keyword is required to make the code work – without that the deinitializer would run without being isolated to the main actor, but it would try to access the `user` property that *is* isolated to the main actor, causing a compile error.

### Task Priority Escalation APIs

[SE-0462](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0462-task-priority-escalation-apis.md) introduces the ability for tasks to detect when their priority has been escalated, and also for us to manually escalate task priority if needed.

To watch for priority escalation, use the `withTaskPriorityEscalationHandler()` function like this:

```swift
let newsFetcher = Task(priority: .medium) {
    try await withTaskPriorityEscalationHandler {
        let url = URL(string: "https://hws.dev/messages.json")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return data
    } onPriorityEscalated: { oldPriority, newPriority in
        print("Priority has been escalated to \(newPriority)")
    }
}
```

As you can see, that gives us both the old and new task priorities, and it's up to us to respond to the change however we want. If you want to use that opportunity to escalate the priority of other tasks, you should use the new `escalatePriority(to:)` method like this:

```swift
newsFetcher.escalatePriority(to: .high)
```

Because there are several task priorities available to us, it's possible your `onPriorityEscalated` code will be triggered multiple times – your priority might start at low then move to medium, then move to high, for example. However, task priority can only ever be *raised*, never lowered.

**Note:** Task priority escalation usually happens automatically, such as when a high-priority task finds itself waiting on the result of a low-priority task – Swift will automatically raise the priority of the low-priority task so it’s able to complete faster. Although this API gives us extra control, it's still best to let priority escalation happen automatically where possible.

### Task Naming

[SE-0469](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0469-task-names.md) introduces a useful change to the way we create tasks and child tasks: we can now give them *names*, which is ideal for debugging when one particular task goes rogue.

The API here is simple: when using `Task.init()` and `Task.detached()` to create new tasks, or using `addTask()` and `addTaskUnlessCancelled()` to create child tasks in a task group, you can now pass an optional `name` parameter string to identify the task uniquely. These name strings can be hard-coded or use string interpolation; either one works.

In its simplest form, the new API looks like this:

```swift
let task = Task(name: "MyTask") {
    print("Current task name: \(Task.name ?? "Unknown")")
}
```

To show you a more real-world example, we might have a `NewsStory` struct that knows how to load some basic information about a news article:

```swift
struct NewsStory: Decodable, Identifiable {
    let id: Int
    let title: String
    let strap: String
    let url: URL
}
```

Now we could use a task group to fetch several news story sources and combine them into a single array, while also printing a log message if any child task hits a problem:

```swift
let stories = await withTaskGroup { group in
    for i in 1...5 {
        // Give each child task a unique name
        // for easier identification.
        group.addTask(name: "Stories \(i)") {
            do {
                let url = URL(string: "https://hws.dev/news-\(i).json")!
                let (data, _) = try await URLSession.shared.data(from: url)
                return try JSONDecoder().decode([NewsStory].self, from: data)
            } catch {
                // This child failed – print a log
                // message with its name then return
                // an empty array.
                print("Loading \(Task.name ?? "Unknown") failed.")
                return []
            }
        }
    }

    var allStories = [NewsStory]()

    for await stories in group {
        allStories.append(contentsOf: stories)
    }

    return allStories.sorted { $0.id > $1.id }
}

print(stories)
```

### InlineArray, a fixed-size array

[SE-0453](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0453-vector.md) introduces a new array type called `InlineArray` that stores an exact number of elements, combining the fixed-size nature of tuples with the natural subscripting of arrays, while adding in some welcome performance improvements at the same time.

Creating an `InlineArray` can be done with an explicit size or type, or you can let type inference figure out both by the usage. This is made possible by a separate Swift 6.2 improvement, [SE-0452](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0452-integer-generic-parameters.md), which adds integer generic parameters.

So, we can create an inline array of names by specifying both the size and element type:

```swift
var names1: InlineArray<4, String> = ["Moon", "Mercury", "Mars", "Tuxedo Mask"]
```

Or you can let Swift figure it out by passing in exactly four strings:

```swift
var names2: InlineArray = ["Moon", "Mercury", "Mars", "Tuxedo Mask"]
```

Either way, these arrays are fixed in size, so they don't have `append()` or remove(at:)` methods. However, you *can* still read and write values at a specific index, like this:

```swift
names1[2] = "Jupiter"
```

`InlineArray` does *not* conform to either `Sequence` or `Collection`, so if you want to loop over their values you should use the `indices` property along with subscripting like this:

```swift
for i in names1.indices {
    print("Hello, \(names1[i])!")
}
```

**Note:** Another Swift Evolution proposal, [SE-0483](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0483-inline-array-sugar.md), is currently being discussed, and if it is approved would add an `InlineArray` literal syntax in the style `var names: [5 x String] = .init(repeating: "Anonymous")` to mean "exactly five strings in this array." The feedback so far has been broadly negative, so it might be returned for revision.

### Regex lookbehind assertions

[SE-0448](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0448-regex-lookbehind-assertions.md) expands Swift's regular expression support to include *lookbehind assertions*, which allow us to check if a specific pattern appears immediately before the current position in the string, *without* including it in the matched text.

For example, we might want to match all prices inside a string by looking for any numbers that come after a dollar sign, *without* matching the dollar sign itself:

```swift
let string = "Buying a jacket costs $100, and buying shoes costs $59.99."
let regex = /(?<=\$)\d+(?:\.\d{2})?/

for match in string.matches(of: regex) {
    print(match.output)
}
```

Swift's regular expression system is remarkably powerful, and it's great to see it continue to evolve. Maybe `?R` recursion will come next…

### Swift Testing: Exit Tests

[ST-0008](https://github.com/swiftlang/swift-evolution/blob/main/proposals/testing/0008-exit-tests.md) introduces a testing feature that has been in demand for as long as I can remember: the ability to test code that results in a critical failure that terminated the app.

For example, code like this is going to fail *hard* if we call it with a `sides` value of 0:

```swift
struct Dice {
    func roll(sides: Int) -> Int {
        precondition(sides > 0)
        return Int.random(in: 1...sides)
    }
}
```

Running `roll(sides: 0)` will literally crash the app, which in turn will cause tests to collapse around it. 

From Swift 6.2 and later we can use `#expect(processExitsWith:)` to look for and catch such critical failures, allowing us to check they happened rather than causing our test run to fail.

Here's how it looks in code:

```swift
@Test func invalidDiceRollsFail() async throws {
    let dice = Dice()

    await #expect
