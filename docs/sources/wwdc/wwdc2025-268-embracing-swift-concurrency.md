---
session: 268
year: 2025
title: Embracing Swift concurrency
presenters: []
duration: 28
---

# About

Join us to learn the core Swift concurrency concepts. Concurrency helps you improve app responsiveness and performance, and Swift is designed to make asynchronous and concurrent code easier to write correctly. We'll cover the steps you need to take an app through from single-threaded to concurrent. We'll also help you determine how and when to make the best use of Swift concurrency features – whether it's making your code more asynchronous, moving it to the background, or sharing data across concurrent tasks.

## Chapters

*   [00:00] - Introduction
*   [03:17] - Single-threaded code
*   [06:00] - Asynchronous tasks
*   [07:24] - Interleaving
*   [10:22] - Introducing concurrency
*   [11:07] - Concurrent functions
*   [13:10] - Nonisolated code
*   [14:13] - Concurrent thread pool
*   [14:58] - Sharing data
*   [15:49] - Value types
*   [17:16] - Actor-isolated types
*   [18:30] - Classes
*   [23:18] - Actors
*   [26:12] - Wrap-up

# Summary

*   [00:00] - Introduction
    Swift concurrency enables apps to perform multiple tasks simultaneously, improving responsiveness and offloading computation to the background. Swift's concurrency model makes concurrent code easier to write correctly by making the introduction of concurrency explicit, identifying data that is shared across concurrent tasks, and identifying potential data races at compile-time.

    Apps start by running all code on the main thread. As complexity increases, asynchronous tasks can be introduced for high-latency operations like network access. Background threads can be used for more computationally intensive tasks. Swift provides tools like actors and tasks to express these concurrent operations.
*   [03:17] - Single-threaded code
    In Swift, single-threaded code runs on the main thread, which is isolated to the main actor. There is no concurrency on the main actor because there is only one main thread that can run it. Data or code can be specified on the main actor using the @MainActor notation.

    Swift will ensure that main-actor code only ever runs on the main thread, and main-actor data is only ever accessed from there. We say that such code is isolated to the main actor. By default, Swift protects main thread code using the main actor, ensuring shared state can be accessed freely.

    Protecting code with the main actor by default is driven by a build setting. Use this primarily for your main app module and any modules that are focused on UI interactions.
*   [06:00] - Asynchronous tasks
    Swift concurrency uses async and await to make functions non-blocking, allowing other work to run while waiting for data like network requests. This prevents hangs and improves UI responsiveness by breaking functions into parts that run before and after the awaited event.
*   [07:24] - Interleaving
    Asynchronous functions run in a task, executing independently of other tasks. A single thread can alternate between running independent tasks as they become ready, using 'interleaving'. This improves performance by avoiding idle time and makes efficient use of system resources.

    Multiple asynchronous tasks are effective when performing many independent operations at the same time. When performing work in a specific order, use a single task.

    Using asynchronous tasks in a single thread is often sufficient. If the main thread becomes too burdened, profiling tools such as Instruments can help identify bottlenecks for optimization before introducing concurrency.
*   [10:22] - Introducing concurrency
    Concurrency allows parts of code to run on a background thread in parallel with the main thread, getting work done faster by using more of the CPU cores in your system. To improve performance, the example introduces concurrency to run code on background threads, freeing up the main thread.
*   [11:07] - Concurrent functions
    By applying the @concurrent attribute, Swift is instructed to run a function in the background. The Swift compiler highlights data access on the main actor to safely introduce concurrency.

    One best practice, to ensure work happens synchronously, is to move the main actor code into a caller that always runs on the main thread.
*   [13:10] - Nonisolated code
    An @concurrent function will always switch off of an actor to execute. The 'nonisolated' keyword allows clients to choose where to run code — main or background. For general-purpose libraries, it is recommended to provide a nonisolated API and let clients decide whether they want to offload work.

    For more concurrency options, see "Beyond the basics of structured concurrency" from WWDC23.
*   [14:13] - Concurrent thread pool
    When offloading work to the background, the system manages scheduling the work on threads in a concurrent thread pool. Smaller devices may have fewer threads in the pool, while larger systems with more cores will have more. Tasks are assigned to available threads in the pool, which may change as tasks suspend and resume, optimizing resource usage.
*   [14:58] - Sharing data
    When working with concurrency and sharing data between different threads, there is a risk of introducing runtime bugs due to accessing shared mutable state. Swift's design helps mitigate this issue by providing compile-time checks, enabling developers to write concurrent code more confidently.
*   [15:49] - Value types
    The use of value types provides a significant advantage when dealing with concurrent tasks. When a value type is copied into a background thread, it creates an independent copy, ensuring that any changes made on the main thread do not impact the background thread's value. This independence makes value types safe to share between threads.

    Value types that conform to the 'Sendable' protocol are always safe to share concurrently. Main actor types are implicitly Sendable.
*   [17:16] - Actor-isolated types
    Swift actors safeguard non-Sendable state by ensuring single-task access. When values are sent to and from actors, the Swift compiler verifies safety.
*   [18:30] - Classes
    In Swift, classes are reference types, meaning changes to an object through one variable are visible through all variables pointing to that object.

    When multiple threads access and modify the same non-Sendable object concurrently, it can result in data races, crashes, or glitches. Swift's concurrency system prevents this at compile-time by enforcing that only Sendable types are shared between actors and tasks.

    To avoid data races, it is crucial to ensure that mutable objects are not shared concurrently. Complete modifications to objects before sending them to another task or actor for display or processing. If an object needs to be modified on a background thread, make it 'nonisolated' but not Sendable.

    Closures with shared state can also be safe as long as they are not called concurrently.
