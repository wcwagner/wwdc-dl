(Heads up! I’m not 100% sure this is actually the best **introduction**, despite the title. You might want to start [here](/step-by-step-network-request) first instead.)

Recently, someone asked me a question about actor isolation. The specifics aren’t important, but I really got to thinking about it because **of course** they were struggling. Isolation is central to how Swift concurrency works, but it’s a totally new concept.

Despite being new, it actually uses mostly familiar mechanisms. You probably **do** understand a lot about how isolation works, you just don’t **realize** it yet.

Here’s breakdown of the concepts, in the simplest terms I could come up with.

### What even is isolation?

Isolation is the mechanism that Swift uses to make data races impossible. With it, the compiler can reason about how data is accessed and when it can and cannot be done in a guaranteed-safe way. It is also worth noting that this is about accessing mutable state in unsafe ways specifically, not about all kinds of races in general.

### Definitions control isolation

You can **always** look at a definition to understand its isolation.

This is a radical departure from other types of thread-safety mechanisms like locks and queues. I think this is probably the number one thing people using concurrency do not understand.

```swift
// no isolation for the type...
class MyClass {
	// ... and none for the function either
	func method() {
		// so this is a non-isolated context
	}

	func asyncMethod() async {
		// async does not affect this, so 
		// this is non-isolated too!
	}
}
```

Now, looking at a definition isn’t always as straightforward as it sounds. It can involve inheritance if a type has a super-class or conforms to protocols. These are not usually in the same file, or even module, and you may need to consult them to get the full picture. In practice though, outside of UI code, inheritance rarely affects isolation.

```swift
class MyClass: SomeSupertype, SomeProtocol {
	// isolation here might depend on inheritance
	func method() {
	}
}
```

Just remember: isolation is specified at compile time. I’m repeating myself here because it is both **critical** and often a source of confusion.

### Isolation comes in three flavors

*   None
*   Static
*   Dynamic

Everything is **non-isolated** by default. You must take explicit action to change this.

Actor types, global actors, and [isolated parameters](https://www.massicotte.org/isolated-parameters) are all forms of static isolation. Global actors in particular are very common. Many projects, even non-trivial ones, will need nothing more than `@MainActor` isolation for all of its concurrency requirements. Concurrency-heavy library authors may find uses for isolated parameters, but I don’t *think* they will play a major role in day-to-day app development.

(Isolated parameters are also getting [less weird](https://forums.swift.org/t/isolation-assumptions/69514/49) and [more powerful](https://github.com/apple/swift-evolution/blob/main/proposals/0420-inheritance-of-actor-isolation.md) soon!)

We’ll get to dynamic isolation in a minute.

### Isolation can change when you await

Whenever you see an `await` keyword, isolation **could** change.

```swift
@MainActor
func doStuff() async {
	// I'm on the MainActor here!
	await anotherFunction() // have to look at the definition of anotherFunction
	// back on the main actor
}
```

This is another very common source of confusion! But, that’s because with other concurrency systems runtime context is important. Definitions are all that matter in Swift!

### Closures can inherit isolation

This is completely distinct from type inheritance. It **only** applies to closure arguments, and it is usually only found in APIs that directly control concurrency features, like `Task`. Note that we are still following the rules: the isolation behavior is still controlled by the definition. It is done using the [`@_inheritActorContext`](https://github.com/apple/swift/blob/main/docs/ReferenceGuides/UnderscoredAttributes.md#_inheritactorcontext) attribute.

Yes, this is confusing. At first!

All this means is isolation will not suddenly change unless **you** decide you want to change it. Whatever isolation was in effect when you create a `Task` will still be used inside the `Task` body by default. This is very convenient and often exactly what you want. You can also opt out of this, if you want.

```swift
@MainActor
class MyIsolatedClass {
	func myMethod() {
		Task {
		    // still isolated to the MainActor here!
		}

		Task.detached {
			// explicitly non-isolated, regardless
			// the enclosing scope
		}
	}
}
```

### Isolation applies to variables

Functions are not the only thing that can be isolated. Non-local variables can require isolation too.

```swift
@MainActor
class MyIsolatedClass {
	static var value = 1 // this is also MainActor-isolated
}
```

The compiler only started checking this in Swift 5.10, and it surprises a lot of people. But it does make sense. These values can be accessed anywhere in the module, so that needs to be done in a thread-safe way. Explicit isolation is one way to get this safety, but it is definitely not the only way.

### You can opt-out of isolation

If something has isolation that you don’t want, you can opt-out with the `nonisolated` keyword. This also can make a lot of sense for static constants that are immutable and safe to access from other threads.

```swift
@MainActor
class MyIsolatedClass {
	nonisolated func nonIsolatedMethod() {
		// no MainActor isolation here
	}

	nonisolated static let someConstantSTring = "I'm thread-safe!"
}
```

(As we saw above, opting out of isolation for `Task` works a little differently **today**. But, this is an area that is being actively worked on.)

### Isolation makes protocols tricky

Protocols, being definitions, can control isolation just like other kinds of definitions.

```swift
protocol NoIsolation {
	func method()
}

@MainActor
protocol GloballyIsolatedProtocol {
	func method()
}

protocol PerMemberIsolatedProtocol {
	@MainActor
	func method()
}
```

The isolation used by protocols, including none at all, can have **major** implications. This is something to pay particularly close attention to when using concurrency. If you use a lot of protocols in your code, investigating how [complete concurrency checking](https://www.massicotte.org/complete-checking) affects your design is a very good idea.

(I have a [collection of techniques](https://github.com/mattmassicotte/ConcurrencyRecipes/blob/main/Recipes/Protocols.md) for working with protocols and concurrency. But I keep finding new problems! Please let me know if you run into issues I have not covered there.)

### Dynamic Isolation

It can happen that the type system alone does not or cannot describe the isolation actually used. This comes up regularly with systems built before concurrency was a thing. One tool we have to deal with this is **dynamic isolation**. These are APIs that allow us to express isolation in a way that is invisible by just looking at definitions.

```swift
// this delegate will actually always make calls on the MainActor
// but its definition does not express this.
@MainActor
class MyMainActorClass: SomeDelegate {
	nonisolated funcSomeDelegateCallback() {
		// promise the compiler we will be on the
		// MainActor at runtime.
		MainActor.assumeIsolated {
			// access MainActor stuff, including self
		}
	}
}
```

### SwiftUI is very confusing

This isn’t **directly** related to the language isolation system, but it is a practical problem that affects a large number of people. SwiftUI’s isolation model is extremely error-prone, and I’d go so far as to say that it [should be changed](https://www.massicotte.org/swiftui-isolation). Right now, if you see a SwiftUI view that is **not** MainActor-isolated, it’s probably a bug.

Both UIKit and AppKit enforce whole-type `MainActor` isolation, so they are much easier to use in this respect.

(I’ve also got a [few ideas](https://github.com/mattmassicotte/ConcurrencyRecipes/blob/main/Recipes/SwiftUI.md) on how to handle this, but I’d love feedback on this stuff from more experienced SwiftUI users.)

## This is new, not impossible

I think with just a little practice, you can get your head around isolation. And while I think the **concept** is straightforward, actually doing isolation correctly can be incredibly difficult. I hope I have covered enough to help get you started. But, please let me know if there’s something I missed or got wrong. This stuff isn’t easy!

Oh yeah, and since you are here, don’t forget to [turn on the warnings](https://www.massicotte.org/complete-checking) 😉

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
