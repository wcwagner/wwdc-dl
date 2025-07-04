---
session: 270
year: 2025
title: Code-along: Elevate an app with Swift concurrency
presenters: []
duration: 33
---

## About

Learn how to optimize your app's user experience with Swift concurrency as we update an existing sample app. We'll start with a main-actor app, then gradually introduce asynchronous code as we need to. We'll use tasks to optimize code running on the main actor, and discover how to parallelize code by offloading work to the background. We'll explore what data-race safety provides, and work through interpreting and fixing data-race safety errors. Finally, we'll show how you can make the most out of structured concurrency in the context of an app.

### Chapters

*   [00:00] - Introduction
*   [02:11] - Approachable concurrency configuration
*   [02:51] - Sample app architecture
*   [03:42] - Asynchronously loading photos from the photo library
*   [09:03] - Extracting the sticker and the colors from the photo
*   [12:30] - Running tasks on a background thread
*   [15:58] - Parallelizing tasks
*   [18:44] - Preventing data races with Swift 6
*   [27:56] - Controlling asynchronous code with structured concurrency
*   [31:36] - Wrap-up

---

## Transcript

[00:06] Hi!
[00:07] I’m Sima, and I work on Swift and SwiftUI.
[00:12] In this video, you will learn how to elevate your app with Swift concurrency.
[00:18] As app developers, most of the code we write is on the main thread.

[00:24] Single-threaded code is easy to understand and maintain.
[00:29] But at the same time, a modern app often needs to perform time-consuming tasks,
[00:35] like a network request, or an expensive computation.
[00:39] In such cases, it is a great practice to move work off the main thread
[00:44] to keep the app responsive.
[00:48] Swift gives you all the tools you need to write concurrent code with confidence.
[00:53] In this session, I will show you how by building an app with you.
[00:58] We will start with a single-threaded app,
[01:01] and gradually introduce asynchronous code as we need to.
[01:06] Then, we will improve the performance of the app by offloading
[01:10] some of the expensive tasks and running them in parallel.
[01:14] Next, we’ll discuss some common data-race safety scenarios you might encounter
[01:19] and explore ways to approach them.
[01:22] And finally, I will touch on structured concurrency and show you how to use tools
[01:28] such as a TaskGroup for more control over your concurrent code.
[01:34] I can’t wait to get started!
[01:37] I love journaling, and decorating my entries with stickers,
[01:41] so I will walk you
[01:42] through building an app for composing sticker packs out of any set of photos.
[01:49] Our app will have two main views.
[01:51] The first view will feature a carousel with all stickers with a gradient
[01:56] reflecting the colors from the original photo,
[01:59] and the second one will show a grid preview
[02:02] of the entire sticker pack, ready to be exported.
[02:06] Feel free to download the sample app below to follow along!
[02:11] When I created the project, Xcode enabled a few features that provide
[02:16] a more approachable path to introducing concurrency,
[02:20] including main actor by default mode and a few upcoming features.
[02:25] These features are enabled by default in new app projects in Xcode 26.

