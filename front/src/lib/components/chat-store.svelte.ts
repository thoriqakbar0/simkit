
type Role = "user" | "assistant" | "system";
interface Message {
    role: Role;
    content: string;
    ready_to_simulate?: boolean;
}


interface SimResource {
    name: string;
    capacity: number;
    cost_per_unit: number;
    efficiency_threshold: number;
    priority?: number;
    shared?: boolean;
}

interface SimMetric {
    name: string;
    target_value: number;
    unit: string;
    description: string;
    aggregation?: string;
}

interface SimInsightRule {
    metric: string;
    condition: string;
    threshold: number;
    recommendation: string;
}

interface SimProcess {
    name: string;
    duration: number;
    required_resources: string[];
    expected_service_time: number;
    max_acceptable_wait: number;
    condition?: string;
    next_processes?: string[];
    loop?: boolean;
    release_resources?: boolean;
}

interface SimEntity {
    attributes: Record<string, any>;
}

interface SimConfig {
    title: string;
    description: string;
    duration: number;
    resources: SimResource[];
    processes: SimProcess[];
    entities_per_hour: number;
    target_metrics: SimMetric[];
    insight_rules: SimInsightRule[];
    business_context: string;
    entity_attributes?: Record<string, any>;
}

export const chatStore: { isStreaming: boolean; messages: Message[]; simConfig: SimConfig | null } = $state({
    isStreaming: false,
    messages: [],
    simConfig: null
});