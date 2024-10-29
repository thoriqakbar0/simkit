<script lang="ts">
    import Button from "./ui/button/button.svelte";
    import Input from "./ui/input/input.svelte";

    type Role = "user" | "assistant" | "system";

    let isStreaming = $state(false);

    interface Message {
        role: Role;
        content: string;
    }

    let messages: Message[] = $state([]);
    let inputMessage = $state("");
    let streamedContent = $state("");

    async function handleSubmit() {
        if (inputMessage.trim()) {
            isStreaming = true;
            messages = [...messages, { role: "user", content: inputMessage }];
            inputMessage = "";
            messages = [...messages, { role: "assistant", content: streamedContent }];

            const response = await fetch("http://localhost:8000/ai", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ messages })
            });

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader?.read() ?? { done: true, value: undefined };
                if (done) break;
                
                streamedContent += decoder.decode(value);
                messages[messages.length - 1].content = streamedContent;
            }
            isStreaming = false;
        }
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === "Enter" && !isStreaming) {
            handleSubmit();
        }
    }
</script>

<div class="flex flex-col h-full debug relative">
    <div class="flex-1 overflow-y-auto p-4">
        {#each messages as message}
            {@render Message(message.role, message.content)}
        {/each}
    </div>
    {@render InputField()}
</div>

{#snippet InputField()}
<div class="flex absolute bottom-5 w-full px-4 gap-2">
    <Input 
        bind:value={inputMessage} 
        placeholder="Type a message..." 
        onkeydown={handleKeydown}
        disabled={isStreaming}
    />
    <Button onclick={handleSubmit} disabled={isStreaming}>Submit</Button>
</div>
{/snippet}

{#snippet Message(role: Role, content: string)}
<div class="flex w-full {role === 'assistant' ? 'justify-start' : 'justify-end'} mb-4">
    <div class="max-w-[70%] rounded-lg px-4 py-2 {role === 'assistant' ? 'bg-secondary text-secondary-foreground' : 'bg-primary text-primary-foreground'}">
        {content}
    </div>
</div>
{/snippet}