[02:32] In the approachable concurrency configuration,
[02:35] the Swift 6 language mode will provide data-race safety
[02:38] without introducing concurrency until you are ready.
[02:43] If you want to enable these features in existing projects, you can learn how
[02:49] in the Swift migration guide.
[02:52] In code, the app will have two main views—StickerCarousel and StickerGrid.
[02:59] These views will use the stickers that the PhotoProcessor struct
[03:03] is responsible for extracting.
[03:06] The PhotoProcessor gets the raw image from the photo library
[03:10] before it returns the sticker.
[03:14] The StickerGrid view has a ShareLink which it can use for sharing the stickers.
[03:20] The PhotoProcessor type performs two expensive operations:
[03:25] the sticker extraction and the dominant colors computation.
[03:30] Let’s see how Swift concurrency features
[03:32] can help us optimize for smooth user experience,
[03:36] while still letting the device perform these expensive tasks!
[03:42] I’m going to start with the StickerCarousel view.
[03:46] This view displays the stickers in a horizontal scroll view.
[03:51] Inside of the scroll view,
[03:53] it has a ForEach which iterates over the array of selected photos
[03:57] from the photo library stored in the view model.
[04:01] It checks the processedPhotos dictionary in the viewModel to get the processed
[04:06] photo corresponding to the selection in the photo library.
[04:10] Currently, we don’t have any processed photos, since I haven’t actually written
[04:15] any code to get an image from the photo picker.
[04:19] If I run the app now, all we will see in the scroll view,
[04:23] is the StickerPlaceholder view.
[04:26] I’ll navigate to StickerViewModel using command-click.
[04:31] The StickerViewModel stores an array of currently selected photos
[04:35] from the photo library,
[04:37] represented as a SelectedPhoto type.
[04:40] I’ll open Quick Help with Option-click to learn more about this type.
[04:46] SelectedPhoto is an Identifiable type that stores a PhotosPickerItem
[04:51] from the PhotosUI framework and its associated ID.
[04:56] The model also has the dictionary called processedPhotos
[05:01] that maps the ID of the selected photo to the SwiftUI Image it represents.
[05:07] I have already started working on the loadPhoto function
[05:11] that takes the selected photo.
[05:13] But currently it does not load any data from the photo picker item that it stores.
[05:20] The PhotosPickerItem conforms to the Transferable protocol from the SDK,
[05:25] which allows me to load the representation I request
[05:29] with the asynchronous loadTransferable function.
[05:32] I will request the Data representation.

[05:41] Now, we have a compiler error.

[05:46] It’s because the call to `loadTransferable` is asynchronous,
[05:49] and my `loadPhoto` function where I call it
[05:52] is not set up to handle asynchronous calls,
[05:55] so Swift helps me by suggesting to mark `loadPhoto` with the async keyword.
[06:01] I’m going to apply this suggestion.

[06:07] Our function is capable of handling asynchronous code.
[06:10] But, there’s still one more error.
[06:13] While `loadPhoto` can handle asynchronous calls, we need to tell it what to wait for.
[06:19] To do this, I need to mark the call to `loadTransferable`
[06:23] with the `await` keyword.
[06:25] I’ll apply the suggested fix.

[06:29] Asynchronously loading the selected photo from the photo library

```swift
func loadPhoto(_ item: SelectedPhoto) async {
    var data: Data? = try? await item.loadTransferable(type: Data.self)

    if let cachedData = getCachedData(for: item.id) { data = cachedData }

    guard let data else { return }
    processedPhotos[item.id] = Image(data: data)

    cacheData(item.id, data)
}
```

[06:30] I’ll call this function in the StickerCarousel view.
[06:33] With command-shift-O, I can use Xcode’s Open Quickly
[06:37] to navigate back to the StickerCarousel.

[06:43] I would like to call the loadPhoto function when the StickerPlaceholder view appears.
[06:49] Because this function is asynchronous, I will use the SwiftUI task modifier
[06:54] to kick off photo processing when this view appears.

[06:59] Calling an asynchronous function when the SwiftUI View appears

```swift
StickerPlaceholder()
    .task {
        await viewModel.loadPhoto(selectedPhoto)
    }
```

[07:03] Let’s check this out on my device!
[07:09] Great, it’s up and running.
[07:11] Let’s try selecting a few photos to test it out.

[07:18] Great! Looks like the images are getting loaded from my photo library.
[07:24] The task allows me to keep the app’s UI responsive
[07:28] while the image is being loaded from the data.
[07:32] And because I'm using LazyHStack for displaying the images,
[07:36] I'm only kicking off photo loading tasks for views that need to be rendered on screen,
[07:41] so the app is not performing more work than necessary.
[07:46] Let’s talk about why async/await improves responsiveness of our app.

