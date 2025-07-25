---
title: Data Race Safety
source: https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/dataracesafety/
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

# Data Race Safety

Learn about the fundamental concepts Swift uses to enable data-race-free concurrent code.

Traditionally, mutable state had to be manually protected via careful runtime synchronization. Using tools such as locks and queues, the prevention of data races was entirely up to the programmer. This is notoriously difficult not just to do correctly, but also to keep correct over time. Even determining the *need* for synchronization may be challenging. Worst of all, unsafe code does not guarantee failure at runtime. This code can often seem to work, possibly because highly unusual conditions are required to exhibit the incorrect and unpredictable behavior characteristic of a data race.

More formally, a data race occurs when one thread accesses memory while the same memory is being mutated by another thread. The Swift 6 language mode eliminates these problems by preventing data races at compile time.

> **Important**
> 
> You may have encountered constructs like `async`/`await` and actors in other languages. Pay extra attention, as similarities to these concepts in Swift may only be superficial.

## Data Isolation

Swift's concurrency system allows the compiler to understand and verify the safety of all mutable state. It does this with a mechanism called *data isolation*. Data isolation guarantees mutually exclusive access to mutable state. It is a form of synchronization, conceptually similar to a lock. But unlike a lock, the protection data isolation provides happens at compile-time.

A Swift programmer interacts with data isolation in two ways: statically and dynamically.

The term *static* is used to describe program elements that are unaffected by runtime state. These elements, such as a function definition, are made up of keywords and annotations. Swift's concurrency system is an extension of its type system. When you declare functions and types, you are doing so statically. Isolation can be a part of these static declarations.

There are cases, however, where the type system alone cannot sufficiently describe runtime behavior. An example could be an Objective-C type that has been exposed to Swift. This declaration, made outside of Swift code, may not provide enough information to the compiler to ensure safe usage. To accommodate these situations, there are additional features that allow you to express isolation requirements dynamically.

Data isolation, be it static or dynamic, allows the compiler to guarantee Swift code you write is free of data races.

