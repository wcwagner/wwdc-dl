---
title: Incremental Adoption
source: https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/incrementaladoption/
date_crawled: '2025-07-03'
type: tutorial
topics:
- actors
- async-await
- concurrency
- data-race-safety
- migration
- sendable
- swift6
- tasks
---

# Incremental Adoption

Learn how you can introduce Swift concurrency features into your project gradually. This allows you to make incremental progress without disrupting the entire project.

Swift includes a number of language features and standard library APIs to help make incremental adoption easier.

## Wrapping Callback-Based Functions

APIs that accept and invoke a single function on completion are an extremely common pattern in Swift. It’s possible to make a version of such a function that is usable directly from an asynchronous context.

```swift
func updateStyle(backgroundColor: ColorComponents, completionHandler: @escaping () -> Void) {
    // ...
}
```

This is an example of a function that informs a client its work is complete using a callback. There is no way for a caller to determine when or on what thread the callback will be invoked without consulting documentation.

You can wrap this function up into an asynchronous version using *continuations*.

```swift
func updateStyle(backgroundColor: ColorComponents) async {
    await withCheckedContinuation { continuation in
        updateStyle(backgroundColor: backgroundColor) {
            // ... do some work here ...

            continuation.resume()
        }
    }
}
```

> Note: You have to take care to **resume** the continuation **exactly once**. If you miss invoking it, the calling task will remain suspended indefinitely. On the other hand, resuming a checked continuation more than once will cause an expected crash, protecting you from undefined behavior.

With an asynchronous version, there is no longer any ambiguity. After the function has completed, execution will always resume in the same context it was started in.

```swift
await updateStyle(backgroundColor: color)
// style has been updated
```

