# SE-0411: Isolated default value expressions
Apr 16, 2024

In my [first post](concurrency-swift-6-se-401) in this series, I said that Swift 5.10 can correctly find all possible sources of data races. But, I kind of lied! It turns out there is actually a pretty significant isolation hole in that version. But it gets a little more complicated, which I’ll get to.

Index:

*   [SE-0401: Remove Actor Isolation Inference caused by Property Wrappers](concurrency-swift-6-se-401)
*   SE-0411: Isolated default value expressions
*   [SE-0414: Region based Isolation](concurrency-swift-6-se-0414)
*   [SE-0417: Task Executor Preference](concurrency-swift-6-se-0417)
*   [SE-0418: Inferring Sendable for methods and key path literals](concurrency-swift-6-se-0418)
*   [SE-0420: Inheritance of actor isolation](concurrency-swift-6-se-0420)
*   [SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol](concurrency-swift-6-se-0421)
*   [SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts](concurrency-swift-6-se-0423)
*   [SE-0424: Custom isolation checking for SerialExecutor](concurrency-swift-6-se-0424)
*   [SE-0430:`sending` parameter and result values](concurrency-swift-6-se-0430)
*   [SE-0431: `@isolated(any)` Function Types](concurrency-swift-6-se-0431)
*   [SE-0434: Usability of global-actor-isolated types](concurrency-swift-6-se-0434)

# The Problem

There are two issues with default value expressions in Swift 5.10. The first is that default arguments are overly-restrictive. This code, from the [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0411-isolated-default-values.md), makes sense and is in fact safe. But the compiler will not allow it.

```swift
@MainActor class C {}

@MainActor func f(c: C = C()) {} // error: Call to main actor-isolated initializer 'init()' in a synchronous nonisolated context

@MainActor func useFromMainActor() {
	f()
}
```

All this stuff is MainActor, so there’s no actual issue here. I have run into this problem myself.

The second problem is related to stored properties of types. This one actually can result in incorrect isolation. Again, adapted from the proposal:

```swift
@MainActor func requiresMainActor() -> Int { ... }

class C {
	@MainActor var x1 = requiresMainActor()
	
	init() {
		// but we aren't on the MainActor here???
	}
}
```

I think it is *probably* not common usage pattern. I imagine it is rare to have a type with properties that use different global actors. Regardless of how wide-spread this is, I’m really happy to see the problem is being addressed.

# The Solution

This is another case where the proposal’s solution is very straightforward. The compiler is now just going to do the right thing. For function arguments, this is going to make code that should work warning/error-free.

What the right thing actually is, in the case of mixed-global actor initializers, is slightly weird. The compiler will only allow default initializers to run in init methods that match their actor isolation. This makes sense, but makes the following situation possible:

```swift
@MainActor func requiresMainActor() -> Int { ... }

class C {
	@MainActor var x1 = requiresMainActor()

	init() {
		// ERROR: 'self.x1' is not initialized
	}
}
```

The compiler warning doesn’t include information on **why** the value isn’t initialized, and that could be confusing. But, I still think this is a reasonable solution to what I hope is an unusual arrangement.

# The Implications

This proposal really just makes stuff work like it should. This could break currently-unsafe code, but that is exactly what Swift concurrency is supposed to do.

# Will it Affect Me?

While writing this, I was experimenting with some code to show off a few different example of issues. But, no matter how hard I tried, I was unable to reproduce these warnings/errors. I was mystified, because I was using the example code from the proposal. I also remembered a spot in my own code where this was a problem.

Well! It turns out that with Swift 5.10, turning on complete concurrency checking has the side-effect of also enabling this feature. This was **not** the case for Swift 5.9. So, it’s possible you already have this feature enabled and don’t even know it.

I think you could make the case that turning this on *without* using complete checking makes sense. It could catch a bug, and can get you past some compiler errors when introducing actor annotations. Maaaaybe.

Most likely you can just ignore this one and enjoy the additional safety.

---
[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
