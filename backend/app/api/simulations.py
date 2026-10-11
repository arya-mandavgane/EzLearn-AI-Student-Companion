"""
simulations.py — /api/simulations/catalog and /api/simulation/plan
Supports interactive visual simulations for ALL topics:
- Dedicated graphical visualizers for Stack and Queue.
- Dynamic AI-driven step-by-step interactive visual simulation for ANY other topic.
"""
import json
import logging
from typing import Optional, List
from fastapi import APIRouter

from app.ai.provider import generate
from app.schemas.simulation import (
    SimulationPlanRequest, SimulationPlanResponse,
    SimulationStep, SimulationItem, SimulationPrediction,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["simulations"])

SIMULATION_CATALOG = [
    {
        "id": "stack",
        "title": "Stack",
        "keywords": ["stack", "push", "pop", "lifo", "last in first out"],
        "description": "Last-In, First-Out data structure visualized as an interactive pile of plates.",
        "category": "Data Structures",
    },
    {
        "id": "queue",
        "title": "Queue",
        "keywords": ["queue", "enqueue", "dequeue", "fifo", "first in first out"],
        "description": "First-In, First-Out data structure visualized as an interactive line of people.",
        "category": "Data Structures",
    },
    {
        "id": "binary_search",
        "title": "Binary Search",
        "keywords": ["binary search", "divide and conquer", "sorted array search"],
        "description": "Efficient logarithmic search narrowing search range in half each step.",
        "category": "Algorithms",
    },
    {
        "id": "bubble_sort",
        "title": "Bubble Sort",
        "keywords": ["bubble sort", "sorting", "swapping"],
        "description": "Stepping through adjacent pairs and swapping out-of-order elements.",
        "category": "Algorithms",
    },
    {
        "id": "photosynthesis",
        "title": "Photosynthesis",
        "keywords": ["photosynthesis", "chlorophyll", "light reaction", "calvin cycle"],
        "description": "Biological energy conversion from sunlight, water, and CO2 into glucose and oxygen.",
        "category": "Science",
    },
]

SIMULATION_METADATA = {
    "stack": {
        "title": "Stack Simulation",
        "intro": "A stack is a linear data structure that follows the Last-In, First-Out (LIFO) principle. Elements can only be added or removed from the top, just like a pile of plates.",
    },
    "queue": {
        "title": "Queue Simulation",
        "intro": "A queue is a linear data structure that follows the First-In, First-Out (FIFO) principle. New elements enter at the rear and exit from the front, just like people waiting in a line.",
    },
}