> **Note**
> 
> For more information about using dynamic isolation, see [Dynamic Isolation](https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/incrementaladoption#Dynamic-Isolation).

### Isolation Domains

Data isolation is the *mechanism* used to protect shared mutable state. But it is often useful to talk about an independent unit of isolation. This is known as an *isolation domain*. How much state a particular domain is responsible for protecting varies widely. An isolation domain might protect a single variable, or an entire subsystem, such as a user interface.

The critical feature of an isolation domain is the safety it provides. Mutable state can only be accessed from one isolation domain at a time. You can pass mutable state from one isolation domain to another, but you can never access that state concurrently from a different domain. This guarantee is validated by the compiler.

Even if you have not explicitly defined it yourself, *all* function and variable declarations have a well-defined static isolation domain. These domains will always fall into one of three categories:

- Non-isolated
- Isolated to an actor value
- Isolated to a global actor

### Non-isolated

Functions and variables do not have to be a part of an explicit isolation domain. In fact, a lack of isolation is the default, called *non-isolated*. Because all the data isolation rules apply, there is no way for non-isolated code to mutate state protected in another domain.

```swift
func sailTheSea() {
}
```

This top-level function has no static isolation, making it non-isolated. It can safely call other non-isolated functions, and access non-isolated variables, but it cannot access anything from another isolation domain.

```swift
class Chicken {
    let name: String
    var currentHunger: HungerLevel
}
```

This is an example of a non-isolated type. Inheritance can play a role in static isolation. But this simple class, with no superclass or protocol conformances, also uses the default isolation.

Data isolation guarantees that non-isolated entities cannot access the mutable state of other domains. As a result of this, non-isolated functions and variables are always safe to access from any other domain.

### Actors

Actors give the programmer a way to define an isolation domain, along with methods that operate within that domain. All stored properties of an actor are isolated to the enclosing actor instance.

```swift
actor Island {
    var flock: [Chicken]
    var food: [Pineapple]
    
    func addToFlock() {
        flock.append(Chicken())
    }
}
```

Here, every `Island` instance will define a new domain, which will be used to protect access to its properties. The method `Island.addToFlock` is said to be isolated to `self`. The body of a method has access to all data that shares its isolation domain, making the `flock` property synchronously accessible.

Actor isolation can be selectively disabled. This can be useful any time you want to keep code organized within an isolated type, but opt-out of the isolation requirements that go along with it. Non-isolated methods cannot synchronously access any protected state.

```swift
actor Island {
    var flock: [Chicken]
    var food: [Pineapple]
    
    nonisolated func canGrow() -> PlantSpecies {
        // neither flock nor food are accessible here
    }
}
```

The isolation domain of an actor is not limited to its own methods. Functions that accept an isolated parameter can also gain access to actor-isolated state without the need for any other form of synchronization.

```swift
func addToFlock(of island: isolated Island) {
    island.flock.append(Chicken())
}
```

> **Note**
> 
> For an overview of actors, please see the [Actors](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency#Actors) section of The Swift Programming Language.

### Global Actors

Global actors share all of the properties of regular actors, but also provide a means of statically assigning declarations to their isolation domain. This is done with an annotation matching the actor name. Global actors are particularly useful when groups of types all need to interoperate as a single pool of shared mutable state.

```swift
@MainActor
class ChickenValley {
    var flock: [Chicken]
    var food: [Pineapple]
}
```

This class is statically-isolated to `MainActor`. This ensures that all access to its mutable state is done from that isolation domain.

You can opt-out of this type of actor isolation as well, using the `nonisolated` keyword. And just as with actor types, doing so will disallow access to any protected state.

```swift
@MainActor
class ChickenValley {
    var flock: [Chicken]
    var food: [Pineapple]
    
    nonisolated func canGrow() -> PlantSpecies {
        // neither flock, food, nor any other MainActor-isolated
        // state is accessible here
    }
}
```

### Tasks

A `task` is a unit of work that can run concurrently within your program. You cannot run concurrent code in Swift outside of a task, but that doesn't mean you must always manually start one. Typically, asynchronous functions do not need to be aware of the task running them. In fact, tasks can often begin at a much higher level, within an application framework, or even at the entry point of the program.

Tasks may run concurrently with one another, but each individual task only executes one function at a time. They run code in order, from beginning to end.

```swift
Task {
    flock.map(Chicken.produce)
}
```

A task always has an isolation domain. They can be isolated to an actor instance, a global actor, or could be non-isolated. This isolation can be established manually, but can also be inherited automatically based on context. Task isolation, just like all other Swift code, determines what mutable state is accessible.

Tasks can run both synchronous and asynchronous code. Regardless of the structure and how many tasks are involved, functions in the same isolation domain cannot run concurrently with each other. There will only ever be one task running synchronous code for any given isolation domain.

> **Note**
> 
> For more information see the [Tasks](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency#Tasks-and-Task-Groups) section of The Swift Programming Language.

### Isolation Inference and Inheritance

There are many ways to specify isolation explicitly. But there are cases where the context of a declaration establishes isolation implicitly, via *isolation inference*.

#### Classes

A subclass will always have the same isolation as its parent.

```swift
@MainActor
class Animal {
}

class Chicken: Animal {
}
```

Because `Chicken` inherits from `Animal`, the static isolation of the `Animal` type also implicitly applies. Not only that, it also cannot be changed by a subclass. All `Animal` instances have been declared to be `MainActor`-isolated, which means all `Chicken` instances must be as well.

The static isolation of a type will also be inferred for its properties and methods by default.

```swift
@MainActor
class Animal {
    // all declarations within this type are also
    // implicitly MainActor-isolated
    let name: String
    
    func eat(food: Pineapple) {
    }
}
```

> **Note**
> 
> For more information, see the [Inheritance](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/inheritance) section of The Swift Programming Language.

#### Protocols

A protocol conformance can implicitly affect isolation. However, the protocol's effect on isolation depends on how the conformance is applied.

```swift
@MainActor
protocol Feedable {
    func eat(food: Pineapple)
}

// inferred isolation applies to the entire type
class Chicken: Feedable {
}

// inferred isolation only applies within the extension
extension Pirate: Feedable {
}
```

A protocol's requirements themselves can also be isolated. This allows more fine-grained control around how isolation is inferred for conforming types.

```swift
protocol Feedable {
    @MainActor
    func eat(food: Pineapple)
}
```

Regardless of how a protocol is defined and conformance added, you cannot alter other mechanisms of static isolation. If a type is globally-isolated, either explicitly or via inference from a superclass, a protocol conformance cannot be used to change it.

> **Note**
> 
> For more information, see the [Protocols](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols) section of The Swift Programming Language.

#### Function Types

Isolation *inference* allows a type to implicitly define the isolation of its properties and methods. But these are all examples of *declarations*. It is also possible to achieve a similar effect with function values, through isolation *inheritance*.

By default, closures are isolated to the same context they're formed in. For example:

```swift
@MainActor
class Model { ... }

@MainActor
class C {
    var models: [Model] = []
    
    func mapModels<Value>(
        _ keyPath: KeyPath<Model, Value>
    ) -> some Collection<Value> {
        models.lazy.map { $0[keyPath: keyPath] }
    }
}
```

In the above code, the closure to `LazySequence.map` has type `@escaping (Base.Element) -> U`. This closure must stay on the main actor where it was originally formed. This allows the closure to capture state or call isolated methods from the surrounding context.

Closures that can run concurrently with the original context are marked explicitly through `@Sendable` and `sending` annotations described in later sections.

For `async` closures that may be evaluated concurrently, the closure can still capture the isolation of the original context. This mechanism is used by the `Task` initializer so that the given operation is isolated to the original context by default, while still allowing explicit isolation to be specified:

```swift
@MainActor
func eat(food: Pineapple) {
    // the static isolation of this function's declaration is
    // captured by the closure created here
    Task {
        // allowing the closure's body to inherit MainActor-isolation
        Chicken.prizedHen.eat(food: food)
    }
    
    Task { @MyGlobalActor in
        // this task is isolated to `MyGlobalActor`
    }
}
```

The closure's type here is defined by `Task.init`. Despite that declaration not being isolated to any actor, this newly-created task will *inherit* the `MainActor` isolation of its enclosing scope unless an explicit global actor is written. Function types offer a number of mechanisms for controlling their isolation behavior, but by default they behave identically to other types.

> **Note**
> 
> For more information, see the [Closures](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/closures) section of The Swift Programming Language.

## Isolation Boundaries

Isolation domains protect their mutable state, but useful programs need more than just protection. They have to communicate and coordinate, often by passing data back and forth. Moving values into or out of an isolation domain is known as *crossing* an isolation boundary. Values are only ever permitted to cross an isolation boundary where there is no potential for concurrent access to shared mutable state.

Values can cross boundaries directly, via asynchronous function calls. When you call an asynchronous function with a *different* isolation domain, the parameters and return value need to move into that domain. Values can also cross boundaries indirectly when captured by closures. Closures introduce many potential opportunities for concurrent accesses. They can be created in one domain and then executed in another. They can even be executed in multiple, different domains.

### Sendable Types

In some cases, all values of a particular type are safe to pass across isolation boundaries because thread-safety is a property of the type itself. This is represented by the `Sendable` protocol. A conformance to `Sendable` means the given type is thread safe, and values of the type can be shared across arbitrary isolation domains without introducing a risk of data races.

Swift encourages using value types because they are naturally safe. With value types, different parts of your program can't have shared references to the same value. When you pass an instance of a value type to a function, the function has its own independent copy of that value. Because value semantics guarantees the absence of shared mutable state, value types in Swift are implicitly `Sendable` when all their stored properties are also Sendable. However, this implicit conformance is not visible outside of their defining module. Making a type `Sendable` is part of its public API contract and must always be done explicitly.

```swift
enum Ripeness {
    case hard
    case perfect
    case mushy(daysPast: Int)
}

struct Pineapple {
    var weight: Double
    var ripeness: Ripeness
}
```

Here, both the `Ripeness` and `Pineapple` types are implicitly `Sendable`, since they are composed entirely of `Sendable` value types.

> **Note**
> 
> For more information see the [Sendable Types](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency#Sendable-Types) section of The Swift Programming Language.

#### Flow-Sensitive Isolation Analysis

The `Sendable` protocol is used to express thread-safety for a type as a whole. But there are situations when a particular *instance* of a non-`Sendable` type is being used in a safe way. The compiler is often capable of inferring this safety through flow-sensitive analysis known as [region-based isolation](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0414-region-based-isolation.md).

Region-based isolation allows the compiler to permit instances of non-`Sendable` types to cross isolation domains when it can prove doing so cannot introduce data races.

```swift
func populate(island: Island) async {
    let chicken = Chicken()
    
    await island.adopt(chicken)
}
```

Here, the compiler can correctly reason that even though `chicken` has a non-`Sendable` type, allowing it to cross into the `island` isolation domain is safe. However, this exception to `Sendable` checking is inherently contigent on the surrounding code. The compiler will still produce an error should any unsafe accesses to the `chicken` variable ever be introduced.

```swift
func populate(island: Island) async {
    let chicken = Chicken()
    
    await island.adopt(chicken)
    
    // this would result in an error
    chicken.eat(food: Pineapple())
}
```

Region-based isolation works without any code changes. But a function's parameters and return values can also explicitly state that they support crossing domains using this mechanism.

```swift
func populate(island: Island, with chicken: sending Chicken) async {
    await island.adopt(chicken)
}
```

The compiler can now provide the guarantee that at all call sites, the `chicken` parameter will never be subject to unsafe access. This is a relaxing of an otherwise significant constraint. Without `sending`, this function would only be possible to implement by requiring that `Chicken` first conform to `Sendable`.

### Actor-Isolated Types

Actors are not value types, but because they protect all of their state in their own isolation domain, they are inherently safe to pass across boundaries. This makes all actor types implicitly `Sendable`, even if their properties are not `Sendable` themselves.

```swift
actor Island {
    var flock: [Chicken] // non-Sendable
    var food: [Pineapple] // Sendable
}
```

Global-actor-isolated types are also implicitly `Sendable` for similar reasons. They do not have a private, dedicated isolation domain, but their state is still protected by an actor.

```swift
@MainActor
class ChickenValley {
    var flock: [Chicken] // non-Sendable
    var food: [Pineapple] // Sendable
}
```

### Reference Types

Unlike value types, reference types cannot be implicitly `Sendable`. And while they can be made `Sendable`, doing so comes with a number of constraints. To make a class `Sendable` it must contain no mutable state and all immutable properties must also be `Sendable`. Further, the compiler can only validate the implementation of final classes.

```swift
final class Chicken: Sendable {
    let name: String
}
```

It is possible to satisfy the thread-safety requirements of `Sendable` using synchronization primitives that the compiler cannot reason about, such as through OS-specific constructs or when working with thread-safe types implemented in C/C++/Objective-C. Such types may be marked as conforming to `@unchecked Sendable` to promise the compiler that the type is thread-safe. The compiler will not perform any checking on an `@unchecked Sendable` type, so this opt-out must be used with caution.

### Suspension Points

A task can switch between isolation domains when a function in one domain calls a function in another. A call that crosses an isolation boundary must be made asynchronously, because the destination isolation domain might be busy running other tasks. In that case, the task will be suspended until the destination isolation domain is available. Critically, a suspension point does *not* block. The current isolation domain (and the thread it is running on) are freed up to perform other work. The Swift concurrency runtime expects code to never block on future work, allowing the system to always make forward progress. This eliminates a common source of deadlocks in concurrent code.

```swift
@MainActor
func stockUp() {
    // beginning execution on MainActor
    let food = Pineapple()
    
    // switching to the island actor's domain
    await island.store(food)
}
```

Potential suspension points are marked in source code with the `await` keyword. Its presence indicates that the call might suspend at runtime, but `await` does not force a suspension. The function being called might suspend only under certain dynamic conditions. It's possible that a call marked with `await` will not actually suspend.

### Atomicity

While actors do guarantee safety from data races, they do not ensure atomicity across suspension points. Concurrent code often needs to execute a sequence of operations together as an atomic unit, such that other threads can never see an intermediate state. Units of code that require this property are known as *critical sections*.

Because the current isolation domain is freed up to perform other work, actor-isolated state may change after an asynchronous call. As a consequence, you can think of explicitly marking potential suspension points as a way to indicate the end of a critical section.

```swift
func deposit(pineapples: [Pineapple], onto island: Island) async {
    var food = await island.food
    food += pineapples
    await island.store(food)
}
```

This code assumes, incorrectly, that the `island` actor's `food` value will not change between asynchronous calls. Critical sections should always be structured to run synchronously.

> **Note**
> 
> For more information, see the [Defining and Calling Asynchronous Functions](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/#Defining-and-Calling-Asynchronous-Functions) section of The Swift Programming Language.