[07:52] We added the `await` keyword when calling the `loadTransferable` method,
[07:57] and annotated the `loadPhoto` function with `async`.
[08:01] The `await` keyword marks a possible suspension point.
[08:05] It means that initially, the loadPhoto function starts on the main thread,
[08:10] and when it calls loadTransferable at the await,
[08:13] it suspends while it’s waiting for loadTransferable to complete.
[08:18] While loadPhoto is suspended, the Transferable framework will run
[08:23] loadTransferable on the background thread.
[08:26] When loadTransferable is done, loadPhoto will resume its execution
[08:31] on the main thread and update the image.
[08:35] The main thread is free to respond to UI events and run other tasks
[08:39] while the loadPhoto is suspended.
[08:43] The await keyword indicates a point in your code where other work can happen
[08:48] while your function is suspended.
[08:52] And just like that, we are done with loading the images from the photo library!
[08:57] Along the way, we learned what asynchronous code means,
[09:00] how to write and think about it.
[09:04] Now, let’s add some code to our app that would extract the sticker
[09:08] from the photo, and its primary colors that we can use for the background gradient
[09:13] when displayed in a carousel view.
[09:16] I’m going to use command-click to navigate back to loadPhoto
[09:20] where I can apply these effects.

[09:26] The project already includes a PhotoProcessor, which takes the Data,
[09:31] extracts the colors and the sticker, and returns the processed photo.
[09:36] Rather than providing the basic image from the data,
[09:41] I’m going to use the PhotoProcessor instead.

[09:45] Synchronously extracting the sticker and the colors from a photo

```swift
func loadPhoto(_ item: SelectedPhoto) async {
    var data: Data? = try? await item.loadTransferable(type: Data.self)

    if let cachedData = getCachedData(for: item.id) { data = cachedData }

    guard let data else { return }
    processedPhotos[item.id] = PhotoProcessor().process(data: data)

    cacheData(item.id, data)
}
```

[09:50] The PhotoProcessor returns a processed photo,
[09:53] so I’ll update the dictionary’s type.

[09:56] Storing the processed photo in the dictionary

```swift
var processedPhotos = [SelectedPhoto.ID: ProcessedPhoto]()
```

[10:04] This ProcessedPhoto will provide us the sticker extracted from the photo
[10:09] and the array of colors to compose the gradient from.

[10:16] I’ve already included a GradientSticker view in the project that takes a processedPhoto.
[10:23] I’m going to use Open Quickly to navigate to it.

[10:31] This view shows a sticker stored in a processed photo
[10:34] on top of a linear gradient in a ZStack.
[10:39] I’m going to add this GradientSticker in the carousel.

[10:44] Currently, in the StickerCarousel we are just resizing the photo,
[10:49] but now that we have a processed photo, we can use the GradientSticker here instead.

[10:45] Displaying the sticker with a gradient background in the carousel

```swift
import SwiftUI
import PhotosUI

struct StickerCarousel: View {
    @State var viewModel: StickerViewModel
    @State private var sheetPresented: Bool = false

    var body: some View {
        ScrollView(.horizontal) {
            LazyHStack(spacing: 16) {
                ForEach(viewModel.selection) { selectedPhoto in
                    VStack {
                        if let processedPhoto = viewModel.processedPhotos[selectedPhoto.id] {
                            GradientSticker(processedPhoto: processedPhoto)
                        } else if viewModel.invalidPhotos.contains(selectedPhoto.id) {
                            InvalidStickerPlaceholder()
                        } else {
                            StickerPlaceholder()
                                .task {
                                    await viewModel.loadPhoto(selectedPhoto)
                                }
                        }
                    }
                    .containerRelativeFrame(.horizontal)
                }
            }
        }
        .configureCarousel(
            viewModel,
            sheetPresented: $sheetPresented
        )
        .sheet(isPresented: $sheetPresented) {
            StickerGrid(viewModel: viewModel)
        }
    }
}
```

[10:59] Let’s build and run the app to see our stickers!
[11:08] It’s working!
[11:11] Oh no!
[11:12] While the stickers are being extracted,
[11:15] scrolling through the carousel isn’t that smooth.

[11:19] I suspect the image processing is very expensive.
[11:23] I have profiled the app using Instruments to confirm that.
[11:27] The trace shows that our app has Severe Hangs.
[11:32] If I zoom in on it and look at the heaviest stack trace,
[11:35] I can see the photo processor blocking the main thread
[11:39] with the expensive processing tasks for more than 10 seconds!
[11:44] If you want to learn more about analyzing hangs in your app, check out our session
[11:50] “Analyze hangs with Instruments”.
[11:52] Now, let’s talk more about the work our app is doing on the main thread.