*   [23:18] - Actors
    As an app grows, the main actor can manage a lot of state, leading to frequent context switching. Introducing actors can mitigate this. Actors isolate their data, allowing only one thread to access it at a time, preventing contention.

    By moving state from the main actor to dedicated actors, more code can execute concurrently on background threads. This frees up the main thread to maintain responsiveness. UI-facing classes and model classes generally need to remain on the main actor or be kept as non-Sendable.
*   [26:12] - Wrap-up
    Apps often start single-threaded and evolve to use asynchronous tasks, concurrent code, and actors for better performance. Swift concurrency aids in this transition, making it easier to move code off the main thread and improve responsiveness. Profiling tools like Instruments help identify when and what code needs to be moved off the main thread. Use the recommended build settings to help simplify introducing concurrency, and the Approachable Concurrency setting to enable a suite of upcoming features to make working with concurrency easier.

# Transcript

[00:06] Hello!
[00:07] I’m Doug from the Swift team, and I’m excited to talk to you about how to make
[00:12] the best use of Swift concurrency in your app.
[00:15] Concurrency allows code to perform multiple tasks at the same time.
[00:20] You can use concurrency in your app
[00:22] to improve responsiveness when waiting on data,
[00:25] like when reading files from disk or performing a network request.
[00:29] It can also be used to offload expensive computation to the background,
[00:33] like processing large images.
[00:36] Swift’s concurrency model is designed to make
[00:39] concurrent code easier to write correctly.
[00:42] It makes the introduction of concurrency explicit
[00:46] and identifies what data is shared across concurrent tasks.
[00:50] It leverages this information to identify potential data races at compile time,
[00:56] so you can introduce concurrency as you need it
[00:58] without fear of creating hard-to-fix data races.
[01:03] Many apps only need to use concurrency sparingly,
[01:06] and some don't need concurrency at all.
[01:09] Concurrent code is more complex than single-threaded code,
[01:12] and you should only introduce concurrency as you need it.
[01:17] Your apps should start by running all of their code on the main thread,
[01:21] and you can get really far with single-threaded code.
[01:24] The main thread is where your app receives UI-related events
[01:28] and can update the UI in response.
[01:30] If you aren’t doing a lot of computation in your app,
[01:33] it’s fine to keep everything on the main thread!
[01:36] Eventually, you are likely to need to introduce asynchronous code,
[01:41] perhaps to fetch some content over the network.
[01:44] Your code can wait for the content to come across the network
[01:47] without causing the UI to hang.
[01:50] If those tasks take too long to run, we can move them off to a background thread
[01:56] that runs concurrently with the main thread.
[01:59] As we develop our app further, we may find
[02:02] that keeping all our data within the main thread
[02:05] is causing the app to perform poorly.
[02:08] Here, we can introduce data types for specific purposes
[02:11] that always run in the background.
[02:15] Swift concurrency provides tools like actors and tasks
[02:19] for expressing these kinds of concurrent operations.
[02:22] A large app is likely to have an architecture that looks a bit like this.
[02:26] But you don’t start there, and not every app needs to end up here.
[02:31] In this session, we’re going to talk through the steps
[02:33] to take an app through this journey
[02:35] from single-threaded to concurrent.
[02:38] For each step along the way, we’ll help you determine when to take that step,
[02:43] what Swift language features that you’ll use, how to use them effectively,
[02:47] and why they work the way they do.
[02:50] First, we’ll describe how single-threaded code works with Swift concurrency.
[02:55] Then, we’ll introduce asynchronous tasks to help with high-latency operations,
[02:59] like network access.
[03:02] Next, we’ll introduce concurrency to move work to a background thread
[03:07] and learn about sharing data across threads without introducing data races.
[03:13] Finally, we’ll move data off the main thread with actors.
[03:17] Let’s start with single-threaded code.
[03:20] When you run a program, code starts running on the main thread.

```swift
var greeting = "Hello, World!"

func readArguments() { }

func greet() {
  print(greeting)
}

readArguments()
greet()
```

[03:24] Any code that you add stays on the main thread,
[03:27] until you explicitly introduce concurrency to run code somewhere else.
[03:32] Single-threaded code is easier to write and maintain,
[03:35] because the code is only doing one thing at a time.
[03:38] If you start to introduce concurrency later on,
[03:41] Swift will protect your main thread code.
[03:44] The main thread and all of its data is represented by the main actor.
[03:49] There is no concurrency on the main actor,
[03:51] because there is only one main thread that can run it.
[03:54] We can specify that data or code is on the main actor using the @MainActor notation.
[04:01] Swift will ensure that main-actor code only ever runs on the main thread,
[04:05] and main-actor data is only ever accessed from there.
[04:09] We say that such code is isolated to the main actor.
[04:14] Swift protects your main thread code using the main actor by default.

```swift
struct Image {
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
}

final class Library {
  static let shared: Library = Library()
}
```

[04:18] This is like the Swift compiler writing
[04:20] @MainActor for you on everything in that module.
[04:24] It lets us freely access shared state like static variables
[04:27] from anywhere in our code.
[04:29] In main actor mode, we don't have to worry about concurrent access
[04:32] until we start to introduce concurrency.
[04:36] Protecting code with the main actor by default is driven by a build setting.
[04:40] Use this primarily for your main app module
[04:43] and any modules that are focused on UI interactions.
[04:47] This mode is enabled by default for new app projects
[04:50] created with Xcode 26.
[04:52] In this talk, we'll assume that main actor mode
[04:54] is enabled throughout the code examples.
[04:58] Let's add a method on our image model to fetch and display an image from a URL.
[05:03] We want to load an image from a local file.
[05:07] Then decode it,
[05:08] and display it in our UI.

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) throws {
    let data = try Data(contentsOf: url)
    let image = decodeImage(data)
    view.displayImage(image)
  }

  func decodeImage(_ data: Data) -> Image {
    Image()
  }
}

