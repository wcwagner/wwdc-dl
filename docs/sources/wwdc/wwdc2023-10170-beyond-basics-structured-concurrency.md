---
session: 10170
year: 2023
title: Beyond the basics of structured concurrency
presenters: []
duration: 24
---

## About

It's all about the task tree: Find out how structured concurrency can help your apps manage automatic task cancellation, task priority propagation, and useful task-local value patterns. Learn how to manage resources in your app with useful patterns and the latest task group APIs. We'll show you how you can leverage the power of the task tree and task-local values to gain insight into distributed systems.

Before watching, review the basics of Swift Concurrency and structured concurrency by checking out “Swift concurrency: Behind the scenes” and “Explore structured concurrency in Swift” from WWDC21.

## Chapters

*   [00:56] - Structured concurrency
*   [03:11] - Task tree
*   [03:44] - Task cancellation
*   [05:26] - withTaskCancellationHandler
*   [08:36] - Task priority
*   [10:23] - Patterns with task groups
*   [11:27] - Limiting concurrent tasks in TaskGroups
*   [12:22] - DiscardingTaskGroup
*   [13:53] - Task-local values
*   [16:58] - swift-log
*   [17:19] - MetadataProvider
*   [18:58] - Task traces
*   [19:46] - Swift-Distributed-Tracing
*   [20:42] - Instrumenting distributed computations
*   [23:38] - Wrap-up

## Resources