[11:59] The implementation of `loadTransferable` handled offloading the work
[12:03] to the background to avoid causing
[12:05] the loading work to happen on the main thread.
[12:09] Now, that we’ve added the image processing code, which is running on the main thread,
[12:14] and takes a long time to complete, the main thread is unable to receive
[12:20] any UI updates, like responding to scrolling gestures,
[12:24] leading to poor user experience in my app.

[12:29] Previously, we adopted an asynchronous API from the SDK,
[12:33] which offloaded the work on our behalf.
[12:36] Now, we need to run our own code in parallel to fix the hang.
[12:42] We can move some of the image transformations into the background.
[12:46] Transforming the image is composed of these three operations.
[12:51] Getting the raw image and updating the image have to interact with the UI,
[12:56] so we can't move this work to the background,
[13:00] but we can offload the image processing.
[13:04] This will ensure the main thread is free to respond to other events
[13:08] while the expensive image processing work is happening.
[13:12] Let’s look at the PhotoProcessor struct to understand how we can do this!
[13:18] Because my app is in the main actor by default mode,
[13:22] the PhotoProcessor is tied to the @MainActor,
[13:25] meaning all of its methods must run on the main actor.
[13:30] The `process` method calls extract sticker and extract colors methods,
[13:35] so I need to mark all methods of this type as capable of running off the main actor.
[13:42] To do this, I can mark the whole PhotoProcessor type with nonisolated.
[13:49] This is a new feature introduced in Swift 6.1.
[13:53] When the type is marked with nonisolated, all of its properties and methods
[13:58] are automatically nonisolated.

[14:02] Now that the PhotoProcessor is not tied to the MainActor, we can apply
[14:07] the new `@concurrent` attribute to the process function
[14:11] and mark it with `async`.
[14:14] This will tell Swift to always switch to a background thread when running this method.
[14:21] I’ll use Open Quickly to navigate back to the PhotoProcessor.

[14:29] First, I’m going to apply nonisolated on the type to decouple the PhotoProcessor
[14:35] from the main actor and allow its methods to be called from concurrent code.

[14:13] Allowing photo processing to run on the background thread

```swift
nonisolated struct PhotoProcessor {
 
    let colorExtractor = ColorExtractor()

    @concurrent
    func process(data: Data) async -> ProcessedPhoto? {
        let sticker = extractSticker(from: data)
        let colors = extractColors(from: data)

        guard let sticker = sticker, let colors = colors else { return nil }

        return ProcessedPhoto(sticker: sticker, colorScheme: colors)
    }

    private func extractColors(from data: Data) -> PhotoColorScheme? {
        // ...
    }

    private func extractSticker(from data: Data) -> Image? {
        // ...
    }
}
```

[14:46] Now that PhotoProcessor is nonisolated,
[14:49] to make sure that the process method
[14:51] will get called from the background thread, I will apply @concurrent and async.

[15:09] Now, I’ll navigate back to the StickerViewModel with Open Quickly.

[15:17] Here, in the loadPhoto method I need to get off the main thread by calling
[15:22] the process method with the `await` keyword, which Swift already suggests.
[15:28] I’m going to apply this suggestion.

[15:31] Running the photo processing operations off the main thread

```swift
func loadPhoto(_ item: SelectedPhoto) async {
    var data: Data? = try? await item.loadTransferable(type: Data.self)

    if let cachedData = getCachedData(for: item.id) { data = cachedData }

    guard let data else { return }
    processedPhotos[item.id] = await PhotoProcessor().process(data: data)

    cacheData(item.id, data)
}
```

[15:32] Let’s build and run our app to see if moving this work off the main actor
[15:37] helped with the hangs!
[15:46] Looks like there are no more hangs on scroll!
[15:50] But even though I can interact with the UI, the image is taking a while to appear
[15:56] in the UI while I'm scrolling.
[15:59] Keeping an app responsive isn't the only factor for improving user experience.
[16:04] If we move work off the main thread but it takes a long time to get results
[16:09] to the user, that can still lead to a frustrating experience using the app.