final class Library {
  static let shared: Library = Library()
}
```

[05:10] Our app has no concurrency in it at all.
[05:13] There is just a single, main thread doing all of the work.
[05:18] This whole function runs on the main thread in one piece.
[05:21] So long as every operation in here is fast enough, that’s fine.
[05:27] Right now, we’re only able to read files locally.
[05:30] If we want to allow our app to fetch an image over the network,
[05:34] we need to use a different API.

```swift
import Foundation

struct Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) throws {
    let (data, _) = try URLSession.shared.data(from: url)
    let image = decodeImage(data)
    view.displayImage(image)
  }

  func decodeImage(_ data: Data) -> Image {
    Image()
  }
}

final class Library {
  static let shared: Library = Library()
}
```

[05:37] This URLSession API lets us fetch data over the network given a URL.
[05:42] However, running this method on the main thread would freeze the UI
[05:47] until the data has been downloaded from the network.
[05:50] As a developer, it’s important to keep your app responsive.
[05:54] That means taking care not to tie up the main thread for so long
[05:58] that the UI will glitch or hang.
[06:00] Swift concurrency provides tools to help:
[06:03] asynchronous tasks can be used when waiting on data,
[06:06] such as a network request, without tying up the main thread.
[06:11] To prevent hangs like this, network access is asynchronous.

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) async throws {
    let (data, _) = try await URLSession.shared.data(from: url)
    let image = decodeImage(data)
    view.displayImage(image)
  }

  func decodeImage(_ data: Data) -> Image {
    Image()
  }
}

final class Library {
  static let shared: Library = Library()
}
```

[06:16] We can change fetchAndDisplayImage so that it's capable of handling asynchronous calls
[06:21] by making the function 'async', and calling the URL session API with 'await'.
[06:27] The await indicates where the function might suspend,
[06:30] meaning that it stops running on the current thread
[06:33] until the event it’s waiting for happens.
[06:36] Then, it can resume execution.
[06:39] We can think of this as breaking the function into two pieces:
[06:43] the piece that runs up until we start to fetch the image,
[06:46] and the piece that runs after the image has been fetched.
[06:49] By breaking up the function this way,
[06:51] we allow other work to run in between the two pieces,
[06:55] keeping our UI responsive.
[06:58] In practice, many library APIs, like URLSession,
[07:02] will offload work to the background for you.
[07:05] We still have not introduced concurrency
[07:07] into our own code, because we didn't need to!
[07:10] We improved the responsiveness of our application by making parts of it asynchronous,
[07:15] and calling library APIs that offload work on our behalf.
[07:19] All we needed to do in our code was adopt async/await.
[07:24] So far, our code is only running one async function.
[07:28] An async function runs in a task.
[07:31] A task executes independently of other code,

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()
  var url: URL = URL("https://swift.org")!

  func onTapEvent() {
    Task {
      do {
	try await fetchAndDisplayImage(url: url)
      } catch let error {
        displayError(error)
      }
    }
  }

  func displayError(_ error: any Error) {
  }

  func fetchAndDisplayImage(url: URL) async throws {
  }
}

final class Library {
  static let shared: Library = Library()
}
```

[07:34] and should be created to perform a specific operation end-to-end.
[07:39] It's common to create a task in response to an event, such as a button press.
[07:44] Here, the task performs the full fetch-and-display image operation.
[07:49] There can be many asynchronous tasks in a given app.
[07:52] In addition to the fetch-and-display image task that we’ve been talking about,
[07:56] here I’ve added a second task that
[07:58] fetches the news, displays it, and then waits for a refresh.
[08:02] Each task will complete its operations in order from start to finish.
[08:07] Fetching happens in the background, but the other operations in each task
[08:12] will all run on the main thread, and only one operation can run at a time.
[08:17] The tasks are independent from each other,
[08:19] so each task can take turns on the main thread.
[08:23] The main thread will run the pieces of each task
[08:25] as they become ready to run.
[08:28] A single thread alternating between multiple tasks is called 'interleaving'.
[08:34] This improves overall performance by making the most efficient use of system resources.
[08:39] A thread can start making progress on any of the tasks as soon as possible,
[08:43] rather than leaving the thread idle while waiting for a single operation.
[08:48] If fetching the image completes before fetching the news,
[08:51] the main thread will start decoding and displaying the image
[08:54] before displaying the news.
[08:57] But if fetching the news finishes first,
[08:59] the main thread can start displaying the news before decoding the image.
[09:06] Multiple asynchronous tasks are great when your app needs to perform
[09:10] many independent operations at the same time.
[09:13] When you need to perform work in a specific order,
[09:16] you should run that work in a single task.

```swift
import Foundation

class Image {
  func applyImageEffect() async { }
}

final class ImageModel {
  func displayImage(_ image: Image) {
  }

  func loadImage() async -> Image {
    Image()
  }
  
  func onButtonTap() {
    Task {
      let image = await loadImage()
      await image.applyImageEffect()
      displayImage(image)
    }
  }
}
```

[09:20] To make your app responsive
[09:21] when there are high-latency operations like a network request,
[09:24] use an asynchronous task to hide that latency.
[09:28] Libraries can help you here,
[09:30] by providing asynchronous APIs that might do some concurrency on your behalf,
[09:34] while your own code stays on the main thread.

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) async throws {
    let (data, _) = try await URLSession.shared.data(from: url)
    let image = decodeImage(data)
    view.displayImage(image)
  }

  func decodeImage(_ data: Data) -> Image {
    Image()
  }
}
```

