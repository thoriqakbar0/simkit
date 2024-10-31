<script lang="ts">
    import Button from "./ui/button/button.svelte";
    import Input from "./ui/input/input.svelte";
    import { cn } from "$lib/utils";
    import { marked } from 'marked';

    let { class: className = ""} = $props();
    import { chatStore} from "./chat-store.svelte";

    type Role = "user" | "assistant" | "system";

    interface Message {
        role: Role;
        content: string;
        ready_to_simulate?: boolean;
    }

    let inputMessage = $state("");

    async function submitMessages() {
        if (inputMessage.trim()) {
            chatStore.isStreaming = true;
            chatStore.messages = [...chatStore.messages, { role: "user", content: inputMessage }];
            inputMessage = "";
            chatStore.messages = [...chatStore.messages, { role: "assistant", content: "" }];
            const messages = chatStore.messages;
            const response = await fetch("https://simkitapi.rethoriq.com/ai", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ messages})
            });

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            while (true) {
                const { done, value } = await reader?.read() ?? { done: true, value: undefined };
                if (done) {
                    chatStore.isStreaming = false;
                    break;
                }
                const chunk = decoder.decode(value);
                try {
                    const { bot_message, ready_to_simulate } = JSON.parse(chunk.replace(/^data: /, '').trim());
                    Object.assign(chatStore.messages[chatStore.messages.length - 1], { content: bot_message, ready_to_simulate });
                } catch (error) {
                    continue;
                }
            }
            chatStore.isStreaming = false;
        }
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === "Enter" && !chatStore.isStreaming) {
            submitMessages();
        }
    }

    async function simulate(content: string) {
        console.log(JSON.stringify({ prompt: content }));
        try {
            const response = await fetch("https://simkitapi.rethoriq.com/generate-sim", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: content })
            });
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            while (true) {
                const { done, value } = await reader?.read() ?? { done: true, value: undefined };
                if (done) {
                    chatStore.isStreaming = false;
                    break;
                }
                const chunk = decoder.decode(value);
                try {
                    const data = JSON.parse(chunk.replace(/^data: /, '').trim());
                    chatStore.simConfig = data;
                    console.log(chatStore.simConfig);
                } catch (error) {
                    continue;
                }
            }
        } catch (error) {
            // console.error("Simulation failed:", error);
        }
    }
</script>

<div class={cn("flex flex-col h-full max-h-screen relative overflow-y-auto pb-20", className)}>
    <div class="flex-1 overflow-y-auto p-4">
        {@render Message("assistant", "Hello! How can I help you with your process flow brainstorm today?")}
        {#each chatStore.messages as message}
            {@render Message(message.role, message.content, message.ready_to_simulate)}
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
        disabled={chatStore.isStreaming}
    />
    <Button onclick={submitMessages} disabled={chatStore.isStreaming}>Submit</Button>
</div>
{/snippet}

{#snippet Message(role: Role, content: string, ready_to_simulate?: boolean)}
<div class="flex w-full {role === 'assistant' ? 'justify-start' : 'justify-end'} mb-4">
    <div class="prose prose-code:max-w-[50%] max-w-[70%] rounded-lg px-4 py-2 text-md {role === 'assistant' ? 'bg-secondary text-secondary-foreground' : 'bg-primary text-primary-foreground'}">
        {@html marked(content)}
    </div>
    {#if role === "assistant" && ready_to_simulate}
        <Button class="ml-2" variant="secondary" onclick={() => simulate(content)} disabled={chatStore.isStreaming}>Simulate</Button>
    {/if}
</div>
{/snippet}