[16:16] We moved the image processing operation to a background thread,
[16:20] but it still takes a lot of time to complete.
[16:23] Let’s see how we can optimize this operation with concurrency
[16:27] to have it complete faster.
[16:30] Processing the image requires extraction of stickers and the dominant colors,
[16:36] but these operations are independent of each other.
[16:39] So we can run these tasks in parallel with each other using async let.
[16:45] Now, the concurrent thread pool, which manages all of the background threads,
[16:49] will schedule these two tasks to start on two different background threads at once.
[16:55] This allows me to take advantage of multiple cores on my phone.

[17:02] I’ll command-click on the process method to adopt async let.

[17:09] By holding down control + shift and down arrow key, I can use multiline cursor
[17:15] to add async in front of sticker and colors variables.

[17:22] Now that we’ve made these two calls run in parallel, we need to await
[17:27] on their results to resume our process function.
[17:30] Let’s fix all of these issues using the Editor menu.

[17:41] But, there’s still one more error.
[17:45] This time it’s about a data race!
[17:48] Let’s take some time to understand this error.

[17:53] This error means that my PhotoProcessor type
[17:56] is not safe to share between concurrent tasks.
[17:59] To understand why, let’s look at its stored properties.
[18:03] The only property the PhotoProcessor stores is an instance of ColorExtractor,
[18:09] needed to extract the colors from the photo.
[18:13] The ColorExtractor class computes the dominant colors that appear in the image.
[18:18] This computation operates on low-level, mutable image data including pixel buffers,
[18:24] so the color extractor type is not safe to access concurrently.

[18:31] Right now, all color extraction operations share the same instance of the ColorExtractor.
[18:38] This leads to concurrent access to the same memory.
[18:43] This is called a “data race”,
[18:45] which can lead to runtime bugs like crashes and unpredictable behavior.
[18:51] The Swift 6 language mode will identify these at compile time,
[18:56] which defines away this set of bugs when you’re writing code that runs in parallel.
[19:02] This moves what would’ve been a tricky runtime bug into a compiler error
[19:07] that you can address right away.
[19:09] If you click the “help” button on the error message,
[19:12] you can learn more about this error on the Swift website.
[19:17] There are multiple options you can consider when trying to solve a data race.
[19:22] Choosing one depends on how your code uses the shared data.
[19:26] First, ask yourself:
[19:28] Does this mutable state need to be shared between concurrent code?
[19:34] In many cases, you can simply avoid sharing it.
[19:38] However, there are cases where the state needs to be shared by such code.
[19:42] If that is the case, consider extracting what you need to share to a value type
[19:47] that’s safe to send.
[19:50] Only if any of these solutions aren’t applicable to your situation,
[19:54] consider isolating this state to an actor such as the MainActor.
[20:00] Let’s see if the first solution would work for our case!
[20:04] While we could refactor this type to work differently
[20:07] to handle multiple concurrent operations,
[20:10] instead we can move the color extractor
[20:13] to a local variable in the extractColors function,
[20:17] so that each photo being processed has its own instance of the color extractor.
[20:23] This is the correct code change, because the color extractor is intended to work on
[20:28] one photo at a time.
[20:31] So we want a separate instance of it for each color extraction task.
[20:36] With this change, nothing outside of the extractColors function
[20:40] can access the color extractor, which prevents the data race!
[20:45] To make this change, let’s move the color extractor property
[20:49] to the extractColors function.

[20:55] Running sticker and color extraction in parallel.

```swift
nonisolated struct PhotoProcessor {

    @concurrent
    func process(data: Data) async -> ProcessedPhoto? {
        async let sticker = extractSticker(from: data)
        async let colors = extractColors(from: data)

        guard let sticker = await sticker, let colors = await colors else { return nil }

        return ProcessedPhoto(sticker: sticker, colorScheme: colors)
    }

    private func extractColors(from data: Data) -> PhotoColorScheme? {
        let colorExtractor = ColorExtractor()
        return colorExtractor.extractColors(from: data)
    }

    private func extractSticker(from data: Data) -> Image? {
        // ...
    }
}
```