[09:38] The URLSession API has already introduced some concurrency for us,
[09:41] because it’s handling the network access on a background thread.
[09:45] Our own fetch-and-display image operation is running on the main thread.
[09:50] We might find that the decode operation is taking too long.
[09:54] This could show up as UI hangs when decoding a large image.
[09:59] Asynchronous, single-threaded is often enough for an app.
[10:03] But if you start to notice that your app isn’t responsive,
[10:07] it’s an indication that too much is happening on the main thread.
[10:11] A profiling tool such as Instruments
[10:13] can help you determine where you are spending too much time.
[10:17] If it’s work that can be made faster without concurrency, do that first.
[10:22] If it can’t be made faster, you might need to introduce concurrency.
[10:27] Concurrency is what lets parts of your code run on a background thread
[10:31] in parallel with the main thread, so it doesn’t block the UI.
[10:35] It can also be used to get work done faster
[10:38] by using more of the CPU cores in your system.

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) async throws {
    let (data, _) = try await URLSession.shared.data(from: url)
    let image = decodeImage(data, at: url)
    view.displayImage(image)
  }

  func decodeImage(_ data: Data, at url: URL) -> Image {
    Image()
  }
}
```

[10:41] Our goal is to get the decoding off the main thread,
[10:45] so that work can happen on the background thread.
[10:48] Because we're in the main actor by default mode,
[10:51] fetchAndDisplaylmage and decodelmage are both isolated to the main actor.
[10:56] Main actor code can freely access all data and code
[11:00] that is accessible only to the main thread,
[11:03] which is safe because there's no concurrency on the main thread.
[11:07] We want to offload the call to decodeImage,
[11:11] Which we can do by applying the @concurrent attribute
[11:14] to the decodeImage function.

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) async throws {
    let (data, _) = try await URLSession.shared.data(from: url)
    let image = await decodeImage(data, at: url)
    view.displayImage(image)
  }

  @concurrent
  func decodeImage(_ data: Data, at url: URL) async -> Image {
    Image()
  }
}
```

[11:16] @concurrent tells Swift to run the function in the background.
[11:21] Changing where decodeImage runs
[11:23] also changes our assumptions about what state decodeImage can access.
[11:28] Let's take a look at the implementation.

```swift
final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var cachedImage: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) async throws {
    let (data, _) = try await URLSession.shared.data(from: url)
    let image = await decodeImage(data, at: url)
    view.displayImage(image)
  }

  @concurrent
  func decodeImage(_ data: Data, at url: URL) async -> Image {
    if let image = cachedImage[url] {
      return image
    }

    // decode image
    let image = Image()
    cachedImage[url] = image
    return image
  }
}
```

[11:31] The implementation is checking a dictionary of cached image data
[11:35] that's stored on the main actor, which is only safe to do on the main thread.
[11:41] The Swift compiler shows us where the function
[11:43] is trying to access data on the main actor.
[11:46] This is exactly what we need to know
[11:48] to make sure we're not introducing bugs as we add concurrency.
[11:53] There are a few strategies you can use when breaking ties to the main actor
[11:56] so you can introduce concurrency safely.
[11:59] In some cases, you can move the main actor code into a caller
[12:03] that always runs on the main actor.
[12:05] This is a good strategy if you want to make sure that work happens synchronously.
[12:11] Or, you can use await to access the main actor from concurrent code asynchronously.
[12:18] If the code doesn’t need to be on the main actor at all, you can add
[12:22] the nonisolated keyword to separate it from any actor.
[12:26] We’re going to explore the first strategy now,
[12:29] and will talk about the others later on.
[12:32] I'm going to move the image caching
[12:33] into fetchAndDisplayImage, which runs on the main actor.
[12:38] Checking the cache before making any async calls is good for eliminating latency.
[12:43] If the image is in the cache, fetchAndDisplayImage
[12:46] will complete synchronously without suspending at all.
[12:50] This means the results will be delivered to the UI immediately,
[12:53] and it will only suspend if the image is not already available.

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var cachedImage: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) async throws {
    if let image = cachedImage[url] {
      view.displayImage(image)
      return
    }

    let (data, _) = try await URLSession.shared.data(from: url)
    let image = await decodeImage(data)
    view.displayImage(image)
  }

  @concurrent
  func decodeImage(_ data: Data) async -> Image {
    // decode image
    Image()
  }
}
```

[12:58] And we can remove the url parameter
[13:00] from decodeImage because we don't need it anymore.
[13:03] Now, all we have to do is await the result of decodeImage.
[13:09] An @concurrent function will always switch off of an actor to run.
[13:14] If you want the function to stay on whatever actor it was called on,
[13:17] you can use the nonisolated keyword.
[13:20] Swift has additional ways to introduce more concurrency.
[13:24] For more information, see “Beyond the basics of structured concurrency”.
[13:29] If we were providing decoding APIs as part of a library for many clients to use,
[13:35] using @concurrent isn't always the best API choice.

```swift
// Foundation
import Foundation