def _parse_steps_json(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            cleaned = "\n".join(lines[1:-1]).strip()
        else:
            cleaned = "\n".join(lines[1:]).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(cleaned[start_idx : end_idx + 1])
        except Exception:
            pass
    return {}


@router.get("/simulations/catalog")
def simulations_catalog():
    """Return catalog of featured simulations."""
    return SIMULATION_CATALOG


@router.post("/simulation/plan", response_model=SimulationPlanResponse)
def plan_simulation(req: SimulationPlanRequest):
    """
    Match simulation topic request:
    1. Dedicated visualizers for 'stack' and 'queue'.
    2. Dynamic AI-generated step-by-step visual simulation for ALL OTHER topics.
    Never rejects topics — every topic gets an interactive simulation!
    """
    cleaned = req.request.strip().lower()
    words = set(cleaned.replace(",", " ").replace("-", " ").split())

    stack_kw = {"stack", "push", "pop", "lifo"}
    queue_kw = {"queue", "enqueue", "dequeue", "fifo"}

    has_stack = any(kw in words or kw in cleaned for kw in stack_kw)
    has_queue = any(kw in words or kw in cleaned for kw in queue_kw)

    if has_stack and not has_queue:
        meta = SIMULATION_METADATA["stack"]
        return SimulationPlanResponse(template="stack", title=meta["title"], intro=meta["intro"])

    if has_queue and not has_stack:
        meta = SIMULATION_METADATA["queue"]
        return SimulationPlanResponse(template="queue", title=meta["title"], intro=meta["intro"])

    # For ALL other topics: Generate dynamic interactive step-by-step simulation
    logger.info("Generating dynamic simulation for topic: %s", req.request)
    prompt = f"""You are an educational simulation designer. Design an interactive step-by-step visual simulation for the concept: '{req.request}'.
Respond with a single valid JSON object strictly matching this schema:
{{
  "template": "process",
  "title": "Short title of the simulation",
  "intro": "2 simple sentences explaining the core intuition.",
  "real_life_analogy": "A simple everyday real-life picture or analogy for beginners.",
  "steps": [
    {{
      "step_number": 1,
      "title": "Stage title",
      "description": "Clear explanation of what happens in this step.",
      "items": [
        {{"label": "item name or number", "status": "active", "info": "short status note"}},
        {{"label": "item 2", "status": "waiting", "info": ""}}
      ],
      "rule": "Code snippet, mathematical rule, or key takeaway for this step",
      "prediction": {{
        "question": "Predict what happens next:",
        "options": ["Choice A", "Choice B", "Choice C"],
        "correct_index": 0,
        "explanation": "Why this prediction is correct"
      }}
    }}
  ]
}}

Generate 4 to 6 logical steps showing how '{req.request}' works from beginning to end. Keep items visual, clear, and beginner-friendly."""

    raw_text = generate(prompt)
    data = _parse_steps_json(raw_text)

    if data and "steps" in data and isinstance(data["steps"], list) and len(data["steps"]) > 0:
        steps_list = []
        for s in data["steps"]:
            items = [SimulationItem(**it) for it in s.get("items", []) if isinstance(it, dict) and "label" in it]
            pred = None
            if isinstance(s.get("prediction"), dict) and "question" in s["prediction"]:
                pred_data = s["prediction"]
                pred = SimulationPrediction(
                    question=str(pred_data.get("question", "")),
                    options=list(pred_data.get("options", ["Option 1", "Option 2"])),
                    correct_index=int(pred_data.get("correct_index", 0)),
                    explanation=str(pred_data.get("explanation", "")),
                )
            steps_list.append(SimulationStep(
                step_number=int(s.get("step_number", len(steps_list) + 1)),
                title=str(s.get("title", f"Step {len(steps_list) + 1}")),
                description=str(s.get("description", "")),
                items=items,
                rule=s.get("rule"),
                prediction=pred,
            ))

        return SimulationPlanResponse(
            template="process",
            title=data.get("title", f"{req.request.title()} Simulation"),
            intro=data.get("intro", f"An interactive walkthrough of how {req.request} works step by step."),
            real_life_analogy=data.get("real_life_analogy"),
            steps=steps_list,
        )

    # Fallback default process steps if parsing or mock didn't return steps
    fallback_steps = [
        SimulationStep(
            step_number=1,
            title=f"Initialization of {req.request.title()}",
            description=f"Start by setting up the initial conditions and parameters for {req.request}.",
            items=[
                SimulationItem(label="Input Data / Initial State", status="active", info="Starting values"),
                SimulationItem(label="Processing Unit", status="waiting", info="Ready"),
                SimulationItem(label="Output Target", status="waiting", info="Pending"),
            ],
            rule="State: Initialized. Verify preconditions before starting execution.",
            prediction=SimulationPrediction(
                question="What happens immediately after initialization?",
                options=["Processing starts on the initial data", "Output is generated immediately", "System resets"],
                correct_index=0,
                explanation="Processing begins sequentially on the inputs.",
            ),
        ),
        SimulationStep(
            step_number=2,
            title="Core Transformation / Processing",
            description=f"The main mechanism of {req.request} is executed step by step.",
            items=[
                SimulationItem(label="Input Data", status="completed", info="Consumed"),
                SimulationItem(label="Active Stage", status="active", info="Transforming"),
                SimulationItem(label="Intermediate Buffer", status="highlighted", info="Current work"),
            ],
            rule="Execute: Transformation applied according to core principles.",
            prediction=SimulationPrediction(
                question="What is the result of this processing stage?",
                options=["Intermediate state is created", "System halts with error", "Inputs are discarded with no trace"],
                correct_index=0,
                explanation="The intermediate state moves the process toward the final goal.",
            ),
        ),
        SimulationStep(
            step_number=3,
            title="Final Verification & Output",
            description=f"The operation terminates and produces the final outcome for {req.request}.",
            items=[
                SimulationItem(label="Processed Result", status="target", info="Success"),
                SimulationItem(label="Verification Check", status="completed", info="Valid"),
            ],
            rule="Complete: Target state reached successfully.",
            prediction=SimulationPrediction(
                question="How do we confirm the simulation succeeded?",
                options=["Check the final output against expected criteria", "Assume it failed", "Restart without checking"],
                correct_index=0,
                explanation="Verifying the result against criteria confirms success.",
            ),
        ),
    ]

    return SimulationPlanResponse(
        template="process",
        title=f"{req.request.title()} Simulation",
        intro=f"An interactive visual model of {req.request}.",
        real_life_analogy=f"Think of {req.request} like an assembly line where each stage accomplishes a specific goal.",
        steps=fallback_steps,
    )