[20:59] Great!
[21:00] With the compiler’s help, we’ve been able to detect and eliminate
[21:03] a data race in our app.
[21:05] Now, let’s run it!
[21:15] I can feel the app running faster!
[21:19] If I collect a profiler trace in Instruments and open it,
[21:22] I no longer see the hangs.
[21:26] Let’s quickly recap the optimizations we made with Swift concurrency!
[21:31] By adopting the `@concurrent` attribute, we have successfully moved
[21:35] our image processing code off the main thread.
[21:38] We have also parallelized its operations, sticker and color extraction
[21:43] with each other using `async let`, making our app much more performant!
[21:50] The optimizations you make with Swift concurrency should always be based on data
[21:54] from analysis tools, such as the time profiler instrument.
[21:59] If you can make your code more efficient without introducing concurrency,
[22:03] you should always do that first.
[22:06] The app feels snappy now!
[22:08] Let’s take a break from image processing and add something fun!
[22:13] Let’s add a visual effect for our processed stickers that will make
[22:17] the sticker scrolled past fade away and blur.
[22:21] Let’s switch to Xcode to write that!
[22:25] I’ll go back to the StickerCarousel using the Xcode project navigator.

[22:33] Now, I’m going to apply the visual effect on each image in the scroll view
[22:38] using the visualEffect modifier.

[22:47] Here, I’m applying some effects to the view.
[22:50] I want to change the offset, the blur, and opacity only for the last sticker
[22:56] in the scroll view,
[22:59] so I need to access the viewModel’s selection property
[23:02] to check if the visual effect is applied to the last sticker.

[23:09] Looks like there’s a compiler error because I’m trying to access
[23:12] main-actor protected view state from the visualEffect closure.
[23:18] Because computing a visual effect is an expensive computation,
[23:22] SwiftUI offloads it off the main thread for maximizing performance of my app.
[23:29] If you feel adventurous and want to learn more,
[23:32] check out our session Explore concurrency in SwiftUI.
[23:37] That’s what this error is telling me:
[23:39] this closure will be evaluated later on the background.
[23:44] Let’s confirm this by looking at the definition of the `visualEffect`,
[23:48] which I’ll command-click on.

[23:53] In the definition, this closure is @Sendable,
[23:56] which is an indication from SwiftUI
[23:59] that this closure will be evaluated on the background.

[24:06] In this case, SwiftUI calls visual effect again whenever selection changes,
[24:12] so I can make a copy of it using the closure's capture list.

[24:20] Applying the visual effect on each sticker in the carousel

```swift
import SwiftUI
import PhotosUI

struct StickerCarousel: View {
    @State var viewModel: StickerViewModel
    @State private var sheetPresented: Bool = false

    var body: some View {
        ScrollView(.horizontal) {
            LazyHStack(spacing: 16) {
                ForEach(viewModel.selection) { selectedPhoto in
                    VStack {
                        if let processedPhoto = viewModel.processedPhotos[selectedPhoto.id] {
                            GradientSticker(processedPhoto: processedPhoto)
                        } else if viewModel.invalidPhotos.contains(selectedPhoto.id) {
                            InvalidStickerPlaceholder()
                        } else {
                            StickerPlaceholder()
                                .task {
                                    await viewModel.loadPhoto(selectedPhoto)
                                }
                        }
                    }
                    .containerRelativeFrame(.horizontal)
                    .visualEffect { [selection = viewModel.selection] content, proxy in
                        let frame = proxy.frame(in: .scrollView(axis: .horizontal))
                        let distance = min(0, frame.minX)
                        let isLast = selectedPhoto.id == selection.last?.id
                        
                        return content
                            .hueRotation(.degrees(frame.origin.x / 10))
                            .scaleEffect(1 + distance / 700)
                            .offset(x: isLast ? 0 : -distance / 1.25)
                            .brightness(-distance / 400)
                            .blur(radius: isLast ? 0 : -distance / 50)
                            .opacity(isLast ? 1.0 : min(1.0, 1.0 - (-distance / 400)))
                    }
                }
            }
        }
        .configureCarousel(
            viewModel,
            sheetPresented: $sheetPresented
        )
        .sheet(isPresented: $sheetPresented) {
            StickerGrid(viewModel: viewModel)
        }
    }
}
```

[24:31] Now, when SwiftUI calls this closure, it will operate on a copy of selection value,
[24:37] making this operation data-race free.