nonisolated
public class JSONDecoder {
  public func decode<T: Decodable>(_ type: T.Type, from data: Data) -> T {
    fatalError("not implemented")
  }
}
```

[13:38] How long it takes to decode data depends on how large the data is,
[13:43] and decoding small amounts of data is okay to do on the main thread.
[13:47] For libraries, it's best to provide a nonisolated API
[13:52] and let clients decide whether to offload work.
[13:56] Nonisolated code is very flexible, because you can call it from anywhere:
[14:01] if you call it from the main actor, it will stay on the main actor.
[14:05] If you call it from a background thread, it will stay on a background thread.
[14:09] This makes it a great default for general-purpose libraries.
[14:13] When you offload work to the background, the system handles scheduling the work
[14:17] to run on a background thread.
[14:20] The concurrent thread pool contains all of the system's background threads,
[14:24] which can involve any number of threads.
[14:27] For smaller devices like a watch,
[14:28] there might be only be one or two threads in the pool.
[14:32] Large systems with more cores will have more background threads in the pool.
[14:37] It doesn't matter which background thread a task runs on,
[14:39] and you can rely on the system to make the best use of resources.
[14:43] For example, when a task suspends,
[14:46] the original thread will start running other tasks that are ready.
[14:50] When the task resumes,
[14:51] it can start running on any available thread in the concurrent pool,
[14:55] which might be different from the background thread it started on.
[14:59] Now that we have concurrency, we will be sharing data among different threads.
[15:03] Sharing mutable state in concurrent code is notoriously prone to mistakes
[15:08] that lead to hard-to-fix runtime bugs.
[15:11] Swift helps you catch these mistakes at compile time
[15:14] so you can write concurrent code with confidence.
[15:18] Each time we go between the main actor and the concurrent pool,

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) async throws {
    let (data, _) = try await URLSession.shared.data(from: url)
    let image = await decodeImage(data, at: url)
    view.displayImage(image)
  }

  @concurrent
  func decodeImage(_ data: Data, at url: URL) async -> Image {
    Image()
  }
}
```

[15:22] we share data between different threads.
[15:25] When we get the URL from the UI, it’s passed from the main actor
[15:29] out the background thread to fetch the image.
[15:32] Fetching the image returns data, which is passed along to image decoding.
[15:38] Then, after we’ve decoded the image,
[15:41] the image is passed back into the main actor, along with self.
[15:45] Swift ensures that all of these values are accessed safely in concurrent code.
[15:50] Let's see what happens if the UI update ends up creating additional tasks
[15:54] that involve the URL.
[15:56] Fortunately, URL is a value type.
[15:59] That means that when we copy the URL into the background thread,
[16:04] the background thread has a separate copy from the one that’s on the main thread.
[16:08] If the user enters a new URL through the UI,
[16:12] code on the main thread is free to use or modify its copy,
[16:16] and the changes have no effect on the value used on the background thread.
[16:20] This means that it is safe to share value types like URL
[16:24] because it isn’t really sharing after all:
[16:26] each copy is independent of the others.

```swift
// Value types are common in Swift
import Foundation

struct Post {
  var author: String
  var title: String
  var date: Date
  var categories: [String]
}
```

[16:30] Value types have been a big part of Swift from the beginning.
[16:34] All of the basic types like strings, integers, and dates, are value types.
[16:40] Collections of value types,
[16:41] such as dictionaries and arrays, are also value types.
[16:46] And so are structs and enums that store value types in them,
[16:49] like this Post struct.

```swift
import Foundation

// Value types are Sendable
extension URL: Sendable {}

// Collections of Sendable elements
extension Array: Sendable where Element: Sendable {}

// Structs and enums with Sendable storage
struct ImageRequest: Sendable {
  var url: URL
}

// Main-actor types are implicitly Sendable
@MainActor class ImageModel {}
```

[16:52] We refer to types that are always safe to share concurrently as Sendable types.
[16:57] Sendable is a protocol, and any type that conforms to Sendable is safe to share.
[17:03] Collections like Array define conditional conformances to Sendable,
[17:07] so they are Sendable when their elements are.
[17:10] Structs and enums are allowed to be marked Sendable
[17:13] when all of their instance data is Sendable.
[17:16] And main actor types are implicitly Sendable,
[17:19] so you don’t have to say so explicitly.

```swift
import Foundation

class Image {
}

final class View {
  func displayImage(_ image: Image) {
  }
}

final class ImageModel {
  var imageCache: [URL: Image] = [:]
  let view = View()

  func fetchAndDisplayImage(url: URL) async throws {
    let (data, _) = try await URLSession.shared.data(from: url)
    let image = await self.decodeImage(data, at: url)
    view.displayImage(image)
  }

  @concurrent
  func decodeImage(_ data: Data, at url: URL) async -> Image {
    Image()
  }
}
```

[17:22] Actors like the main actor protect non-Sendable state
[17:26] by making sure it’s only ever accessed by one task at a time.
[17:31] Actors might store values passed into its methods,
[17:34] and the actor might return a reference to its protected state from its methods.
[17:39] Whenever a value is sent into or out of an actor,
[17:43] the Swift compiler checks that the value is safe to send to concurrent code.
[17:48] Let's focus on the async call to decodeImage.
[17:53] Decode image is an instance method, so we're passing an implicit self argument.
[17:59] Here, we see two values being sent outside the main actor,
[18:03] and a result value being sent back into the main actor.
[18:07] 'self' is my image model class, which is main actor isolated.
[18:11] The main actor protects the mutable state,
[18:14] so it's safe to pass a reference to the class
[18:16] to the background thread.
[18:19] And Data is a value type, so it's Sendable.
[18:22] That leaves the image type.
[18:25] It could be a value type, like Data, in which case it would be Sendable.
[18:29] Instead let’s talk about types that are not Sendable, such as classes.
[18:34] Classes are reference types, meaning that when you assign one variable to another,

```swift
import Foundation

struct Color { }

nonisolated class MyImage {
  var width: Int
  var height: Int
  var pixels: [Color]
  var url: URL

  init() {
    width = 100
    height = 100
    pixels = []
    url = URL("https://swift.org")!
  }

  func scale(by factor: Double) {
  }
}

let image = MyImage()
let otherImage = image // refers to the same object as 'image'
image.scale(by: 0.5)   // also changes otherImage!
```

