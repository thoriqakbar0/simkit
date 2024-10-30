
type Role = "user" | "assistant" | "system";
interface Message {
    role: Role;
    content: string;
    ready_to_simulate?: boolean;
}

export let isStreaming = $state(false);

export let messages: Message[] = $state([]);

export const chatStore: { isStreaming: boolean; messages: Message[] } = $state({
    isStreaming,
    messages,
})