[24:41] Let’s check out our visual effect!
[24:49] It’s looking great,
[24:50] and I can see how the previous image blurs and fades out as I’m scrolling.

[24:58] In both of these data-race scenarios we’ve encountered,
[25:02] the solution was to not share data that can be mutated from concurrent code.
[25:08] The key difference was that in the first example, I introduced a data-race myself
[25:13] by running some of the code in parallel.
[25:16] In the second example though, I used a SwiftUI API that offloads work
[25:21] to the background thread on my behalf.

[25:25] If you must share mutable state, there are other ways to protect it.
[25:30] Sendable value types prevent the type from being able to be shared by concurrent code.
[25:37] For example, extractSticker and extractColors methods are running in parallel
[25:42] and both take the same image’s data.
[25:45] But there’s no data-race condition in this case because Data is a Sendable value type.
[25:51] Data also implements copy-on-write, so it’s only copied if it’s mutated.
[25:58] If you can’t use a value type, you can consider isolating your state to the main actor.
[26:04] Luckily, the main actor by default mode already does that for you.
[26:09] For example, our model is a class, and we can access it from a concurrent task.
[26:15] Because the model is implicitly marked with the MainActor,
[26:18] it is safe to reference from concurrent code.
[26:21] The code will have to switch to the main actor to access the state.
[26:26] In this case, the class is protected by the main actor
[26:30] but the same applies to other actors that you might have in your code.

[26:15] Accessing a reference type from a concurrent task

```swift
Task { @concurrent in
    await viewModel.loadPhoto(selectedPhoto)      
}
```

[26:36] Our app is looking great so far!
[26:38] But it still doesn’t feel complete.
[26:42] To be able to export the stickers, let’s add a sticker grid view
[26:46] that kicks off a photo processing task for each photo that hasn't been processed yet,
[26:52] and displays all of the stickers at once.
[26:55] It will also have a share button that would allow for export of these stickers.
[27:00] Let’s jump back to the code!
[27:03] First, I’ll use command-click to navigate to the StickerViewModel.

[27:11] I’m going to add another method to our model, `processAllPhotos()`.

[27:22] Here, I want to iterate over all processed photos saved so far in my model,
[27:27] and if there are still unprocessed photos, I want to start multiple parallel tasks
[27:33] to kick off processing for them at once.

[27:37] We’ve used async let before, but that only worked because we knew
[27:41] that there’s only two tasks to kick off —the sticker and color extraction.
[27:46] Now, we need to create a new task for all raw photos in the array, and there can be
[27:52] any amount of these processing tasks.

[27:56] APIs like TaskGroup allow you to take more control over the asynchronous work
[28:01] your app needs to perform.

[28:05] Task groups provide fine grained control over child tasks and their results.
[28:10] The task group allows to kick off any number of child tasks which can be run in parallel.
[28:18] Each child task can take arbitrary amounts of time to finish,
[28:22] so they might be done in a different order.
[28:25] In our case, the processed photos will be saved into a dictionary,
[28:29] so the order doesn't matter.

[28:33] TaskGroup conforms to AsyncSequence, so we can iterate over the results
[28:38] as they’re done to store them into the dictionary.
[28:42] And finally, we can await on the whole group to finish the child tasks.
[28:47] Let's go back to the code to adopt a task group!
[28:51] To adopt the task group, I’ll start by declaring it.

[28:58] Here, inside the closure I have a reference to the group
[29:03] which I can add image processing tasks to.
[29:07] I’m going to iterate over the selection saved in the model.

[29:14] If this photo has been processed, then I don’t need to create a task for it.

[29:22] I’ll start a new task of loading the data and processing the photo.

[29:00] Processing all photos at once with a task group

```swift
func processAllPhotos() async {
    await withTaskGroup { group in
        for item in selection {
            guard processedPhotos[item.id] == nil else { continue }
            group.addTask {
                let data = await self.getData(for: item)
                let photo = await PhotoProcessor().process(data: data)
                return photo.map { ProcessedPhotoResult(id: item.id, processedPhoto: $0) }
            }
        }

        for await result in group {
            if let result {
                processedPhotos[result.id] = result.processedPhoto
            }
        }
    }
}
```