[18:39] they point at the same object in memory.
[18:42] If you change something about the object through one variable,
[18:45] such as scaling the image, then those changes are
[18:48] immediately visible through the other variables that point at the same object.
[18:54] fetchAndDisplayImage does not use the image value concurrently.
[18:58] decodeImage runs in the background,
[19:00] so it can't access any state protected by an actor.
[19:04] It creates a new instance of an image from the given data.
[19:07] This image can't be referenced by any concurrent code,
[19:11] so it's safe to send over to the main actor and display it in the UI.

```swift
import Foundation

struct Color { }

nonisolated class MyImage {
  var width: Int
  var height: Int
  var pixels: [Color]
  var url: URL

  init() {
    width = 100
    height = 100
    pixels = []
    url = URL("https://swift.org")!
  }

  func scaleImage(by factor: Double) {
  }
}

final class View {
  func displayImage(_ image: MyImage) {
  }
}

final class ImageModel {
  var cachedImage: [URL: MyImage] = [:]
  let view = View()

  // Slide content start
  func scaleAndDisplay(imageName: String) {
    let image = loadImage(imageName)
    Task { @concurrent in
      image.scaleImage(by: 0.5)
    }

    view.displayImage(image)
  }
  // Slide content end

  func loadImage(_ imageName: String) -> MyImage {
    // decode image
    return MyImage()
  }
}
```

[19:16] Let’s see what happens when we introduce some concurrency.
[19:19] First, this scaleAndDisplay method loads a new image on the main thread.
[19:24] The image variable points to this image object, which contains the cat picture.
[19:29] Then, the function creates a task running on the concurrent pool,
[19:33] and that gets a copy of the image.
[19:36] Finally, the main thread moves on to display the image.
[19:41] Now, we have a problem.
[19:42] The background thread is changing the image: making the width and height different,
[19:47] and replacing the pixels with those of a scaled version.
[19:50] At the same time, the main thread is iterating
[19:54] over the pixels based on the old width and height.
[19:58] That’s a data race.
[19:59] You might end up with a UI glitch, or more likely you’ll end up with a crash
[20:03] when your program tries to access outside of the pixel array’s bounds.
[20:08] Swift concurrency prevents data races
[20:10] with compiler errors if your code tries to share a non-Sendable type.
[20:15] Here, the compiler is indicating that the concurrent task is capturing the image,
[20:20] which is also used by the main actor to display the image.
[20:24] To correct this, we need to make sure that we avoid sharing
[20:27] the same object concurrently.
[20:29] If we want the image effect to be shown in the UI,
[20:32] the right solution is to wait for the scaling
[20:34] to complete before displaying the image.

```swift
import Foundation

struct Color { }

nonisolated class MyImage {
  var width: Int
  var height: Int
  var pixels: [Color]
  var url: URL

  init() {
    width = 100
    height = 100
    pixels = []
    url = URL("https://swift.org")!
  }

  func scaleImage(by factor: Double) {
  }
}

final class View {
  func displayImage(_ image: MyImage) {
  }
}

final class ImageModel {
  var cachedImage: [URL: MyImage] = [:]
  let view = View()

  func scaleAndDisplay(imageName: String) {
    Task { @concurrent in
      let image = loadImage(imageName)
      image.scaleImage(by: 0.5)
      await view.displayImage(image)
    }
  }

  nonisolated
  func loadImage(_ imageName: String) -> MyImage {
    // decode image
    return MyImage()
  }
}
```

[20:37] We can move all three of these operations into the task
[20:40] to make sure they happen in order.

```swift
import Foundation

struct Color { }

nonisolated class MyImage {
  var width: Int
  var height: Int
  var pixels: [Color]
  var url: URL

  init() {
    width = 100
    height = 100
    pixels = []
    url = URL("https://swift.org")!
  }

  func scaleImage(by factor: Double) {
  }
}

final class View {
  func displayImage(_ image: MyImage) {
  }
}

final class ImageModel {
  var cachedImage: [URL: MyImage] = [:]
  let view = View()

  @concurrent
  func scaleAndDisplay(imageName: String) async {
    let image = loadImage(imageName)
    image.scaleImage(by: 0.5)
    await view.displayImage(image)
  }

  nonisolated
  func loadImage(_ imageName: String) -> MyImage {
    // decode image
    return MyImage()
  }
}
```

[20:43] displayImage has to run on the main actor,
[20:46] so we use await to call it from a concurrent task.
[20:51] If we can make scaleAndDisplay async directly,
[20:54] we can simplify the code to not create a new task,
[20:57] and perform the three operations in order in the task that calls scaleAndDisplay.

```swift
import Foundation

struct Color { }

nonisolated class MyImage {
  var width: Int
  var height: Int
  var pixels: [Color]
  var url: URL

  init() {
    width = 100
    height = 100
    pixels = []
    url = URL("https://swift.org")!
  }

  func scaleImage(by factor: Double) {
  }

  func applyAnotherEffect() {
  }
}

final class View {
  func displayImage(_ image: MyImage) {
  }
}

final class ImageModel {
  var cachedImage: [URL: MyImage] = [:]
  let view = View()

  // Slide content start
  @concurrent
  func scaleAndDisplay(imageName: String) async {
    let image = loadImage(imageName)
    image.scaleImage(by: 0.5)
    await view.displayImage(image)
    image.applyAnotherEffect()
  }
  // Slide content end

  nonisolated
  func loadImage(_ imageName: String) -> MyImage {
    // decode image
    return MyImage()
  }
}
```

