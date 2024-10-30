<script lang="ts">
    import { chatStore } from "./chat-store.svelte";
    let simConfig = chatStore.simConfig;
</script>

<div class="simulation-container">
    {#if !simConfig}
        <div class="empty-state">
            <h2>Simulation Dashboard</h2>
            <p>Configure your simulation to get started</p>
        </div>
    {:else}
        <div class="simulation-details">
            <header class="sim-header">
                <h1>{simConfig.title}</h1>
                <p class="description">{simConfig.description}</p>
            </header>

            <div class="sim-stats">
                <div class="stat-card">
                    <span class="stat-label">Duration</span>
                    <span class="stat-value">{simConfig.duration} minutes</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">Throughput</span>
                    <span class="stat-value">{simConfig.entities_per_hour} per hour</span>
                </div>
            </div>

            <div class="sim-grid">
                <div class="grid-item">
                    <h2>Resources</h2>
                    <div class="resource-list">
                        {#each simConfig.resources as resource}
                            <div class="resource-card">
                                <h3>{resource.name}</h3>
                                <div class="resource-details">
                                    <span>Capacity: {resource.capacity}</span>
                                    <span>Cost: ${resource.cost_per_unit}/unit</span>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>

                <div class="grid-item">
                    <h2>Processes</h2>
                    <div class="process-list">
                        {#each simConfig.processes as process}
                            <div class="process-card">
                                <h3>{process.name}</h3>
                                <span>{process.duration} minutes</span>
                            </div>
                        {/each}
                    </div>
                </div>

                <div class="grid-item">
                    <h2>Target Metrics</h2>
                    <div class="metrics-list">
                        {#each simConfig.target_metrics as metric}
                            <div class="metric-card">
                                <h3>{metric.name}</h3>
                                <span>{metric.target_value} {metric.unit}</span>
                            </div>
                        {/each}
                    </div>
                </div>

                <div class="grid-item">
                    <h2>Insight Rules</h2>
                    <div class="rules-list">
                        {#each simConfig.insight_rules as rule}
                            <div class="rule-card">
                                <h3>{rule.metric}</h3>
                                <p>{rule.condition} {rule.threshold}</p>
                                <p class="recommendation">{rule.recommendation}</p>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .simulation-container {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        overflow-y: auto;
        max-height: 100vh;
    }

    .empty-state {
        text-align: center;
        padding: 4rem;
        background: #f8fafc;
        border-radius: 8px;
        color: #64748b;
    }

    .sim-header {
        margin-bottom: 2rem;
    }

    .sim-stats {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        flex: 1;
    }

    .sim-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
    }

    .grid-item {
        background: #fff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .resource-card, .process-card, .metric-card, .rule-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }

    .recommendation {
        color: #0ea5e9;
        font-style: italic;
    }
</style>
