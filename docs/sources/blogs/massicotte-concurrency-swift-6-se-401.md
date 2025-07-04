# SE-0401: Remove Actor Isolation Inference caused by Property Wrappers
Apr 9, 2024

With Swift 5.10, the compiler can correctly find all possible sources of data races. But, there are still quite a few sharp edges and usability issues with concurrency. Swift 6 is going to come with **many** language changes that will help. In fact, there are currently 13 evolution proposals and 4 pitches that are either directly or indirectly related to concurrency. That’s a lot!

The thing is, I often find it quite challenging to read these proposals. It can be really difficult for me to go from the abstract language changes to how them will impact concrete problems I’ve faced. Honestly, sometimes I don’t even fully get the language changes! But, I’m not going to let that stop me 😬

So, I’m going to make an attempt to cover all of the *accepted* evolution proposals. I’m not going to go too deep. Just a little introduction to the problem and a few examples to highlights the syntax changes. Of course, I’ll also throw in a little commentary. Each of these proposals probably deserves its own in-depth post. But, I’m getting tired just thinking about that.

Index:

*   SE-0401: Remove Actor Isolation Inference caused by Property Wrappers
*   [SE-0411: Isolated default value expressions](concurrency-swift-6-se-411)
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

Here’s an example from the [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0401-remove-property-wrapper-isolation.md):

```swift
struct MyView: View {
	// Note that `StateObject` has a MainActor-isolated `wrappedValue`
	@StateObject private var model = Model()
	
	var body: some View {
		Text("Hello, \(model.name)")
			.onAppear { viewAppeared() }
	}
	
	// This function is inferred to be `@MainActor`
	func viewAppeared() {
		updateUI()
	}
}

@MainActor func updateUI() { /* do stuff here */ }
```

The really important thing to note is this `View` is non-isolated. This should be setting off [alarm bells](swiftui-isolation)! And yet, somehow `viewAppeared` really is becoming `MainActor`-isolated?

Before this proposal, property wrappers could change the isolation of their enclosing type. This is **really** weird! It’s also very hard to predict how it will affect your code. Changing that `StateObject` to a `State` will introduce an isolation **error** in `viewAppeared`.

This is incredibly confusing.

# The Solution

Property wrappers will just stop doing this! Pretty simple.

# The Implications

As it turns out, this behavior also happens to make a lot of otherwise-incorrect SwiftUI code work right. This non-obvious, implicit behavior is masking a real isolation issue. I’m sure there is some SwiftUI code out there using concurrency that is **accidentally correct** today because of this.

The proposal authors did a pretty amazing job of trying to determine how problematic this would be. It didn’t seem like a disaster, but they were at least worried enough that this change, which actually shipped with Swift 5.9, is opt-in. You have to turn it on with the upcoming feature flag: `DisableOutwardActorInference`.

I would absolutely recommend [enabling](https://www.swift.org/blog/using-upcoming-feature-flags/) this one if you are already using complete checking. I think it’s probably a good idea even if you aren’t.

# Will it Affect Me?

Code that is already complete-checking clean will probably be ok. But, this could be a major source of confusion for SwiftUI users that aren’t familiar with isolation. Even if you are, the behavior is so surprising it could catch you off-guard.

---

<span>[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.</span>