[21:02] Once we send the image to the main actor to display in the UI,
[21:06] the main actor is free to store a reference to the image,
[21:09] for example by caching the image object.
[21:12] If we try to change the image after it's displayed in the UI,
[21:16] we'll get a compiler error about unsafe concurrent access.

```swift
import Foundation

struct Color { }

nonisolated class MyImage {
  var width: Int
  var height: Int
  var pixels: [Color]
  var url: URL

  init() {
    width = 100
    height = 100
    pixels = []
    url = URL("https://swift.org")!
  }

  func scaleImage(by factor: Double) {
  }

  func applyAnotherEffect() {
  }
}

final class View {
  func displayImage(_ image: MyImage) {
  }
}

final class ImageModel {
  var cachedImage: [URL: MyImage] = [:]
  let view = View()

  // Slide content start
  @concurrent
  func scaleAndDisplay(imageName: String) async {
    let image = loadImage(imageName)
    image.scaleImage(by: 0.5)
    image.applyAnotherEffect()
    await view.displayImage(image)
  }
  // Slide content end

  nonisolated
  func loadImage(_ imageName: String) -> MyImage {
    // decode image
    return MyImage()
  }
}
```

[21:20] We can address the issue by making any changes to the image
[21:23] before we send it over to the main actor.
[21:27] If you are using classes for your data model,
[21:29] your model classes will likely start on the main actor,
[21:32] so you can present parts of them in the UI.
[21:35] If you eventually decide that you need to work with them on a background thread,
[21:39] make them nonisolated.
[21:42] But they should probably not be Sendable.
[21:44] You don’t want to be in a position where some of the model
[21:46] is being updated on the main thread
[21:49] and other parts of the model are being updated on the background thread.
[21:53] Keeping model classes non-Sendable
[21:55] prevents this kind of concurrent modification from occurring.
[21:59] It's also easier, because making a class Sendable
[22:01] usually requires using a low-level synchronization mechanism like a lock.

```swift
import Foundation

struct Color { }

nonisolated class MyImage {
  var width: Int
  var height: Int
  var pixels: [Color]
  var url: URL

  init() {
    width = 100
    height = 100
    pixels = []
    url = URL("https://swift.org")!
  }

  func scale(by factor: Double) {
  }

  func applyAnotherEffect() {
  }
}

final class View {
  func displayImage(_ image: MyImage) {
  }
}

final class ImageModel {
  var cachedImage: [URL: MyImage] = [:]
  let view = View()

  // Slide content start
  @concurrent
  func scaleAndDisplay(imageName: String) async throws {
    let image = loadImage(imageName)
    try await perform(afterDelay: 0.1) {
      image.scale(by: 0.5)
    }
    await view.displayImage(image)
  }

  nonisolated
  func perform(afterDelay delay: Double, body: () -> Void) async throws {
    try await Task.sleep(for: .seconds(delay))
    body()
  }
  // Slide content end
  
  nonisolated
  func loadImage(_ imageName: String) -> MyImage {
    // decode image
    return MyImage()
  }
}
```

[22:06] Like classes, closures can create shared state.
[22:10] Here is a function similar to one we had earlier that scales and displays an image.
[22:16] It creates an image object.
[22:18] Then, it calls perform(afterDelay:),
[22:20] providing it with a closure that scales the image object.
[22:24] This closure contains another reference to the same image.
[22:28] We call this a capture of the image variable.
[22:31] Just like non-Sendable classes,
[22:33] a closure with shared state is still safe as long as it isn't called concurrently.
[22:39] Only make a function type Sendable if you need to share it concurrently.
[22:44] Sendable checking occurs whenever some data passes between actors and tasks.
[22:49] It’s there to ensure that there are no data races
[22:52] that could cause bugs in your app.
[22:55] Many common types are Sendable,
[22:57] and these can be freely shared across concurrent tasks.
[23:01] Classes and closures can involve mutable state
[23:04] that is not safe to share concurrently,
[23:06] so use them from one task at a time.
[23:10] You can still send an object from one task to another,
[23:13] but be sure to make all modifications to the object before sending it.
[23:18] Moving asynchronous tasks to background threads
[23:21] can free up the main thread to keep your app responsive.
[23:24] If you find that you have a lot of data on the main actor
[23:27] that is causing those asynchronous tasks to “check in” with the main thread too often,
[23:32] you might want to introduce actors.
[23:35] As your app grows over time,
[23:37] you may find that the amount of state on the main actor also grows.
[23:42] You’ll introduce new subsystems to handle things like managing access to the network.

```swift
import Foundation

nonisolated class MyImage { }

struct Connection {
  func data(from url: URL) async throws -> Data { Data() }
}

final class NetworkManager {
  var openConnections: [URL: Connection] = [:]

  func openConnection(for url: URL) async -> Connection {
    if let connection = openConnections[url] {
      return connection
    }

    let connection = Connection()
    openConnections[url] = connection
    return connection
  }

  func closeConnection(_ connection: Connection, for url: URL) async {
    openConnections.removeValue(forKey: url)
  }

}

final class View {
  func displayImage(_ image: MyImage) {
  }
}

final class ImageModel {
  var cachedImage: [URL: MyImage] = [:]
  let view = View()
  let networkManager: NetworkManager = NetworkManager()

  func fetchAndDisplayImage(url: URL) async throws {
    if let image = cachedImage[url] {
      view.displayImage(image)
      return
    }

    let connection = await networkManager.openConnection(for: url)
    let data = try await connection.data(from: url)
    await networkManager.closeConnection(connection, for: url)

    let image = await decodeImage(data)
    view.displayImage(image)
  }

  @concurrent
  func decodeImage(_ data: Data) async -> MyImage {
    // decode image
    return MyImage()
  }
}
```