The `withCheckedContinuation` function is one of a [suite of standard library APIs](https://developer.apple.com/documentation/swift/concurrency#continuations) that exist to make interfacing non-async and async code possible.

> Note: Introducing asynchronous code into a project can surface data isolation checking violations. To understand and address these, see [Crossing Isolation Boundaries](doc://org.swift.migration.6/documentation/Swift-6-Concurrency-Migration-Guide/CommonProblems#Crossing-Isolation-Boundaries).

## Dynamic Isolation

Expressing the isolation of your program statically, using annotations and other language constructs, is both powerful and concise. But it can be difficult to introduce static isolation without updating all dependencies simultaneously.

Dynamic isolation provides runtime mechanisms you can use as a fallback for describing data isolation. It can be an essential tool for interfacing a Swift 6 component with another that has not yet been updated, even if these components are within the *same* module.

### Internal-Only Isolation

Suppose you have determined that a reference type within your project can be best described with `MainActor` static isolation.

```swift
@MainActor
class WindowStyler {
    private var backgroundColor: ColorComponents

    func applyStyle() {
        // ...
    }
}
```

This `MainActor` isolation may be *logically* correct. But if this type is used in other unmigrated locations, adding static isolation here could require many additional changes. An alternative is to use dynamic isolation to help control the scope.

```swift
class WindowStyler {
    @MainActor
    private var backgroundColor: ColorComponents

    func applyStyle() {
        MainActor.assumeIsolated {
            // use and interact with other `MainActor` state
        }
    }
}
```

Here, the isolation has been internalized into the class. This keeps any changes localized to the type, allowing you make changes without affecting any clients of the type.

However, a major disadvantage of this technique is the type’s true isolation requirements remain invisible. There is no way for clients to determine if or how they should change based on this public API. You should use this approach only as a temporary solution, and only when you have exhausted other options.

### Usage-Only Isolation

If it is impractical to contain isolation exclusively within a type, you can instead expand the isolation to cover only its API usage.

To do this, first apply static isolation to the type, and then use dynamic isolation at any usage locations:

```swift
@MainActor
class WindowStyler {
    // ...
}

class UIStyler {
    @MainActor
    private let windowStyler: WindowStyler
    
    func applyStyle() {
        MainActor.assumeIsolated {
            windowStyler.applyStyle()
        }
    }
}
```

Combining static and dynamic isolation can be a powerful tool to keep the scope of changes gradual.

### Explicit MainActor Context

The `assumeIsolated` method is synchronous and exists to recover isolation information from runtime back into the type-system by preventing execution if the assumption was incorrect. The `MainActor` type also has a method you can use to manually switch isolation in an asynchronous context.

```swift
// type that should be MainActor, but has not been updated yet
class PersonalTransportation {
}

await MainActor.run {
    // isolated to the MainActor here
    let transport = PersonalTransportation()
    
    // ...
}
```

Remember that static isolation allows the compiler to both verify and automate the process of switching isolation as needed. Even when used in combination with static isolation, it can be difficult to determine when `MainActor.run` is truly necessary. While `MainActor.run` can be useful during migration, it should not be used as a substitute for expressing the isolation requirements of your system statically. The ultimate goal should still be to apply `@MainActor` to `PersonalTransportation`.

## Missing Annotations

Dynamic isolation gives you tools to express isolation at runtime. But you may also find you need to describe other concurrency properties that are missing from unmigrated modules.

### Unmarked Sendable Closures

The sendability of a closure affects how the compiler infers isolation for its body. A callback closure that actually does cross isolation boundaries but is *missing* a `Sendable` annotation violates a critical invariant of the concurrency system.

```swift
// definition within a pre-Swift 6 module
extension JPKJetPack {
    // Note the lack of a @Sendable annotation
    static func jetPackConfiguration(_ callback: @escaping () -> Void) {
        // Can potentially cross isolation domains
    }
}

@MainActor
class PersonalTransportation {
    func configure() {
        JPKJetPack.jetPackConfiguration {
            // MainActor isolation will be inferred here
            self.applyConfiguration()
        }
    }

    func applyConfiguration() {
    }
}
```

If `jetPackConfiguration` can invoke its closure in another isolation domain, it must be marked `@Sendable`. When an un-migrated module hasn’t yet done this, it will result in incorrect actor inference. This code will compile without issue but crash at runtime.

> Note: It is not possible for the compiler to detect or diagnose the *lack* of compiler-visible information.

To workaround this, you can manually annotate the closure with `@Sendable.` This will prevent the compiler from inferring `MainActor` isolation. Because the compiler now knows actor isolation could change, it will require a task at the callsite and an await in the task.

```swift
@MainActor
class PersonalTransportation {
    func configure() {
        JPKJetPack.jetPackConfiguration { @Sendable in
            // Sendable closures do not infer actor isolation,
            // making this context non-isolated
            Task {
                await self.applyConfiguration()
            }
        }
    }

    func applyConfiguration() {
    }
}
```

Alternatively, it is also possible to disable runtime isolation assertions for the module with the `-disable-dynamic-actor-isolation` compiler flag. This will suppress all runtime enforcement of dynamic actor isolation.

> Warning: This flag should be used with caution. Disabling these runtime checks will permit data isolation violations.

## Integrating DispatchSerialQueue with Actors

By default, the mechanism actors use to schedule and execute work is system-defined. However you can override this to provide a custom implementation. The `DispatchSerialQueue` type includes built-in support for this facility.

```swift
actor LandingSite {
    private let queue = DispatchSerialQueue(label: "something")

    nonisolated var unownedExecutor: UnownedSerialExecutor {
        queue.asUnownedSerialExecutor()
    }

    func acceptTransport(_ transport: PersonalTransportation) {
        // this function will be running on queue
    }
}
```

This can be useful if you want to migrate a type towards the actor model while maintaining compatibility with code that depends on `DispatchQueue`.

## Backwards Compatibility

It’s important to keep in mind that static isolation, being part of the type system, affects your public API. But you can migrate your own modules in a way that improves their APIs for Swift 6 *without* breaking any existing clients.

Suppose the `WindowStyler` is public API. You have determined that it really should be `MainActor`-isolated, but want to ensure backwards compatibility for clients.

```swift
@preconcurrency @MainActor
public class WindowStyler {
    // ...
}
```

Using `@preconcurrency` this way marks the isolation as conditional on the client module also having complete checking enabled. This preserves source compatibility with clients that have not yet begun adopting Swift 6.

## Dependencies

Often, you aren’t in control of the modules you need to import as dependencies. If these modules have not yet adopted Swift 6, you may find yourself with errors that are difficult or impossible to resolve.

There are a number of different kinds of problems that result from using unmigrated code. The `@preconcurrency` annotation can help with many of these situations:

- [Non-Sendable types](doc://org.swift.migration.6/documentation/Swift-6-Concurrency-Migration-Guide/CommonProblems#Non-Sendable-Types)
- Mismatches in [protocol-conformance isolation](doc://org.swift.migration.6/documentation/Swift-6-Concurrency-Migration-Guide/CommonProblems#Protocol-Conformance-Isolation-Mismatch)

## C/Objective-C

You can expose Swift concurrency support for your C and Objective-C APIs using annotations. This is made possible by Clang’s [concurrency-specific annotations](https://clang.llvm.org/docs/AttributeReference.html#customizing-swift-import):

```
__attribute__((swift_attr("@Sendable")))
__attribute__((swift_attr("@_nonSendable")))
__attribute__((swift_attr("nonisolated")))
__attribute__((swift_attr("@UIActor")))
__attribute__((swift_attr("sending")))

__attribute__((swift_async(none)))
__attribute__((swift_async(not_swift_private, COMPLETION_BLOCK_INDEX))
__attribute__((swift_async(swift_private, COMPLETION_BLOCK_INDEX)))
__attribute__((__swift_async_name__(NAME)))
__attribute__((swift_async_error(none)))
__attribute__((__swift_attr__("@_unavailableFromAsync(message: \\"\" msg \"\\\")")))
```

When working with a project that can import Foundation, the following annotation macros are available in `NSObjCRuntime.h`:

```
NS_SWIFT_SENDABLE
NS_SWIFT_NONSENDABLE
NS_SWIFT_NONISOLATED
NS_SWIFT_UI_ACTOR
NS_SWIFT_SENDING

NS_SWIFT_DISABLE_ASYNC
NS_SWIFT_ASYNC(COMPLETION_BLOCK_INDEX)
NS_REFINED_FOR_SWIFT_ASYNC(COMPLETION_BLOCK_INDEX)
NS_SWIFT_ASYNC_NAME
NS_SWIFT_ASYNC_NOTHROW
NS_SWIFT_UNAVAILABLE_FROM_ASYNC(msg)
```

### Dealing with missing isolation annotations in Objective-C libraries

While the SDKs and other Objective-C libraries make progress in adopting Swift concurrency, they will often go through the exercise of codifying contracts which were only explained in documentation. For example, before Swift concurrency, APIs frequently had to document their threading behavior with comments like “this will always be called on the main thread”.

Swift concurrency enables us to turn these code comments, into compiler and runtime enforced isolation checks, that Swift will then verify when you adopt such APIs.

For example, the fictional `NSJetPack` protocol generally invokes all of its delegate methods on the main thread, and therefore has now become MainActor-isolated.

The library author can mark as MainActor isolated using the `NS_SWIFT_UI_ACTOR` attribute, which is equivalent to annotating a type using `@MainActor` in Swift:

```swift
NS_SWIFT_UI_ACTOR
@protocol NSJetPack // fictional protocol
  // ...
@end
```

Thanks to this, all member methods of this protocol inherit the `@MainActor` isolation, and for most methods this is correct.

However, in this example, let us consider a method which was previously documented as follows:

```objc
NS_SWIFT_UI_ACTOR // SDK author annotated using MainActor in recent SDK audit
@protocol NSJetPack // fictional protocol
/* Return YES if this jetpack supports flying at really high altitude!
 
 JetPackKit invokes this method at a variety of times, and not always on the main thread. For example, ...
*/
@property(readonly) BOOL supportsHighAltitude;

@end
```

This method’s isolation was accidentally inferred as `@MainActor`, because of the annotation on the enclosing type. Although it has specifically documented a different threading strategy - it may or may not be invoked on the main actor - annotating these semantics on the method was accidentally missed.

This is an annotation problem in the fictional JetPackKit library. Specifically, it is missing a `nonisolated` annotation on the method, which would inform Swift about the correct and expected execution semantics.

Swift code adopting this library may look like this:

```swift
@MainActor
final class MyJetPack: NSJetPack {
  override class var supportsHighAltitude: Bool { // runtime crash in Swift 6 mode
    true
  }
}
```

The above code will crash with a runtime check, which aims to ensure we are actually executing on the main actor as we’re crossing from objective-c’s non-swift-concurrency land into Swift.

It is a Swift 6 feature to detect such issues automatically and crash at runtime when such expectations are violated. Leaving such issues un-diagnosed, could lead to actual hard-to-detect data races, and undermine Swift 6’s promise about data-race safety.

Such failure would include a similar backtrace to this:

```
* thread #5, queue = 'com.apple.root.default-qos', stop reason = EXC_BREAKPOINT (code=1, subcode=0x1004f8a5c)
  * frame #0: 0x00000001004..... libdispatch.dylib`_dispatch_assert_queue_fail + 120
    frame #1: 0x00000001004..... libdispatch.dylib`dispatch_assert_queue + 196
    frame #2: 0x0000000275b..... libswift_Concurrency.dylib`swift_task_isCurrentExecutorImpl(swift::SerialExecutorRef) + 280
    frame #3: 0x0000000275b..... libswift_Concurrency.dylib`Swift._checkExpectedExecutor(_filenameStart: Builtin.RawPointer, _filenameLength: Builtin.Word, _filenameIsASCII: Builtin.Int1, _line: Builtin.Word, _executor: Builtin.Executor) -> () + 60
    frame #4: 0x00000001089..... MyApp.debug.dylib`@objc static JetPack.supportsHighAltitude.getter at <compiler-generated>:0
    ...
    frame #10: 0x00000001005..... libdispatch.dylib`_dispatch_root_queue_drain + 404
    frame #11: 0x00000001005..... libdispatch.dylib`_dispatch_worker_thread2 + 188
    frame #12: 0x00000001005..... libsystem_pthread.dylib`_pthread_wqthread + 228
```

> Note: When encountering such an issue, and by investigating the documentation and API annotations you determine something was incorrectly annotated, the best way to resolve the root cause of the problem is to report the issue back to the library maintainer.

As you can see, the runtime injected an executor check into the call, and the dispatch queue assertion (of it running on the MainActor), has failed. This prevents sneaky and hard to debug data-races.

The correct long-term solution to this issue is the library fixing the method’s annotation, by marking it as `nonisolated`:

```objc
// Solution in the library providing the API:
@property(readonly) BOOL supportsHighAltitude NS_SWIFT_NONISOLATED;
```

Until the library fixes its annotation issue, you are able to witness the method using a correctly `nonisolated` method, like this:

```swift
// Solution in adopting client code, wishing to run in Swift 6 mode:
@MainActor
final class MyJetPack: NSJetPack {
  // Correct
  override nonisolated class var supportsHighAltitude: Bool {
    true
  }
}
```

This way Swift knows not to check for the not-correct assumption that the method requires main actor isolation.

