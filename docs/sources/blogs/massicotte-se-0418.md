```markdown
# SE-0418: Inferring Sendable for methods and key path literals

May 3, 2024

This is a [dense proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0418-inferring-sendable-for-methods.md), covering a lot of tricky stuff around the relationships between functions, key paths, and sendability. I’m going to go out on a limb here and say that the changes here won’t affect the majority of Swift users. However, the changes are still welcome!

Index:

*   [SE-0401: Remove Actor Isolation Inference caused by Property Wrappers](concurrency-swift-6-se-401)
*   [SE-0411: Isolated default value expressions](concurrency-swift-6-se-411)
*   [SE-0414: Region based Isolation](concurrency-swift-6-se-0414)
*   [SE-0417: Task Executor Preference](concurrency-swift-6-se-0417)
*   SE-0418: Inferring Sendable for methods and key path literals
*   [SE-0420: Inheritance of actor isolation](concurrency-swift-6-se-0420)
*   [SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol](concurrency-swift-6-se-0421)
*   [SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts](concurrency-swift-6-se-0423)
*   [SE-0424: Custom isolation checking for SerialExecutor](concurrency-swift-6-se-0424)
*   [SE-0430:`sending` parameter and result values](concurrency-swift-6-se-0430)
*   [SE-0431: `@isolated(any)` Function Types](concurrency-swift-6-se-0431)
*   [SE-0434: Usability of global-actor-isolated types](concurrency-swift-6-se-0434)

# The Problem

The first part of this proposal addresses an annoying loss of sendability around so-called unapplied functions. Here’s the idea:

```swift
struct SendableType: Sendable {
	func someMethod() { }
}

func test() {
	let value = SendableType()
	
	// WARNING: Converting non-sendable function value to
	// '@Sendable () async -> Void' may introduce data races
	Task<Void, Never>(operation: value.someMethod)
}
```

This warning doesn’t make sense - everything here is Sendable and should be allowed.

The second problem is related to key path literals. I’m just going to steal the example right from the proposal, because it’s complex.

```swift
class Info: Hashable {
	// some information about the user
}

struct Entry {}

struct User {
	public subscript(info: Info) -> Entry {
		// find entry based on the given info
	}
}

// WARNING: Cannot form key path that captures non-sendable type 'Info'
let entry: KeyPath<User, Entry> = \.[Info()]
```

The issue here is that key path literals, the `\.[Info()]` in this case, must always capture only `Sendable` types. Since `Info` is not `Sendable`, this cannot be done warning-free.

# The Solution

In the case of unapplied functions, the compiler is now just going to chill out. It will assume that functions of Sendable types are also themselves Sendable. Very reasonable fix.

The key path changes are more involved and have some subtlety to them. But, the upshot is that the sendability of the key paths will match the types involved. Sendable types => Sendable key path. Non-Sendable types => non-Sendable key path. A very natural solution.

# The Implications

I think this is just an example of cleaning up some loose ends. Once you see this proposal, it kinda becomes surprising things weren’t **already** working this way.

# Will it Affect Me?

If you were applying `@Sendable` to functions, which I have seen, you might run into problems here. But you were probably only doing that to workaround the issues this proposal fixes. So, yes, it could potentially impact your code, but the fix is straightforward and just makes it simpler.

I **think** the key path changes will only affect you if you have some fairly advanced concurrency/key path usage. And, I have no doubt those people exist. This will make stuff just work!

Overall, two thumbs up! This proposal just makes concurrency better.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing.
I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
```