[23:47] This can lead to a lot of state living on the main actor,
[23:51] for example the set of open connections handled by the network manager,
[23:55] which we would access whenever we need to fetch data over the network.
[24:00] When we start using these extra subsystems,
[24:03] the fetch-and-display image task from earlier has gotten more complicated:
[24:07] it’s trying to run on the background thread,
[24:10] but it has to hop over to the main thread because
[24:12] that’s where the network manager’s data is.
[24:15] This can lead to contention,
[24:16] where many tasks are trying to run code on the main actor at the same time.
[24:21] The individual operations might be quick, but if you have a lot of tasks doing this,
[24:26] it can add up to UI glitches.
[24:29] Earlier, we moved code off the main thread
[24:31] by putting it into an @concurrent function.
[24:35] Here, all of the work is in accessing the network manager’s data.
[24:39] To move that out, we can introduce our own network manager actor.

```swift
import Foundation

nonisolated class MyImage { }

struct Connection {
  func data(from url: URL) async throws -> Data { Data() }
}

actor NetworkManager {
  var openConnections: [URL: Connection] = [:]

  func openConnection(for url: URL) async -> Connection {
    if let connection = openConnections[url] {
      return connection
    }

    let connection = Connection()
    openConnections[url] = connection
    return connection
  }

  func closeConnection(_ connection: Connection, for url: URL) async {
    openConnections.removeValue(forKey: url)
  }

}

final class View {
  func displayImage(_ image: MyImage) {
  }
}

final class ImageModel {
  var cachedImage: [URL: MyImage] = [:]
  let view = View()
  let networkManager: NetworkManager = NetworkManager()

  func fetchAndDisplayImage(url: URL) async throws {
    if let image = cachedImage[url] {
      view.displayImage(image)
      return
    }

    let connection = await networkManager.openConnection(for: url)
    let data = try await connection.data(from: url)
    await networkManager.closeConnection(connection, for: url)

    let image = await decodeImage(data)
    view.displayImage(image)
  }

  @concurrent
  func decodeImage(_ data: Data) async -> MyImage {
    // decode image
    return MyImage()
  }
}
```

[24:44] Like the main actor, actors isolate their data,
[24:47] so you can only access that data when running on that actor.
[24:51] Along with the main actor, you can define your own actor types.
[24:55] An actor type is similar to a main-actor class.
[24:59] Like a main actor-class, it will isolate its data
[25:02] so that only one thread can touch the data at a time.
[25:05] An actor type is also Sendable, so you can freely share actor objects.
[25:10] Unlike the main actor, there can be many actor objects in a program,
[25:14] each of which is independent.
[25:17] In addition, actor objects aren’t tied to a single thread like the main actor is.
[25:23] So moving some state from the main actor over to an actor object
[25:27] will allow more code to execute on a background thread,
[25:30] leaving the main thread open to keep the UI responsive.
[25:34] Use actors when you find that storing data on the main actor
[25:38] is causing too much code to run on the main thread.
[25:41] At that point, separate out the data for one non-UI part of your code,
[25:46] such as the network management code, into a new actor.
[25:50] Be aware that most of the classes in your app probably are not meant to be actors:
[25:55] UI-facing classes should stay on the main actor
[25:58] so they can interact directly with UI state.
[26:01] Model classes should generally be on the main actor with the UI,
[26:05] or kept non-Sendable,
[26:07] so that you don’t encourage lots of concurrent accesses to your model.
[26:12] In this talk, we started with single-threaded code.
[26:16] As our needs grew, we introduced asynchronous tasks to hide latency,
[26:21] concurrent code to run on a background thread,
[26:24] and actors to move data access off the main thread.
[26:28] Over time, many apps will follow this same course.
[26:33] Use profiling tools to identify when and what code to move off the main thread.
[26:39] Swift concurrency will help you separate that code from the main thread correctly,
[26:43] improving the performance and responsiveness of your app.
[26:48] We have some recommended build settings for your app
[26:50] to help with the introduction of concurrency.
[26:53] The Approachable Concurrency setting enables a suite of upcoming features
[26:57] that make easier to work with concurrency.
[27:00] We recommend that all projects adopt this setting.
[27:04] For Swift modules that are primarily interacting with the UI,
[27:07] such as your main app module,
[27:09] we also recommend setting the default actor isolation to 'main actor'.
[27:14] This puts code on the main actor unless you’ve said otherwise.
[27:18] These settings work together to make single-threaded apps easier to write,
[27:22] and provide a more approachable path to introducing concurrency when you need it.
[27:28] Swift concurrency is a tool designed to help improve your app.
[27:31] Use it to introduce asynchronous or concurrent code
[27:34] when you find performance problems with your app.
[27:37] The Swift 6 migration guide can help answer more questions about concurrency
[27:41] and the road to data-race safety.
[27:44] And to see how the concepts in this talk apply in an example app,
[27:48] please watch our code-along companion talk.
[27:51] Thank you.

# Resources

*   [Swift Migration Guide](https://www.swift.org/migration/documentation/migrationguide/)
*   [The Swift Programming Language: Concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/)
*   [HD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/268/4/9de10aea-96a5-468d-a7b9-211a8f9b2d0a/downloads/wwdc2025-268_hd.mp4?dl=1)
*   [SD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/268/4/9de10aea-96a5-468d-a7b9-211a8f9b2d0a/downloads/wwdc2025-268_sd.mp4?dl=1)

## Related Videos

#### WWDC25

*   [Code-along: Elevate an app with Swift concurrency](/videos/play/wwdc2025/270)

#### WWDC23

*   [Beyond the basics of structured concurrency](/videos/play/wwdc2023/10170)