[29:31] Because the group is an async sequence I can iterate over it
[29:35] to save the processed photo
[29:36] into the processedPhotos dictionary once it’s ready.

[29:45] That’s it!
[29:47] Now we are ready to display our stickers in the StickerGrid.
[29:52] I’ll use Open Quickly to navigate to the StickerGrid.

[30:03] Here, I have a state property finishedLoading which indicates
[30:08] if all photos have finished processing.

[30:12] If the photos haven’t been processed yet, a progress view will be displayed.
[30:18] I’m going to call the processAllPhotos() method we just implemented.

[30:00] Kicking off photo processing and configuring the share link in a sticker grid view.

```swift
import SwiftUI

struct StickerGrid: View {
    let viewModel: StickerViewModel
    @State private var finishedLoading: Bool = false

    var body: some View {
        NavigationStack {
            VStack {
                if finishedLoading {
                    GridContent(viewModel: viewModel)
                } else {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .padding()
                }
            }
            .task {
                await viewModel.processAllPhotos()
                finishedLoading = true
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    if finishedLoading {
                        ShareLink("Share", items: viewModel.selection.compactMap {
                            viewModel.processedPhotos[$0.id]?.sticker
                        }) { sticker in
                            SharePreview(
                                "Sticker Preview",
                                image: sticker,
                                icon: Image(systemName: "photo")
                            )
                        }
                    }
                }
            }
            .configureStickerGrid()
        }
    }
}
```

[30:28] After all photos are processed, we can set the state variable.
[30:33] And finally, I will add the share link in the toolbar to share the stickers!
[30:45] I’m populating the share link items with a sticker for each selected photo.
[30:52] Let’s run the app!
[30:56] I will tap on the StickerGrid button.
[30:59] Thanks to the TaskGroup, the preview grid starts processing all photos at once.
[31:04] And when they are ready, I can instantly see all of the stickers!
[31:08] Finally, using the Share button in the toolbar,
[31:11] I can export all of the stickers as files that I can save.

[31:18] In our app, the stickers will be collected in the order they’re done processing.
[31:23] But you can also keep track of the order, and the task group has many more capabilities.
[31:30] To learn more, check out the session “Beyond the basics of structured concurrency”.
[31:36] Congrats!
[31:37] The app is done and now I can save my stickers!
[31:42] We’ve added new features to an app, discovered when they had an impact on the UI,
[31:47] and used concurrency as much as we needed to improve responsiveness and performance.
[31:53] We also learned about structured concurrency and how to prevent data races.
[31:59] If you didn’t follow along, you can still download the final version of the app
[32:04] and make some stickers out of your own photos!
[32:08] To familiarize yourself with new Swift concurrency features and techniques
[32:12] mentioned in this talk,
[32:14] try to optimize or tweak the app further.
[32:18] Finally, see if you could bring these techniques to your app
[32:22] —remember to profile it first!
[32:24] To dive deeper into understanding the concepts in Swift's concurrency model,
[32:29] check out our session “Embracing Swift concurrency”.
[32:33] For migrating your existing project to adopt new approachable concurrency features,
[32:38] check out the "Swift Migration Guide"!
[32:41] And my favorite part, I got some stickers for my notebook!
[32:46] Thanks for watching!

---

## Resources

*   [Code-along: Elevating an app with Swift concurrency](https://developer.apple.com/documentation/Swift/code-along-elevating-an-app-with-swift-concurrency)
*   [Swift Migration Guide](https://www.swift.org/migration/documentation/migrationguide/)
*   [HD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/270/4/fec27360-7913-4e07-8025-e80187a8d00a/downloads/wwdc2025-270_hd.mp4?dl=1)
*   [SD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2025/270/4/fec27360-7913-4e07-8025-e80187a8d00a/downloads/wwdc2025-270_sd.mp4?dl=1)

### Related Videos

#### WWDC25

*   [Embracing Swift concurrency](/videos/play/wwdc2025/268)
*   [Explore concurrency in SwiftUI](/videos/play/wwdc2025/266)

#### WWDC23

*   [Analyze hangs with Instruments](/videos/play/wwdc2023/10248)
*   [Beyond the basics of structured concurrency](/videos/play/wwdc2023/10170)