*   [Swift Distributed Tracing - Repository](https://github.com/apple/swift-distributed-tracing)
*   [HD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2023/10170/5/4608ED1F-4D83-4444-83A0-DF3EACCE4369/downloads/wwdc2023-10170_hd.mp4?dl=1)
*   [SD Video](https://devstreaming-cdn.apple.com/videos/wwdc/2023/10170/5/4608ED1F-4D83-4444-83A0-DF3EACCE4369/downloads/wwdc2023-10170_sd.mp4?dl=1)

## Related Videos

#### WWDC23

*   [What’s new in Swift](/videos/play/wwdc2023/10164)

#### WWDC22

*   [Visualize and optimize Swift concurrency](/videos/play/wwdc2022/110350)

#### WWDC21

*   [Analyze HTTP traffic in Instruments ](/videos/play/wwdc2021/10212)
*   [Explore structured concurrency in Swift](/videos/play/wwdc2021/10134)
*   [Swift concurrency: Behind the scenes](/videos/play/wwdc2021/10254)

## Transcript

[00:01] ♪ ♪
[00:10] Evan: Hi, my name is Evan.
[00:12] Today, we are going beyond the basics of structured concurrency,
[00:15] exploring how structured tasks can simplify realizing useful behaviors.
[00:20] Before we get started, if you're new or want to review structured concurrency,
[00:24] feel free to watch the "Explore structured concurrency in Swift"
[00:27] and "Swift concurrency: Behind the scenes" sessions from WWDC 2021.

[00:33] Today, we will review the task hierarchy,
[00:36] and how it unlocks automatic task cancellation,
[00:39] priority propagation, and useful task-local value behaviors.

[00:44] Then we will cover some patterns with task groups
[00:46] to help manage resource usage.

[00:48] Finally, we'll look at how all of these come together
[00:51] to facilitate profiling and tracing tasks in a server environment.

[00:56] Structured concurrency enables you to reason about concurrent code
[01:00] using well-defined points where execution branches off and runs concurrently,
[01:04] and where results from that execution rejoin,
[01:07] similar to how "if"-blocks and "for"-loops define how control-flow behaves
[01:11] in synchronous code.
[01:13] Concurrent execution is triggered when you use an "async let",
[01:16] a task group, or create a task or detached task.

[01:20] Results rejoin the current execution at a suspension point,
[01:23] indicated by an "await".

[01:26] Not all tasks are structured.

[01:28] Structured tasks are created using "async let" and task groups,
[01:32] while unstructured tasks are created using Task and Task.detached.
[01:37] Structured tasks live to the end of the scope where they are declared,
[01:40] like local variables, and are automatically cancelled
[01:43] when they go out of scope,
[01:44] making it clear how long the task will live.

[01:48] Whenever possible, prefer structured Tasks.
[01:51] The benefits of structured concurrency discussed later
[01:53] do not always apply to unstructured tasks.

[01:57] Before we dive into the code, let's come up with a concrete example.

[02:02] Suppose we have a kitchen with multiple chefs preparing soup.
[02:05] Soup preparation consists of multiple steps.

[02:08] The chefs have to cut ingredients, marinate chicken,
[02:11] bring the broth to a boil, and finally, cook the soup before it is ready to serve.
[02:16] Some tasks can be performed in parallel,
[02:18] while others must be done in a specific order.

[02:21] Let's see how we can express this in code.

[02:24] For now, we'll focus on the makeSoup function.

[02:28] You may find yourself creating unstructured Tasks
[02:31] to add concurrency to your functions, and awaiting their values when necessary.

```swift
func makeSoup(order: Order) async throws -> Soup {
    let boilingPot = Task { try await stove.boilBroth() }
    let choppedIngredients = Task { try await chopIngredients(order.ingredients) }
    let meat = Task { await marinate(meat: .chicken) }
    let soup = await Soup(meat: meat.value, ingredients: choppedIngredients.value)
    return await stove.cook(pot: boilingPot.value, soup: soup, duration: .minutes(10))
}
```

[02:35] While this expresses which tasks can run concurrently and which cannot,
[02:39] this is not the recommended way to use concurrency in Swift.
[02:43] Here is the same function expressed using structured concurrency.
[02:47] Since we have a known number of child tasks to create,
[02:50] we can use the convenient "async let" syntax.

```swift
func makeSoup(order: Order) async throws -> Soup {
    async let pot = stove.boilBroth()
    async let choppedIngredients = chopIngredients(order.ingredients)
    async let meat = marinate(meat: .chicken)
    let soup = try await Soup(meat: meat, ingredients: choppedIngredients)
    return try await stove.cook(pot: pot, soup: soup, duration: .minutes(10))
}
```

[02:54] These tasks form a structured relationship with their parent task.
[02:58] We will talk about why this is important shortly.

[03:01] makeSoup calls a number of asynchronous functions.

[03:04] One of them is "chopIngredients", which takes a list of ingredients
[03:07] and uses a task group to chop all of them concurrently.

```swift
func chopIngredients(_ ingredients: [any Ingredient]) async -> [any ChoppedIngredient] {
    return await withTaskGroup(of: (ChoppedIngredient?).self,
                               returning: [any ChoppedIngredient].self) { group in
         // Concurrently chop ingredients
         for ingredient in ingredients {
             group.addTask { await chop(ingredient) }
         }
         // Collect chopped vegetables
         var choppedIngredients: [any ChoppedIngredient] = []
         for await choppedIngredient in group {
             if choppedIngredient != nil {
                choppedIngredients.append(choppedIngredient!)
             }
         }
         return choppedIngredients
    }
}
```

[03:11] Now that we are familiar with makeSoup, let's take a look at the task hierarchy.
[03:16] Child tasks are indicated by the colored boxes,
[03:19] while the arrows point from parent task to child task.

[03:22] makeSoup has three child tasks for chopping ingredients,
[03:26] marinating chicken, and boiling broth.

[03:29] chopIngredients uses a task group to create a child task for each ingredient.
[03:34] If we have three ingredients, it too will create three children.

[03:38] This parent-child hierarchy forms a tree, the task tree.

[03:43] Now that we've introduced the task tree,
[03:45] let's start identifying how that benefits our code.
[03:48] Task cancellation is used to signal that the app no longer needs the result
[03:52] of a task and the task should stop and either return a partial result
[03:56] or throw an error.

[03:58] In our soup example, we may want to stop making a soup order if that customer left,
[04:02] decided they wanted to order something else, or it's closing time.

[04:08] What causes task a cancellation?
[04:10] Structured tasks are cancelled implicitly when they go out of scope,
[04:14] though you can call "cancelAll" on task groups
[04:16] to cancel all active children and any future child tasks.

[04:21] Unstructured tasks are cancelled explicitly with the "cancel" function.

[04:26] Cancelling the parent task results in the cancellation of all child tasks.

```swift
func makeSoup(order: Order) async throws -> Soup {
    async let pot = stove.boilBroth()

    guard !Task.isCancelled else {
        throw SoupCancellationError()
    }

    async let choppedIngredients = chopIngredients(order.ingredients)
    async let meat = marinate(meat: .chicken)
    let soup = try await Soup(meat: meat, ingredients: choppedIngredients)
    return try await stove.cook(pot: pot, soup: soup, duration: .minutes(10))
}
```

[04:32] Cancellation is cooperative, so child tasks aren't immediately stopped.

[04:36] It simply sets the "isCancelled" flag on that task.
[04:40] Actually acting on the cancellation is done in your code.

[04:43] Cancellation is a race.

[04:45] If the task is cancelled before our check,
[04:48] "makeSoup" throws a "SoupCancellationError".

[04:51] If the task is cancelled after the guard executes,
[04:54] the program will carry on preparing the soup.

[04:58] If we are going to throw a cancellation error
[05:00] instead of returning a partial result, we can call "Task.checkCancellation",
[05:04] which throws a "CancellationError" if the task was cancelled.

```swift
func chopIngredients(_ ingredients: [any Ingredient]) async throws -> [any ChoppedIngredient] {
    return try await withThrowingTaskGroup(of: (ChoppedIngredient?).self,
                                   returning: [any ChoppedIngredient].self) { group in
        try Task.checkCancellation()
        
        // Concurrently chop ingredients
        for ingredient in ingredients {
            group.addTask { await chop(ingredient) }
        }

        // Collect chopped vegetables
        var choppedIngredients: [any ChoppedIngredient] = []
        for try await choppedIngredient in group {
            if let choppedIngredient {
                choppedIngredients.append(choppedIngredient)
            }
        }
        return choppedIngredients
    }
}
```

[05:08] It's important to check the task cancellation status
[05:11] before starting any expensive work
[05:13] to verify that the result is still necessary.
[05:15] Cancellation checking is synchronous, so any function,
[05:19] asynchronous or synchronous, that should react to cancellation
[05:22] should check the task cancellation status before continuing.
[05:27] Polling for cancellation with "isCancelled"
[05:30] or "checkCancellation" is useful when the task is running,
[05:33] but there are times when you may need to respond to cancellation
[05:36] while the task is suspended and no code is running,
[05:39] like when implementing an AsyncSequence.
[05:42] This is where "withTaskCancellationHandler" is useful.

[05:47] Let's introduce a shift function.

```swift
actor Cook {
    func handleShift<Orders>(orders: Orders) async throws
       where Orders: AsyncSequence,
             Orders.Element == Order {

        for try await order in orders {
            let soup = try await makeSoup(order)
            // ...
        }
    }
}
```

[05:50] The cook should make soups as orders come in
[05:52] until the end of their shift, signaled by a task cancellation.

[05:58] In one cancellation scenario,
[06:00] the asynchronous for-loop gets a new order before it is cancelled.
[06:04] The "makeSoup" function handles the cancellation
[06:06] as we defined earlier, and throws an error.

[06:09] In another scenario, the cancellation may take place
[06:12] while the task is suspended, waiting on the next order.

[06:16] This case is more interesting because the task isn't running,
[06:19] so we can't explicitly poll for the cancellation event.

[06:23] Instead, we have to use the cancellation handler
[06:26] to detect the cancellation event and break out of the asynchronous for-loop.
[06:31] The orders are produced from an AsyncSequence.

[06:35] AsyncSequences are driven by an AsyncIterator,
[06:38] which defines an asynchronous "next" function.

[06:42] Like with synchronous iterators,
[06:44] the "next" function returns the next element in the sequence,
[06:48] or nil to indicate that we are at the end of the sequence.

```swift
public func next() async -> Order? {
    return await withTaskCancellationHandler {
        let result = await kitchen.generateOrder()
        guard state.isRunning else {
            return nil
        }
        return result
    } onCancel: {
        state.cancel()
    }
}
```

[06:52] Many AsyncSequences are implemented with a state machine,
[06:56] which we use to stop the running sequence.

[06:59] In our example here, when "isRunning" is true,
[07:02] the sequence should continue emitting orders.
[07:05] Once the task is cancelled,
[07:06] we need to indicate that the sequence is done and should shut down.

[07:10] We do this by synchronously calling the "cancel" function
[07:13] on our sequence state machine.

[07:16] Note that because the cancellation handler runs immediately,
[07:20] the state machine is shared mutable state between the cancellation handler
[07:24] and main body, which can run concurrently.
[07:28] We'll need to protect our state machine.

[07:30] While actors are great for protecting encapsulated state,
[07:34] we want to modify and read individual properties on our state machine,
[07:38] so actors aren't quite the right tool for this.

[07:41] Furthermore, we can't guarantee the order that operations run on an actor,
[07:46] so we can't ensure that our cancellation will run first.
[07:49] We'll need something else.

```swift
private final class OrderState: Sendable {
    let protectedIsRunning = ManagedAtomic<Bool>(true)
    var isRunning: Bool {
        get { protectedIsRunning.load(ordering: .acquiring) }
        set { protectedIsRunning.store(newValue, ordering: .relaxed) }
    }
    func cancel() { isRunning = false }
}
```

[07:51] I've decided to use atomics from the Swift Atomics package,
[07:55] but we could use a dispatch queue or locks.

[07:58] These mechanisms allow us to synchronize the shared state,
[08:01] avoiding race conditions, while allowing us to cancel the running state machine
[08:05] without introducing an unstructured task in the cancellation handler.

[08:10] The task tree automatically propagates task cancellation information.
[08:14] Instead of having to worry about a cancellation token and synchronization,
[08:18] we let the Swift runtime handle it for us safely.

[08:21] Remember, cancellation does not stop a task from running,
[08:25] it only signals to the task that it has been cancelled
[08:28] and should stop running as soon a possible.

[08:31] It is up to your code to check for cancellation.

[08:35] Next, let's consider how the structured task tree
[08:38] helps propagate priority and avoid priority inversions.

[08:42] First, what is priority, and why do we care?
[08:46] Priority is your way to communicate to the system how urgent a given task is.
[08:51] Certain tasks, like responding to a button press,
[08:53] need to run immediately or the app will appear frozen.

[08:57] Meanwhile, other tasks, like prefetching content from a server,
[09:01] can run in the background without anyone noticing.

[09:04] Second, what is a priority inversion?
[09:08] A priority inversion happens when a high-priority task is waiting
[09:11] on the result of a lower-priority task.

[09:15] By default, child tasks inherit their priority from their parent,
[09:19] so assuming that makeSoup is running in a task at medium priority,
[09:23] all child tasks will also run at medium priority.

[09:28] Let's say a VIP guest who comes to our restaurant looking for soup.

[09:33] We give their soup a higher priority to ensure we get a good review.

[09:37] When they await their soup, the priority of all child tasks is escalated,
[09:42] ensuring that no high-priority task is waiting on a lower-priority task,
[09:46] avoiding the priority inversion.

[09:50] Awaiting a result from a task with a higher priority
[09:53] escalates the priority of all child tasks in the task tree.

[09:57] Note that awaiting the next result of a task group
[10:00] escalates all child tasks in the group,
[10:03] since we don't know which one is most likely to complete next.

[10:07] The concurrency runtime uses priority queues to schedule tasks,
[10:11] so higher-priority tasks are selected to run before lower-priority tasks.

[10:16] The task keeps the escalated priority for the remainder of its lifetime.

[10:20] It's not possible to undo a priority escalation.

[10:23] We effectively satisfied our VIP guest with a speedy soup delivery
[10:27] and got a good review, so our kitchen is starting to get popular now.
[10:31] We want to ensure we're using our resources effectively
[10:34] and noticed that we're creating a lot of chopping tasks.

[10:37] Let's investigate some useful patterns for managing concurrency with task groups.

[10:43] We only have space for so many cutting boards.

[10:45] If we chop too many ingredients simultaneously,
[10:48] we'll run out of space for other tasks, so we want to limit
[10:52] the number of ingredients getting chopped at the same time.

[10:56] Going back to our code,
[10:58] we want to investigate the loop creating the chopping tasks.

```swift
func chopIngredients(_ ingredients: [any Ingredient]) async -> [any ChoppedIngredient] {
    return await withTaskGroup(of: (ChoppedIngredient?).self,
                               returning: [any ChoppedIngredient].self) { group in
        // Concurrently chop ingredients
        for ingredient in ingredients {
            group.addTask { await chop(ingredient) }
        }

        // Collect chopped vegetables
        var choppedIngredients: [any ChoppedIngredient] = []
        for await choppedIngredient in group {
            if let choppedIngredient {
                choppedIngredients.append(choppedIngredient)
            }
        }
        return choppedIngredients
    }
}
```

[11:03] We replace the original loop over each ingredient
[11:05] with a loop that starts up to the maximum number of chopping tasks.

```swift
func chopIngredients(_ ingredients: [any Ingredient]) async -> [any ChoppedIngredient] {
    return await withTaskGroup(of: (ChoppedIngredient?).self,
                               returning: [any ChoppedIngredient].self) { group in
        // Concurrently chop ingredients
        let maxChopTasks = min(3, ingredients.count)
        for ingredientIndex in 0..<maxChopTasks {
            group.addTask { await chop(ingredients[ingredientIndex]) }
        }

        // Collect chopped vegetables
        var choppedIngredients: [any ChoppedIngredient] = []
        var nextIngredientIndex = maxChopTasks
        for await choppedIngredient in group {
            if nextIngredientIndex < ingredients.count {
                group.addTask { await chop(ingredients[nextIngredientIndex]) }
                nextIngredientIndex += 1
            }
            if let choppedIngredient {
                choppedIngredients.append(choppedIngredient)
            }
        }
        return choppedIngredients
    }
}
```

[11:10] Next, we want the loop collecting results to start a new task
[11:14] each time an earlier task finishes.

```swift
func chopIngredients(_ ingredients: [any Ingredient]) async -> [any ChoppedIngredient] {
    return await withTaskGroup(of: (ChoppedIngredient?).self,
                               returning: [any ChoppedIngredient].self) { group in
        // Concurrently chop ingredients
        let maxChopTasks = min(3, ingredients.count)
        for ingredientIndex in 0..<maxChopTasks {
            group.addTask { await chop(ingredients[ingredientIndex]) }
        }

        // Collect chopped vegetables
        var choppedIngredients: [any ChoppedIngredient] = []
        var nextIngredientIndex = maxChopTasks
        for await choppedIngredient in group {
            if nextIngredientIndex < ingredients.count {
                group.addTask { await chop(ingredients[nextIngredientIndex]) }
                nextIngredientIndex += 1
            }
            if let choppedIngredient {
                choppedIngredients.append(choppedIngredient)
            }
        }
        return choppedIngredients
    }
}
```

[11:18] The new loop waits until one of the running tasks finish
[11:21] and, while there are still ingredients to chop,
[11:23] adds a new task to chop the next ingredient.

[11:28] Let's distill this idea down to see the pattern more clearly.

```swift
withTaskGroup(of: Something.self) { group in
    for _ in 0..<maxConcurrentTasks {
        group.addTask { }
    }
    while let <partial result> = await group.next() {
        if !shouldStop { 
            group.addTask { }
        }
    }
}
```

[11:32] The initial loop creates up to the maximum number of concurrent tasks,
[11:35] ensuring that we don't create too many.

[11:37] Once the maximum number of tasks is running, we wait for one to finish.

[11:42] After it finishes and we haven't hit a stopping condition,
[11:45] we create a new task to keep making progress.

[11:49] This limits the number of concurrent tasks in the group
[11:51] since we won't start new work until earlier tasks finish.

[11:57] Earlier, we talked about chefs working in shifts
[12:00] and using cancellation to indicate when their shift was over.

[12:04] This is the Kitchen Service code handling the shift.

```swift
func run() async throws {
    try await withThrowingTaskGroup(of: Void.self) { group in
        for cook in staff.keys {
            group.addTask { try await cook.handleShift() }
        }

        group.addTask {
            // keep the restaurant going until closing time
            try await Task.sleep(for: shiftDuration)
        }

        try await group.next()
        // cancel all ongoing shifts
        group.cancelAll()
    }
}
```

[12:07] Each cook starts their shift in a separate task.

[12:11] Once the cooks are working, we start a timer.
[12:14] When the timer finishes, we cancel all ongoing shifts.

[12:18] Notice that none of the tasks return a value.
[12:22] New in Swift 5.9 is the withDiscardingTaskGroup API.
[12:27] Discarding task groups don't hold onto the results of completed child tasks.
[12:32] Resources used by tasks are freed immediately after the task finishes.

[12:37] We can change the run method to make use of a discarding task group.

```swift
func run() async throws {
    try await withThrowingDiscardingTaskGroup { group in
        for cook in staff.keys {
            group.addTask { try await cook.handleShift() }
        }

        group.addTask { // keep the restaurant going until closing time
            try await Task.sleep(for: shiftDuration)
            throw TimeToCloseError()
        }
    }
}
```

[12:41] Discarding task groups automatically clean up their children,
[12:45] so there is no need to explicitly cancel the group and clean up.

[12:48] The discarding task group also has automatic sibling cancellation.

[12:52] If any of the child tasks throw an error,
[12:56] all remaining tasks are automatically cancelled.

[12:59] This is ideal for our use case here.
[13:02] We can throw a "TimeToCloseError" when the shift is over,
[13:05] and it will automatically end the shift for all chefs.

[13:10] The new discard task group automatically releases resources
[13:14] when a task finishes, unlike the normal task groups
[13:16] where you have to collect the result.
[13:18] This helps reduce memory consumption
[13:20] when you have many tasks that don't need to return anything,
[13:23] like when you're processing a stream of requests.

[13:26] In some situations, you'll want to return a value from your task group,
[13:30] but also want to limit the number of concurrent tasks.
[13:33] We covered a general pattern for using the completion of one task
[13:37] to start another, avoiding a task explosion.
[13:42] We're making soup more efficiently than ever,
[13:44] but we still need to scale up more.

[13:47] It's time to move production to the server.

[13:49] With that comes challenges of tracing orders as they are processed.

[13:53] Task-local values are here to help.

[13:56] A task-local value is a piece of data associated with a given task,
[14:00] or more precisely, a task hierarchy.
[14:03] It's like a global variable, but the value bound
[14:06] to the task-local value is only available from the current task hierarchy.

[14:10] Task-local values are declared as static properties
[14:13] with the "TaskLocal" property wrapper.

```swift
actor Kitchen {
    @TaskLocal static var orderID: Int?
    @TaskLocal static var cook: String?
    func logStatus() {
        print("Current cook: \(Kitchen.cook ?? "none")")
    }
}

let kitchen = Kitchen()
await kitchen.logStatus()
await Kitchen.$cook.withValue("Sakura") {
    await kitchen.logStatus()
}
await kitchen.logStatus()
```

[14:16] It's a good practice to make the task local optional.

[14:19] Any task that doesn't have the value set will need to return a default value,
[14:24] which is easily represented by a nil optional.
[14:28] An unbound task local contains its default value.

[14:32] In our case, we have an optional String,
[14:34] so it's nil and there is no cook associated with the current task.
[14:39] Task-local values can't be assigned to explicitly,
[14:42] but must be bound for a specific scope.
[14:46] The binding lasts for the duration of the scope,
[14:49] and reverts back to the original value at the end of the scope.

[14:54] Going back to the task tree, each task has an associated place for task-local values.

[14:59] We bound the name "Sakura" to the "cook"task-local variable
[15:03] before making soup.
[15:05] Only makeSoup stores the bound value.
[15:08] The children do not have any values saved in their task-local storage.

[15:13] Looking for the value bound to a task-local variable
[15:16] involves recursively walking each parent until we find a task with that value.

[15:21] If we find a task with the value bound, the task local will assume that value.

[15:26] If we reach the root, indicated by the task not having a parent,
[15:29] the task local was not bound and we get the original default value.
[15:34] The Swift runtime is optimized to run these queries faster.

[15:38] Instead of walking the tree,
[15:39] we have a direct reference to the task with the key we're looking for.

[15:44] The recursive nature of the task tree lends itself nicely
[15:47] to shadowing values without losing the former value.

[15:51] Suppose we want to track the current step in the soup-making process.

[15:56] We can bind the "step" variable to "soup" in "'makeSoup",
[15:59] then rebind it to "chop" in "chopIngredients".

[16:03] The value bound in chopIngredients will shadow the former value
[16:06] until we return from chopIngredients, where we observe the original value.

[16:12] Through the powers of video editing magic,
[16:15] we've moved our service to the cloud to keep up with the demands for soup.

[16:18] We still have the same soup-making functionality,
[16:21] but it's on a server instead.

[16:23] We'll need to observe orders as they pass through the system
[16:26] to ensure they're being completed in a timely manner
[16:29] and to monitor for unexpected failures.

[16:32] The server environment handles many requests concurrently,
[16:35] so we'll want to include information that will allow us to trace a given order.

[16:41] Logging by hand is repetitive and verbose, which leads to subtle bugs and typos.

```swift
func makeSoup(order: Order) async throws -> Soup {
     log.debug("Preparing dinner", [
       "cook": "\(self.name)",
       "order-id": "\(order.id)",
       "vegetable": "\(vegetable)",
     ])
     // ... 
}

 func chopVegetables(order: Order) async throws -> [Vegetable] {
     log.debug("Chopping ingredients", [
       "cook": "\(self.name)",
       "order-id": "\(order.id)",
       "vegetable": "\(vegetable)",
     ])
     
     async let choppedCarrot = try chop(.carrot)
     async let choppedPotato = try chop(.potato)
     return try await [choppedCarrot, choppedPotato]
}

func chop(_ vegetable: Vegetable, order: Order) async throws -> Vegetable {
    log.debug("Chopping vegetable", [
      "cook": "\(self.name)",
      "order-id": "\(order)",
      "vegetable": "\(vegetable)",
    ])
    // ...
}
```

[16:46] Oh no, I've accidentally logged the entire order instead of just the order ID.

[16:51] Let's find out how we can use task-local values to make our logging more reliable.

[16:57] On Apple devices, you'll want to continue using the OSLog APIs directly,
[17:03] but as parts of your application move to the cloud,
[17:06] you'll need other solutions.

[17:08] SwiftLog is a logging API package with multiple backing implementations,
[17:13] allowing you to drop in a logging back end
[17:15] that suites your needs without making changes to your server.

[17:19] MetadataProvider is a new API in SwiftLog 1.5.

```swift
let orderMetadataProvider = Logger.MetadataProvider {
    var metadata: Logger.Metadata = [:]
    if let orderID = Kitchen.orderID {
        metadata["orderID"] = "\(orderID)"
    }
    return metadata
}
```

[17:24] Implementing a metadata provider makes it easy to abstract your logging logic
[17:28] to ensure that you're emitting consistent information about relevant values.

[17:34] The metadata provider uses a dictionary-like structure,
[17:37] mapping a name to the value being logged.
[17:40] We want to automatically log the orderID task-local variable,
[17:45] so we check to see if it was defined, and if it is, add it to the dictionary.
[17:51] Multiple libraries may define their own metadata provider
[17:54] to look for library-specific information,
[17:56] so the MetadataProvider defines a "multiplex" function,
[18:00] which takes multiple metadata providers and combines them into a single object.

```swift
let orderMetadataProvider = Logger.MetadataProvider {
    var metadata: Logger.Metadata = [:]
    if let orderID = Kitchen.orderID {
        metadata["orderID"] = "\(orderID)"
    }
    return metadata
}

let chefMetadataProvider = Logger.MetadataProvider {
    var metadata: Logger.Metadata = [:]
    if let chef = Kitchen.chef {
        metadata["chef"] = "\(chef)"
    }
    return metadata
}

let metadataProvider = Logger.MetadataProvider.multiplex([orderMetadataProvider,
                                                          chefMetadataProvider])

LoggingSystem.bootstrap(StreamLogHandler.standardOutput, metadataProvider: metadataProvider)

let logger = Logger(label: "KitchenService")
```

[18:05] Once we have a metadata provider, we initialize the logging system
[18:09] with that provider, and we're ready to start logging.

[18:14] The logs automatically include information specified in the metadata provider,
[18:18] so we don't need to worry about including it in the log message.

```swift
func makeSoup(order: Order) async throws -> Soup {
    logger.info("Preparing soup order")
    async let pot = stove.boilBroth()
    async let choppedIngredients = chopIngredients(order.ingredients)
    async let meat = marinate(meat: .chicken)
    let soup = try await Soup(meat: meat, ingredients: choppedIngredients)
    return try await stove.cook(pot: pot, soup: soup, duration: .minutes(10))
}
```

[18:22] The logs show as order 0 enters the kitchen,
[18:25] and where our chefs picks up that order.

[18:28] Values in the metadata provider are listed clearly in the log,
[18:31] making it easier for you to track an order through the soup-making process.

[18:37] Task-local values allow you to attach information to a task hierarchy.

[18:41] All tasks, except detached tasks, inherit task-local values from the current task.
[18:48] They are bound in a given scope to a specific task tree,
[18:51] providing you with low-level building blocks
[18:53] to propagate additional context information through the task hierarchy.
[18:59] Now we'll use the task hierarchy and tools it provides us
[19:02] to trace and profile a concurrent distributed system.
[19:07] When working with concurrency on Apple platforms,
[19:09] Instruments is your friend.
[19:11] The Swift Concurrency instrument gives you insight
[19:13] into the relationships between your structured tasks.
[19:17] For more information, check out the session,
[19:19] "Visualize and optimize Swift concurrency."
[19:23] Instruments also introduced an HTTP traffic instrument
[19:27] in the "Analyze HTTP Traffic in instruments" session.
[19:31] The HTTP traffic analyzer only shows traces for events happening locally.

[19:36] The profile shows a grey box while waiting for a response from the server,
[19:40] so we'll need more information to understand
[19:43] how to improve the performance of our server.

[19:46] Introducing the new Swift Distributed Tracing package.

[19:50] The task tree is great for managing child tasks
[19:52] in a single task hierarchy.

[19:54] Distributed tracing allows you to leverage the benefits of the task tree
[19:58] across multiple systems to gain insight
[20:01] into performance characteristics and task relationships.
[20:04] The Swift Distributed Tracing package has an implementation
[20:07] of the OpenTelemetry protocol, so existing tracing solutions,
[20:11] like Zipkin and Jaeger, will work out of the box.

[20:16] Our goal with Swift Distributed Tracing is to fill in the opaque
[20:19] "waiting for response" in Xcode Instruments
[20:21] with detailed information about what is happening in the server.
[20:26] We'll need to instrument our server code to figure out where we need to focus.

[20:31] Distributed tracing is a little different from tracing processes locally.

[20:35] Instead of getting a trace per-function,
[20:37] we instrument our code with spans using the "withSpan" API.

```swift
func makeSoup(order: Order) async throws -> Soup {
    try await withSpan("makeSoup(\(order.id)") { span in
        async let pot = stove.boilWater()
        async let choppedIngredients = chopIngredients(order.ingredients)
        async let meat = marinate(meat: .chicken)
        let soup = try await Soup(meat: meat, ingredients: choppedIngredients)
        return try await stove.cook(pot: pot, soup: soup, duration: .minutes(10))
    }
}
```

[20:43] Spans allow us to assign names to regions of code
[20:46] that are reported in the tracing system.
[20:49] Spans don't need to cover an entire function.

[20:51] They can provide more insight on specific pieces of a given function.

[20:56] withSpan annotates our tasks with additional trace IDs and other metadata,
[21:01] allowing the tracing system to merge the task trees into a single trace.
[21:06] The tracing system has enough information to provide you with insight
[21:10] into the task hierarchy, along with information
[21:13] about the runtime performance characteristics of a task.

[21:17] The span name is presented in the tracing UI.

[21:20] You'll want to keep them short and descriptive
[21:22] so that you can easily find information about a specific span without clutter.

[21:27] We can attach additional metadata with the use of span attributes,
[21:32] so we don't need to clutter the span name with the order ID.

[21:36] Here we've replaced the span name with the "#function" directive
[21:40] to automatically fill the span name with the function name,
[21:43] and used the span attribute to attach the current order ID
[21:47] to the span information reported to the tracer.

```swift
func makeSoup(order: Order) async throws -> Soup {
    try await withSpan(#function) { span in
        span.attributes["kitchen.order.id"] = order.id
        async let pot = stove.boilWater()
        async let choppedIngredients = chopIngredients(order.ingredients)
        async let meat = marinate(meat: .chicken)
        let soup = try await Soup(meat: meat, ingredients: choppedIngredients)
        return try await stove.cook(pot: pot, soup: soup, duration: .minutes(10))
    }
}
```

[21:51] Tracing systems usually present the attributes while inspecting a given span.

[21:56] Most spans come with HTTP status codes,
[21:59] request and response sizes, start and end times, and other metadata
[22:03] making it easier for you to track information passing through your system.

[22:07] As noted on the previous slide, you can define your own attributes.
[22:11] For more examples of how you can leverage spans, please check out
[22:14] the swift-distributed-tracing-extras repository.

[22:18] If a task fails and throws an error,
[22:21] that information is also presented in the span and reported in the tracing system.
[22:26] Since spans contain both timing information
[22:29] and the relationships of tasks in the tree,
[22:31] it's a helpful way to track down errors
[22:33] caused by timing races and identify how they impact other tasks.
[22:39] We've talked about the tracing system and how it can reconstruct task trees
[22:43] using the trace IDs and how you can attach your own attributes to a span,
[22:48] but we haven't started working this into a distributed system yet.
[22:52] The beauty of the tracing system
[22:54] is that there is nothing more that needs to be done.

[22:56] If we factor a chopping service out of our kitchen service,
[23:00] otherwise keeping the same code,
[23:02] the tracing system will automatically pick up the traces
[23:05] and relate them across different machines in the distributed system.

[23:09] The trace view will indicate
[23:10] that the spans are running on a different machine,
[23:12] but will otherwise be the same.
[23:15] Distributed tracing is most powerful when all parts of the system
[23:19] embrace traces, including the HTTP clients,
[23:23] servers, and other RPC systems.

[23:26] Swift Distributed Tracing leverages task-local values,
[23:30] built on the task trees, to automatically propagate
[23:33] all of the information necessary to produce reliable cross-node traces.
[23:37] Structured tasks unlock the secrets of your concurrent systems,
[23:41] providing you with tools to automatically cancel operations,
[23:45] automatically propagate priority information,
[23:48] and facilitate tracing complex distributed workloads.

[23:52] All of these work because
[23:53] of the structured nature of concurrency in Swift.

[23:57] I hope this session excited you about structured concurrency,
[24:00] and that you'll reach for structured tasks
[24:02] before using unstructured alternatives.

[24:05] Thank you for watching!
[24:06] I can't wait to see what other useful patterns you'll come up with
[24:09] using structured concurrency.

[24:11] Mm, soup!
[24:15] ♪ ♪

