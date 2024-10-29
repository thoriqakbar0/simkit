from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from ship_llm import AI
from fastapi.responses import StreamingResponse
import os
from pydantic import BaseModel
from typing import Literal, List, Dict, Optional, Any
import simpy

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("API_KEY"))
ai = AI(client, "gpt-4o-mini")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class MessageHistory(BaseModel):
    messages: List[Message]

@ai.text(stream=True)
def test_ai(chat: MessageHistory):
    """
    You are SimKitty, a specialized assistant for creating SimPy simulations.
    Output format must be JSON-compatible and match SimulationConfig schema.
    Focus on:
    - Resource allocation
    - Process flows
    - Entity interactions
    - Time-based events
    """
    return chat

@app.post("/ai")
def hello(chat: MessageHistory):
    sum = chat.model_dump()
    response = test_ai(sum['messages'])
    def generate_response(response):
        for chunk in response:
            yield chunk

    return StreamingResponse(
        generate_response(response),
        media_type="text/event-stream"
    )

class SimResource(BaseModel):
    name: str
    capacity: int
    cost_per_unit: float
    efficiency_threshold: float  # Define what's considered optimal utilization
    priority: Optional[int] = 1  # For resource prioritization
    shared: Optional[bool] = False  # Indicates if resource is shared among processes

class SimMetric(BaseModel):
    name: str
    target_value: float
    unit: str  # e.g., "minutes", "percentage", "count"
    description: str
    aggregation: Optional[str] = "average"  # Could be sum, max, min, etc.

class SimInsightRule(BaseModel):
    metric: str
    condition: str  # e.g., "above_threshold", "below_target"
    threshold: float
    recommendation: str

class SimProcess(BaseModel):
    name: str
    duration: int
    required_resources: List[str]
    expected_service_time: int
    max_acceptable_wait: int
    condition: Optional[str] = None  # Conditional execution based on entity attributes
    next_processes: List[str] = []  # Names of subsequent processes
    loop: Optional[bool] = False  # Indicates if the process loops
    release_resources: bool = True  # Release resources after process

class SimEntity(BaseModel):
    attributes: Dict[str, Any]  # Entity-specific data

class SimConfig(BaseModel):
    title: str
    description: str
    duration: int
    resources: List[SimResource]
    processes: List[SimProcess]
    entities_per_hour: int
    target_metrics: List[SimMetric]
    insight_rules: List[SimInsightRule]
    business_context: str  # Additional context for generating relevant insights
    entity_attributes: Dict[str, Any] = {}  # Default attributes for entities

    def get_metric_units(self) -> List[str]:
        return list(set(metric.unit for metric in self.target_metrics))

@ai.structured(response_format=SimConfig)
def generate_simulation(prompt: str) -> SimConfig:
    """You are SimKitty, an expert at creating SimPy simulation configurations.
    Generate practical and realistic simulation scenarios based on user prompts.
    Focus on:
    - Complex process flows with conditional logic and loops
    - Resource allocation and capacity planning with prioritization
    - Entity attributes and state changes
    - Inter-process communication and advanced timing controls

    Important rules:
    1. All process.required_resources must match existing resource names
    2. Resource names must be simple and consistent (e.g., "cashier", "ticket_booth")
    3. Each process must have at least one required resource
    4. All durations must be positive integers
    5. Resource capacities must be positive integers
    6. Processes can define conditional execution based on entity attributes
    7. Entities can have attributes that affect process flow
    """
    return prompt


def run_simulation(config: SimConfig):
    env = simpy.Environment()

    # Initialize metrics
    metrics = {}
    valid_units = config.get_metric_units()
    for metric in config.target_metrics:
        if metric.unit in valid_units:
            metrics[metric.name] = 0
        else:
            metrics[metric.name] = []

    resources = {}
    for res in config.resources:
        if res.priority:
            resources[res.name] = simpy.PriorityResource(env, capacity=res.capacity)
        else:
            resources[res.name] = simpy.Resource(env, capacity=res.capacity)

    # Map processes by name for easy access
    process_dict = {process.name: process for process in config.processes}

    def process_flow(env, entity, process_name):
        process_config = process_dict[process_name]
        start_time = env.now

        # Check if the process has a condition
        if process_config.condition:
            try:
                condition_met = eval(process_config.condition, {"entity": entity.attributes})
            except NameError as e:
                condition_met = False
                print(f"Condition evaluation error: {e}")
            if not condition_met:
                return  # Skip this process

        # Request resources
        reqs = []
        for resource_name in process_config.required_resources:
            resource = resources[resource_name]
            if isinstance(resource, simpy.PriorityResource):
                priority = 1  # Adjust priority as needed
                req = resource.request(priority=priority)
            else:
                req = resource.request()
            reqs.append(req)
            yield req

        # Process execution
        yield env.timeout(process_config.duration)

        # Update entity attributes if needed
        # Example: entity.attributes["processed"] = True

        # Track metrics
        for metric in config.target_metrics:
            if metric.unit in valid_units:
                metrics[metric.name] += 1
            else:
                elapsed_time = env.now - start_time
                metrics[metric.name].append(elapsed_time)

        # Release resources if specified
        if process_config.release_resources:
            for i, resource_name in enumerate(process_config.required_resources):
                resources[resource_name].release(reqs[i])

        # Proceed to next processes
        for next_process in process_config.next_processes:
            env.process(process_flow(env, entity, next_process))

        # Handle looping processes
        if process_config.loop:
            env.process(process_flow(env, entity, process_name))

    def entity_generator(env):
        entity_interval = 60 / (config.entities_per_hour / 60)  # Time between entities in minutes
        while True:
            yield env.timeout(entity_interval)
            entity_attributes = config.entity_attributes.copy()
            # Initialize entity attributes if needed
            entity_attributes["Age"] = 0  # Example attribute
            entity_attributes["Has laid eggs"] = False  # Example attribute
            entity = SimEntity(attributes=entity_attributes)
            # Start with processes that have no predecessors
            starting_processes = [p.name for p in config.processes if not any(p.name in proc.next_processes for proc in config.processes)]
            for process_name in starting_processes:
                env.process(process_flow(env, entity, process_name))

    env.process(entity_generator(env))
    env.run(until=config.duration)

    # Process results
    results = {
        "simulation_time": env.now,
        "metrics": {}
    }

    for metric in config.target_metrics:
        values = metrics[metric.name]
        if isinstance(values, list):
            if values:
                aggregation = metric.aggregation or "average"
                if aggregation == "sum":
                    aggregated_value = sum(values)
                elif aggregation == "max":
                    aggregated_value = max(values)
                elif aggregation == "min":
                    aggregated_value = min(values)
                else:  # Default to average
                    aggregated_value = sum(values) / len(values)
                results["metrics"][metric.name] = {
                    aggregation: aggregated_value,
                    "samples": len(values)
                }
            else:
                results["metrics"][metric.name] = {
                    metric.aggregation or "average": 0,
                    "samples": 0
                }
        else:
            results["metrics"][metric.name] = values

    return results
@app.post("/generate-sim")
def create_simulation(prompt: str):
    config = generate_simulation(prompt)
    results = run_simulation(config)
    return {"config": config, "results": results}

@app.post("/run-sim")
def run_sim(config: SimConfig):
    results = run_simulation(config)
    return results